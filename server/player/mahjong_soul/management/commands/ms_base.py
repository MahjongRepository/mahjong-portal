import asyncio
import hashlib
import hmac
import ujson as json
import os
import random
import uuid

import aiohttp
import ms.protocol_pb2 as pb
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from ms.base import MSRPCChannel
from ms.rpc import Lobby

MS_HOST = "https://game.maj-soul.com"


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

    async def connect(self):
        version_to_force = ""
        async with aiohttp.ClientSession() as session:
            async with session.get("{}/1/version.json".format(MS_HOST)) as res:
                version = await res.json()
                version = version["version"]
                version_to_force = version.replace(".w", "")

            async with session.get("{}/1/v{}/config.json".format(MS_HOST, version)) as res:
                config = await res.json()
                url = config["ip"][0]["region_urls"][1]["url"]

            async with session.get(url + "?service=ws-gateway&protocol=ws&ssl=true") as res:
                servers = await res.json()
                # maintenance mode
                if not servers.get("servers"):
                    return

                servers = servers["servers"]
                server = random.choice(servers)
                endpoint = "wss://{}/gateway".format(server)

        print("Chosen endpoint: {}".format(endpoint))
        channel = MSRPCChannel(endpoint)

        lobby = Lobby(channel)

        await channel.connect(MS_HOST)
        print("Connection was established")

        return lobby, channel, version_to_force

    async def login(self, lobby, username, password, version_to_force):
        print("Login with username and password")
        print(f"Version {version_to_force}")

        uuid_key = str(uuid.uuid1())

        req = pb.ReqLogin()
        req.account = username
        req.password = hmac.new(b"lailai", password.encode(), hashlib.sha256).hexdigest()
        req.device.is_browser = True
        req.random_key = uuid_key
        req.gen_access_token = True
        req.client_version_string = f"web-{version_to_force}"
        req.currency_platforms.append(2)

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

        request = pb.ReqOauth2Login()
        request.access_token = data["access_token"]
        request.device.is_browser = True
        request.random_key = data["random_key"]
        request.client_version_string = f"web-{version_to_force}"
        request.currency_platforms.append(2)

        response = await lobby.oauth2_login(request)
        if not response.access_token:
            print("Login Error:")
            print(response)
            return False

        print("Logged in")
        return True

    async def run_code(self, lobby, *args, **options):
        pass
