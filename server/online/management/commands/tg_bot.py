import datetime
import logging
import os
import sys
from threading import Thread
from time import sleep

import telegram
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

from online.handler import TournamentHandler
from online.models import TournamentGame
from tournament.models import Tournament

logger = logging.getLogger()
tournament_handler = TournamentHandler()


class Command(BaseCommand):
    def handle(self, *args, **options):
        set_up_logging()

        tournament_id = settings.TOURNAMENT_ID
        lobby = settings.TOURNAMENT_PRIVATE_LOBBY
        game_type = settings.TOURNAMENT_GAME_TYPE

        if not tournament_id or not lobby or not game_type:
            print("Tournament wasn't configured properly")
            return

        tournament = Tournament.objects.get(id=tournament_id)
        tournament_handler.init(tournament, lobby, game_type)

        updater = Updater(token=settings.TELEGRAM_TOKEN)
        dispatcher = updater.dispatcher

        def stop_and_restart():
            """Gracefully stop the Updater and replace the current process with a new one"""
            updater.stop()
            os.execl(sys.executable, sys.executable, *sys.argv)

        def restart(bot, update):
            message = "Bot is restarting..."
            logger.info(message)
            update.message.reply_text(message)
            Thread(target=stop_and_restart).start()

        start_handler = CommandHandler("me", set_tenhou_nickname, pass_args=True)
        log_handler = CommandHandler("log", set_game_log, pass_args=True)
        status_handler = CommandHandler("status", get_tournament_status)
        help_handler = CommandHandler("help", help_bot)

        # admin commands
        dispatcher.add_handler(
            CommandHandler("restart", restart, filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME))
        )
        dispatcher.add_handler(
            CommandHandler(
                "prepare_next_round",
                prepare_next_round,
                filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "start_failed_games",
                start_failed_games,
                filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "start_games", start_games, filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME)
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "close_registration",
                close_registration,
                filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME),
            )
        )
        dispatcher.add_handler(
            CommandHandler(
                "send_team_names_to_pantheon",
                send_team_names_to_pantheon,
                filters=Filters.user(username=TournamentHandler.TG_ADMIN_USERNAME),
            )
        )

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(log_handler)
        dispatcher.add_handler(status_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_error_handler(error_callback)
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_member))

        logger.info("Starting the bot...")
        updater.start_polling()

        updater.idle()


