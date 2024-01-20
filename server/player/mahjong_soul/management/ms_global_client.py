import random

import aiohttp
from ms.base import MSRPCChannel
from ms.rpc import Lobby

MS_EN_HOST = "https://mahjongsoul.game.yo-star.com"


class MSGlobalLobbyClient:

    async def connect(self):
        version_to_force = ""
        async with aiohttp.ClientSession() as session:
            async with session.get("{}/version.json".format(MS_EN_HOST)) as res:
                version = await res.json()
                version = version["version"]
                version_to_force = version.replace(".w", "")

            async with session.get("{}/v{}/config.json".format(MS_EN_HOST, version)) as res:
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

        await channel.connect(MS_EN_HOST)
        print("Connection was established")

        return lobby, channel, version_to_force
