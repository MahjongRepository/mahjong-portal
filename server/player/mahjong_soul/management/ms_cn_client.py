# -*- coding: utf-8 -*-

import random

import aiohttp
from ms.base import MSRPCChannel
from ms.rpc import Lobby

MS_CN_HOST = "https://game.maj-soul.com"


class MSChinaLobbyClient:
    async def connect(self):
        version_to_force = ""
        async with aiohttp.ClientSession() as session:
            async with session.get("{}/1/version.json".format(MS_CN_HOST)) as res:
                version = await res.json()
                version = version["version"]
                version_to_force = version.replace(".w", "")

            async with session.get("{}/1/v{}/config.json".format(MS_CN_HOST, version)) as res:
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

        await channel.connect(MS_CN_HOST)
        print("Connection was established")

        return lobby, channel, version_to_force