def set_up_logging():
    logs_directory = os.path.join(settings.BASE_DIR, "..", "logs")
    if not os.path.exists(logs_directory):
        os.mkdir(logs_directory)

    logger.setLevel(logging.NOTSET)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    file_name = "{}.log".format(datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S"))
    fh = logging.FileHandler(os.path.join(logs_directory, file_name))
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def set_game_log(bot, update, args):
    logger.info("Set game log command. {}, {}".format(update.message.from_user.username, args))

    if not len(args):
        update.message.reply_text("Укажите ссылку на ханчан после команды.")
        return

    # it can take some time to add log, so lets show typing notification
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

    message = tournament_handler.add_game_log(args[0])
    update.message.reply_text(message)

    message = tournament_handler.check_round_was_finished()
    if message:
        bot.send_message(chat_id=update.message.chat_id, text=message)


def get_tournament_status(bot, update):
    logger.info("Get tournament status command")

    message = tournament_handler.get_tournament_status()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def help_bot(bot, update):
    logger.info("Help")

    message = "1. Ссылка на турнирное лобби:\n http://tenhou.net/0/?{} \n".format(settings.TOURNAMENT_PUBLIC_LOBBY)
    message += "2. Ссылка на статистику:\n https://gui.mjtop.net/eid{}/stat \n".format(settings.PANTHEON_EVENT_ID)
    message += "3. Текущие игры в лобби:\n https://tenhou.net/wg/?{} \n".format(settings.TOURNAMENT_PUBLIC_LOBBY[:5])
    message += '4. Отправка лога игры через команду "/log http://tenhou.net..." \n'
    message += "5. Регламент турнира:\n https://mahjong.click/ru/online/ \n"
    message += "6. Как получить ссылку на лог игры для flash/windows клиентов?\n https://imgur.com/gallery/7Hv52md \n"
    message += "7. Как получить ссылку на лог игры для мобильного/нового клиента?\n https://imgur.com/gallery/rP72mPx\n"
    message += "8. Как открыть турнирное лобби с мобильного/нового приложения?\n https://imgur.com/gallery/vcjsODf \n"
    message += "9. Как открыть турнирное лобби с windows приложения?\n https://imgur.com/gallery/8vB307e"
    bot.send_message(chat_id=update.message.chat_id, text=message, disable_web_page_preview=True)


def set_tenhou_nickname(bot, update, args):
    logger.info("Nickname command. {}, {}".format(update.message.from_user.username, args))

    if not len(args):
        update.message.reply_text(text="Укажите ваш tenhou.net ник после команды.")
        return

    username = update.message.from_user.username
    if not username:
        text = (
            "Перед привязкой tenhou.net ника нужно установить username в настройках "
            "телеграма. Инструкция: http://telegramzy.ru/nik-v-telegramm/"
        )
        update.message.reply_text(text=text, disable_web_page_preview=True)
        return

    # it can take some time to validate nickname, so lets show typing notification
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

    tenhou_nickname = args[0]
    message = tournament_handler.link_username_and_tenhou_nick(username, tenhou_nickname)
    update.message.reply_text(message)


def new_chat_member(bot, update):
    username = update.message.from_user.username
    logger.info("New member. {}".format(username))

    message = tournament_handler.new_chat_member(username)
    bot.send_message(chat_id=update.message.chat_id, text=message, disable_web_page_preview=True)


def prepare_next_round(bot, update):
    logger.info("Prepare next round")

    games, message = tournament_handler.prepare_next_round()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def start_games(bot, update):
    logger.info("Start games")

    games = TournamentGame.objects.filter(status=TournamentGame.NEW)
    bot.send_message(chat_id=update.message.chat_id, text="Запускаю игры...")
    bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "После завершения вашей игры отправьте ссылку на лог игры в этот чат. "
            "Одну ссылку можно отправлять много раз, так что не бойтесь - ничего сломается.\n\n"
            "Это поможет сократить время турнира и разгрузит админов. "
            "Пока ВСЕ ссылки на игры не будут добавлены, следующий тур запустить не получится.\n\n"
            "Как получить ссылку на лог игры для flash/windows клиентов?\nhttps://imgur.com/gallery/7Hv52md \n\n"
            "Как получить ссылку на лог игры для мобильного/нового клиента?\nhttps://imgur.com/gallery/rP72mPx \n\n"
        ),
        disable_web_page_preview=True,
    )

    for game in games:
        message = tournament_handler.start_game(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)
        sleep(2)


def start_failed_games(bot, update):
    logger.info("Start failed games")

    games = TournamentGame.objects.filter(Q(status=TournamentGame.FAILED_TO_START) | Q(status=TournamentGame.NEW))
    bot.send_message(chat_id=update.message.chat_id, text="Запускаю игры...")

    for game in games:
        message = tournament_handler.start_game(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)


def close_registration(bot, update):
    logger.info("Close registration")

    message = tournament_handler.close_registration()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def send_team_names_to_pantheon(bot, update):
    logger.info("Send team names to pantheon")

    message = tournament_handler.send_team_names_to_pantheon()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def error_callback(bot, update, error):
    logger.error(error)

    try:
        raise error
    except Unauthorized:
        # remove update.message.chat_id from conversation list
        pass
    except BadRequest:
        # handle malformed requests - read more below!
        pass
    except TimedOut:
        # handle slow connection problems
        pass
    except NetworkError:
        # handle other connection problems
        pass
    except ChatMigrated:
        # the chat_id of a group has changed, use e.new_chat_id instead
        pass
    except TelegramError:
        # handle all other telegram related errors
        pass
