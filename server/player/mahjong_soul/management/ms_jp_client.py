import random

import aiohttp
from ms.base import MSRPCChannel
from ms.rpc import Lobby

MS_JP_HOST = "https://game.mahjongsoul.com"


class MSJapanLobbyClient:
    async def connect(self):
        version_to_force = ""
        async with aiohttp.ClientSession() as session:
            async with session.get("{}/version.json".format(MS_JP_HOST)) as res:
                version = await res.json()
                version = version["version"]
                version_to_force = version.replace(".w", "")

            async with session.get("{}/v{}/config.json".format(MS_JP_HOST, version)) as res:
                config = await res.json()
                url = config["ip"][0]["region_urls"][0]["url"]

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

        await channel.connect(MS_JP_HOST)
        print("Connection was established")

        return lobby, channel, version_to_force
