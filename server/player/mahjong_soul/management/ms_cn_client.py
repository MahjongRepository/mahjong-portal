# -*- coding: utf-8 -*-
from player.mahjong_soul.management.commands.ms_base import MSBaseCommand

MS_CN_HOST = "https://game.maj-soul.com"


class MSChinaLobbyClient(MSBaseCommand):
    async def do_connect(self):
        version_url_pattern = "{}/1/version.json"
        config_url_pattern = "{}/1/v{}/config.json"
        return await super().connect(version_url_pattern, config_url_pattern, MS_CN_HOST)
