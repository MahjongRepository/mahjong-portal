# -*- coding: utf-8 -*-
import asyncio
import hashlib
import hmac
import uuid

import ms.protocol_pb2 as pb
from django.conf import settings
from django.core.management import BaseCommand

from player.mahjong_soul.management.ms_cn_client import MSChinaLobbyClient
from player.mahjong_soul.management.ms_global_client import MSGlobalLobbyClient
from player.mahjong_soul.management.ms_jp_client import MSJapanLobbyClient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("friend_id", type=str)
        parser.add_argument("server_type", type=str)
        parser.add_argument("access_token", type=str)

    def handle(self, *args, **options):
        asyncio.run(self.run(*args, **options))

    async def run(self, *args, **options):
        server_type = options.get("server_type")

        lobby, channel, version_to_force = await self.connect(server_type.lower())
        await self.run_code(lobby, channel, version_to_force, *args, **options)
        await channel.close()

    async def connect(self, server_type):
        if server_type == "en":
            client = MSGlobalLobbyClient()
            return await client.do_connect()
        if server_type == "jp":
            client = MSJapanLobbyClient()
            return await client.do_connect()
        if server_type == "cn":
            client = MSChinaLobbyClient()
            return await client.do_connect()
        raise Exception("Incorrect server type, should be [en, jp, cn]")

    async def search(self, lobby, ms_friend_id):
        req = pb.ReqSearchAccountByPattern()
        req.search_next = False
        req.pattern = str(ms_friend_id)

        res = await lobby.search_account_by_pattern(req)

        if res.error.code:
            print("SearchAccount Error:")
            print(res)

        print("found account_id: " + str(res.decode_id))

    async def run_code(self, lobby, channel, version_to_force, *args, **options):
        server_type = options.get("server_type")
        access_token = options.get("access_token")
        friend_id = options.get("friend_id")

        if server_type.lower() == "cn":
            result = await self.cn_login(lobby, settings.MS_USERNAME, settings.MS_PASSWORD, version_to_force)
        else:
            result = await self.login(lobby, access_token, version_to_force)
        if not result:
            print("Exit")
            await channel.close()
            return

        await self.search(lobby, friend_id)

    async def cn_login(self, lobby, username, password, version_to_force):
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

        return True

    async def login(self, lobby, acess_token, version_to_force):
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
