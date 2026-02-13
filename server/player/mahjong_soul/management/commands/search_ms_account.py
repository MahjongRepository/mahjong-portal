# -*- coding: utf-8 -*-
import ms.protocol_pb2 as pb
from django.conf import settings

from player.mahjong_soul.management.commands.ms_servers_base import MSServerBaseCommand


class Command(MSServerBaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("friend_id", type=str)
        parser.add_argument("server_type", type=str)
        parser.add_argument("access_token", type=str)

    async def search(self, lobby, ms_friend_id):
        req = pb.ReqSearchAccountByPattern()
        req.search_next = False
        req.pattern = str(ms_friend_id)

        res = await lobby.search_account_by_pattern(req)

        if res.error.code:
            print("SearchAccount Error:")
            print(res)

        found_account_id = res.decode_id
        req = pb.ReqMultiAccountId()
        req.account_id_list.extend([found_account_id])
        res = await lobby.fetch_multi_account_brief(req)

        if res.error.code:
            print("SearchAccount Error:")
            print(res)

        found_nickname = None
        for player in res.players:
            if player.account_id == found_account_id:
                found_nickname = player.nickname

        print(f"found account_id: [{str(found_account_id)}], found nickname: [{found_nickname}]")

    async def run_code_with_channel(self, lobby, channel, version_to_force, *args, **options):
        server_type = options.get("server_type")
        access_token = options.get("access_token")
        friend_id = options.get("friend_id")

        if server_type.lower() == "cn":
            result = await self.login(lobby, settings.MS_USERNAME, settings.MS_PASSWORD, version_to_force)
        else:
            result = await self.login_with_token(lobby, access_token, version_to_force)
        if not result:
            print("Exit")
            await channel.close()
            return

        await self.search(lobby, friend_id)
