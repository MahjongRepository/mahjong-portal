# -*- coding: utf-8 -*-

import argparse
import asyncio

from django.core.management import BaseCommand

from player.mahjong_soul.management.ms_cn_client import MSChinaLobbyClient
from player.mahjong_soul.management.ms_global_client import MSGlobalLobbyClient
from player.mahjong_soul.management.ms_jp_client import MSJapanLobbyClient


class MSServerBaseCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=int)
        parser.add_argument("server_type", type=str)
        parser.add_argument("access_token", type=str)
        parser.add_argument("--force", default=False, action=argparse.BooleanOptionalAction)

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
