# -*- coding: utf-8 -*-

import asyncio
import hashlib
import hmac
import os
import random
import uuid
from datetime import datetime
from datetime import timezone as stdtimezone

import aiohttp
import ms.protocol_pb2 as pb
import ujson as json
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from ms.base import MSRPCChannel
from ms.rpc import Lobby, Route


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class MSBaseCommand(BaseCommand):
    TOKEN_PATH = os.path.join(settings.BASE_DIR, ".ms")

    def handle(self, *args, **options):
        asyncio.run(self.run(settings.MS_USERNAME, settings.MS_PASSWORD, *args, **options))

    async def run(self, username, password, *args, **options):
        lobby, channel, version_to_force = await self.connect()

        result = await self.re_login(lobby, version_to_force)
        if not result:
            result = await self.login(lobby, username, password, version_to_force)

        if not result:
            print("Exit")
            await channel.close()
            return

        await self.run_code(lobby, *args, **options)
        await channel.close()

    async def connect(
        self,
        version_url_pattern="{}/1/version.json",
        config_url_pattern="{}/1/v{}/config.json",
        host="https://game.maj-soul.com",
    ):
        version_to_force = ""
        async with aiohttp.ClientSession() as session:
            async with session.get(version_url_pattern.format(host)) as res:
                version = await res.json()
                version = version["version"]
                version_to_force = version.replace(".w", "")

            async with session.get(config_url_pattern.format(host, version)) as res:
                config = await res.json()
                url = config["ip"][0]["gateways"][1]["url"]

            async with session.get("{}/api/clientgate/routes?platform=Web&version={}".format(url, version)) as res:
                routes = await res.json()
                # maintenance mode
                if not routes.get("data"):
                    return

                if "routes" in routes["data"]:
                    routes = routes["data"]["routes"]
                    server = random.choice(routes)
                    endpoint = "wss://{}/gateway".format(server["domain"])
                    route_id = str(server["id"]).strip()

        print("Chosen endpoint: {}".format(endpoint))
        channel = MSRPCChannel(endpoint)

        lobby = Lobby(channel)
        route = Route(channel)

        await self.route_connect(channel, route, route_id, host)
        return lobby, channel, version_to_force

    async def route_connect(self, channel, route, route_id, host):
        await channel.connect(host)
        print("Connection was established")

        utc_now = int(datetime.now(stdtimezone.utc).timestamp() * 1000)
        req_connection = pb.ReqRequestConnection()
        req_connection.type = 3
        req_connection.route_id = route_id
        req_connection.timestamp = utc_now
        req_connection.platform = "Web"
        req_connection_result = await route.request_connection(req_connection)
        if int(req_connection_result.error.ByteSize()) > 0:
            await channel.close()
            raise RuntimeError("request connection for route {} failed".format(route_id))

    async def login_with_token(self, lobby, acess_token, version_to_force):
        print("Login with access_token")
        print(f"Version {version_to_force}")

        req = pb.ReqOauth2Check()
        req.type = 7
        req.access_token = acess_token
        res = await lobby.oauth2_check(req)

        if not res.has_account:
            print("Oauth2Check Error:")
            print(res)
            return False

        req = pb.ReqOauth2Login()
        req.client_version_string = f"web-{version_to_force}"
        req.client_version.resource = version_to_force
        req.type = 7
        req.access_token = acess_token
        req.device.hardware = "pc"
        req.device.is_browser = True
        req.device.os = "window"
        req.device.os_version = "win10"
        req.device.platform = "pc"
        req.device.sale_platform = "web"
        req.device.software = "Chrome"
        req.device.screen_height = 474
        req.device.screen_width = 1920
        req.random_key = str(uuid.uuid1())
        req.reconnect = False
        req.tag = "en"

        res = await lobby.oauth2_login(req)
        token = res.access_token
        if not token:
            print("Oauth2Login Error:")
            print(res)
            return False

        return True

    async def login(self, lobby, username, password, version_to_force):
        print(f"Login with username[{username}] and password[{password}]")
        print(f"Version {version_to_force}")

        uuid_key = str(uuid.uuid1())

        resource_version = "0.16.290"
        package_version = "4.0.51"

        req = pb.ReqLogin()
        req.account = username
        req.password = hmac.new(b"lailai", password.encode(), hashlib.sha256).hexdigest()
        req.reconnect = False
        req.device.platform = "pc"
        req.device.hardware = "pc"
        req.device.os = "windows"
        req.device.os_version = "win10"
        req.device.is_browser = True
        req.device.software = "Chrome"
        req.device.sale_platform = "web"
        req.device.screen_width = 2133
        req.device.screen_height = 1103
        req.device.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        )
        req.device.screen_type = 1
        req.random_key = uuid_key
        req.gen_access_token = True
        # todo: search path to resolve version
        req.client_version_string = f"WebGL_2022-{resource_version}"
        req.currency_platforms.append(1)
        req.currency_platforms.append(2)
        req.currency_platforms.append(5)
        req.currency_platforms.append(6)
        req.currency_platforms.append(8)
        req.currency_platforms.append(10)
        req.currency_platforms.append(11)
        req.tag = "cn"
        req.client_version.resource = resource_version
        req.client_version.package = package_version

        res = await lobby.login(req)
        token = res.access_token
        if not token:
            print("Login Error:")
            print(res)
            return False

        with open(self.TOKEN_PATH, "w") as f:
            print("Saving access token...")
            json.dump({"random_key": uuid_key, "access_token": token}, f)

        return True

    async def re_login(self, lobby, version_to_force):
        print(f"Version {version_to_force}")

        if not os.path.exists(self.TOKEN_PATH):
            print("Access token is not present")
            return False

        with open(self.TOKEN_PATH) as f:
            print("Reading access token...")
            data = json.load(f)

        print("Checking access token...")
        request = pb.ReqOauth2Check()
        request.access_token = data["access_token"]
        response = await lobby.oauth2_check(request)
        if not response.has_account:
            print("Invalid access token")
            return False

        resource_version = "0.16.290"
        package_version = "4.0.51"

        request = pb.ReqOauth2Login()
        request.access_token = data["access_token"]
        request.reconnect = False
        request.device.platform = "pc"
        request.device.hardware = "pc"
        request.device.os = "windows"
        request.device.os_version = "win10"
        request.device.is_browser = True
        request.device.software = "Chrome"
        request.device.sale_platform = "web"
        request.device.screen_width = 2133
        request.device.screen_height = 1103
        request.device.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/150.0.0.0 Safari/537.36"
        )
        request.device.screen_type = 1
        request.random_key = data["random_key"]
        # todo: search path to resolve version
        request.client_version_string = f"WebGL_2022-{resource_version}"
        request.currency_platforms.append(1)
        request.currency_platforms.append(2)
        request.currency_platforms.append(5)
        request.currency_platforms.append(6)
        request.currency_platforms.append(8)
        request.currency_platforms.append(10)
        request.currency_platforms.append(11)
        request.tag = "cn"
        request.client_version.resource = resource_version
        request.client_version.package = package_version

        response = await lobby.oauth2_login(request)
        if not response.access_token:
            print("Login Error:")
            print(response)
            return False

        print("Logged in")
        return True

    async def run_code(self, lobby, *args, **options):
        pass

    async def run_code_with_channel(self, lobby, channel, version_to_force, *args, **options):
        pass
