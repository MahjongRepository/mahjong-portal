# -*- coding: utf-8 -*-
from player.mahjong_soul.management.commands.ms_base import MSBaseCommand

MS_JP_HOST = "https://game.mahjongsoul.com"


class MSJapanLobbyClient(MSBaseCommand):
    async def do_connect(self):
        version_url_pattern = "{}/version.json"
        config_url_pattern = "{}/v{}/config.json"
        return await super().connect(version_url_pattern, config_url_pattern, MS_JP_HOST)
