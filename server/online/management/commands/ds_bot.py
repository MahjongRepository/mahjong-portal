import asyncio
import logging

import discord
from discord import Message
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate
from django.utils.translation import gettext as _

from online.handler import TournamentHandler
from online.models import TournamentNotification
from tournament.models import Tournament
from utils.logs import set_up_logging

logger = logging.getLogger("tournament_bot")


class Command(BaseCommand):
    def handle(self, *args, **options):
        set_up_logging(TournamentHandler.DISCORD_DESTINATION)

        required_configs = [
            settings.TOURNAMENT_ID,
            settings.TOURNAMENT_PUBLIC_LOBBY,
            settings.TOURNAMENT_PRIVATE_LOBBY,
            settings.TOURNAMENT_GAME_TYPE,
            settings.DISCORD_TOKEN,
            settings.DISCORD_GUILD_NAME,
            settings.DISCORD_ADMIN_ID,
        ]

        for config_item in required_configs:
            if not config_item:
                logger.error("One of the required tournament config wasn't configured.")
                return

        ds_client = DiscordClient()
        ds_client.run(settings.DISCORD_TOKEN)


class DiscordClient(discord.Client):
    CONFIRMATION_EN = "confirmation_en"
    CONFIRMATION_RU = "confirmation_ru"
    NOTIFICATIONS_EN = "notifications_en"
    NOTIFICATIONS_RU = "notifications_ru"
    GENERAL_EN = "general_en"
    GENERAL_RU = "general_ru"
    GAME_LOGS = "game_logs"

    REQUIRED_CHANNELS = [
        CONFIRMATION_EN,
        CONFIRMATION_RU,
        NOTIFICATIONS_EN,
        NOTIFICATIONS_RU,
        GAME_LOGS,
        GENERAL_EN,
        GENERAL_RU,
    ]

    guild = None
    channels_dict = None

    def __init__(self):
        super(DiscordClient, self).__init__()

        self.channels_dict = {}
        self.bg_task = self.loop.create_task(self.send_notifications())

        tournament = Tournament.objects.get(id=settings.TOURNAMENT_ID)
        self.tournament_handler = TournamentHandler()
        self.tournament_handler.init(
            tournament,
            settings.TOURNAMENT_PRIVATE_LOBBY,
            settings.TOURNAMENT_GAME_TYPE,
            TournamentHandler.DISCORD_DESTINATION,
        )

    async def on_ready(self):
        self.guild = discord.utils.get(self.guilds, name=settings.DISCORD_GUILD_NAME)

        for channel in self.guild.channels:
            self.channels_dict[channel.name] = channel.id

        logger.info(f'"{self.user}" has connected to {self.guild.name} (id: {self.guild.id}) guild')
        logger.info(f"found {len(self.guild.channels)} channels")

        for required_channel in self.REQUIRED_CHANNELS:
            if required_channel not in self.channels_dict:
                raise AssertionError(f"Guild doesn't have required #{required_channel} channel")

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        channel_name = message.channel.name

        if channel_name == DiscordClient.CONFIRMATION_EN or channel_name == DiscordClient.CONFIRMATION_RU:
            await self.confirm_participation(message)
            return

        if channel_name == DiscordClient.GAME_LOGS:
            await self.add_game_log(message)
            return

        if message.content == "!status":
            await self.get_status(message)
            return

        if message.content == "!help":
            await self.get_help(message)
            return

    async def get_help(self, message: Message):
        self.activate_language(message.channel.name)

        m = ""
        m += _("1. Tournament lobby:\n <%(lobby_link)s> \n") % {"lobby_link": self.tournament_handler.get_lobby_link()}
        m += _("2. Tournament statistics:\n <%(rating_link)s> \n") % {
            "rating_link": self.tournament_handler.get_rating_link()
        }
        m += _("2.1. Team statistics:\n <%(rating_link)s>/team \n") % {
            "rating_link": self.tournament_handler.get_rating_link()
        }
        m += _("3. Current games:\n <%(current_games_link)s> \n") % {
            "current_games_link": f"https://tenhou.net/wg/?{settings.TOURNAMENT_PUBLIC_LOBBY[:5]}"
        }

        await message.channel.send(m)

    async def add_game_log(self, message: Message):
        _, success = self.tournament_handler.add_game_log(message.content)
        emoji = success and "\N{THUMBS UP SIGN}" or "\N{NO ENTRY SIGN}"
        await message.add_reaction(emoji)

    async def get_status(self, message: Message):
        self.activate_language(message.channel.name)

        response = self.tournament_handler.get_tournament_status()
        await message.channel.send(response)

    async def confirm_participation(self, message: Message):
        self.activate_language(message.channel.name)

        tenhou_nickname = message.content
        ds_nickname = message.author.name

        response = self.tournament_handler.confirm_participation_in_tournament(
            tenhou_nickname, discord_username=ds_nickname
        )
        await self.replay(message.channel, message.author, response)

    async def send_notifications(self):
        await self.wait_until_ready()

        if not self.channels_dict:
            print("no dicts")
            await asyncio.sleep(5)

        while not self.is_closed():
            notification = TournamentNotification.objects.filter(
                is_processed=False, destination=TournamentNotification.DISCORD
            ).last()

            if not notification:
                await asyncio.sleep(2)
                continue

            extra_kwargs = {"confirmation_channel": self.channel_mention(DiscordClient.CONFIRMATION_EN)}
            message = self.tournament_handler.get_notification_text("en", notification, extra_kwargs)
            channel = self.get_channel(self.channels_dict[DiscordClient.NOTIFICATIONS_EN])
            await channel.send(message)

            extra_kwargs = {"confirmation_channel": self.channel_mention(DiscordClient.CONFIRMATION_RU)}
            message = self.tournament_handler.get_notification_text("ru", notification, extra_kwargs)
            channel = self.get_channel(self.channels_dict[DiscordClient.NOTIFICATIONS_RU])
            await channel.send(message)

            notification.is_processed = True
            notification.save()

            logger.info(f"notification id={notification.id} sent")

            await asyncio.sleep(2)

    async def replay(self, channel, user, message):
        m = f"{user.mention}\n{message}"
        await channel.send(m)

    def channel_mention(self, channel_name):
        return f"<#{self.channels_dict[channel_name]}>"

    def activate_language(self, channel_name: str):
        lang = "en"
        if channel_name.endswith("_ru"):
            lang = "ru"
        activate(lang)
        return lang
