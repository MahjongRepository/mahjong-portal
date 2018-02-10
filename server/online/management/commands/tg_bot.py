import datetime
import logging
import os
import sys
from threading import Thread

import telegram
from django.conf import settings
from django.core.management.base import BaseCommand
from telegram.error import Unauthorized, BadRequest, TimedOut, NetworkError, ChatMigrated, TelegramError
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

from online.handler import TournamentHandler
from online.models import TournamentGame
from tournament.models import Tournament

logger = logging.getLogger()
tournament_handler = None


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', type=int)
        parser.add_argument('lobby', type=str)
        parser.add_argument('game_type', type=str)

    def handle(self, *args, **options):
        set_up_logging()

        tournament_id = options.get('tournament_id')
        lobby = options.get('lobby')
        game_type = options.get('game_type')

        tournament = Tournament.objects.get(id=tournament_id)

        global tournament_handler
        tournament_handler = TournamentHandler(tournament, lobby, game_type)

        updater = Updater(token=settings.TELEGRAM_TOKEN)
        dispatcher = updater.dispatcher

        def stop_and_restart():
            """Gracefully stop the Updater and replace the current process with a new one"""
            updater.stop()
            os.execl(sys.executable, sys.executable, *sys.argv)

        def restart(bot, update):
            message = 'Bot is restarting...'
            logger.info(message)
            update.message.reply_text(message)
            Thread(target=stop_and_restart).start()

        start_handler = CommandHandler('me', set_tenhou_nickname, pass_args=True)
        log_handler = CommandHandler('log', set_game_log, pass_args=True)
        status_handler = CommandHandler('status', get_tournament_status)
        help_handler = CommandHandler('help', help_bot)

        # admin commands
        dispatcher.add_handler(CommandHandler('restart', restart,
                                              filters=Filters.user(username='@Nihisil')))
        dispatcher.add_handler(CommandHandler('prepare_next_round', prepare_next_round,
                                              filters=Filters.user(username='@Nihisil')))
        dispatcher.add_handler(CommandHandler('start_failed_games', start_failed_games,
                                              filters=Filters.user(username='@Nihisil')))
        dispatcher.add_handler(CommandHandler('start_games', start_games,
                                              filters=Filters.user(username='@Nihisil')))
        dispatcher.add_handler(CommandHandler('close_registration', close_registration,
                                              filters=Filters.user(username='@Nihisil')))

        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(log_handler)
        dispatcher.add_handler(status_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_error_handler(error_callback)
        dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_chat_member))

        logger.info('Starting the bot...')
        updater.start_polling()

        updater.idle()


def set_up_logging():
    logs_directory = os.path.join(settings.BASE_DIR, '..', 'logs')
    if not os.path.exists(logs_directory):
        os.mkdir(logs_directory)

    logger.setLevel(logging.NOTSET)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    file_name = '{}.log'.format(datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S'))
    fh = logging.FileHandler(os.path.join(logs_directory, file_name))
    fh.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def set_game_log(bot, update, args):
    logger.info('Set game log command. {}, {}'.format(update.message.from_user.username, args))

    if not len(args):
        update.message.reply_text(u'Укажите ссылку на ханчан после команды.')
        return

    # it can take some time to add log, so lets show typing notification
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)

    message = tournament_handler.add_game_log(args[0])
    update.message.reply_text(message)

    message = tournament_handler.check_round_was_finished()
    if message:
        bot.send_message(chat_id=update.message.chat_id, text=message)


def get_tournament_status(bot, update):
    logger.info('Get tournament status command')

    message = tournament_handler.get_tournament_status()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def help_bot(bot, update):
    logger.info('Help')

    message = '1. Ссылка на турнирное лобби:\n http://tenhou.net/0/?C44234907 \n'
    message += '2. Ссылка на статистику:\n https://gui.mjtop.net/eid73/stat \n'
    message += '3. Как получить ссылку на лог игры?\n http://telegra.ph/Kak-poluchit-ssylku-na-log-igry-02-10'
    bot.send_message(chat_id=update.message.chat_id, text=message, disable_web_page_preview=True)


def set_tenhou_nickname(bot, update, args):
    logger.info('Nickname command. {}, {}'.format(update.message.from_user.username, args))

    if not len(args):
        bot.send_message(chat_id=update.message.chat_id, text=u'Укажите ваш тенхо ник после команды.')
        return

    username = update.message.from_user.username
    if not username:
        update.message.reply_text(text=u'Перед привязкой тенхо ника нужно установить username в настройках телеграма.')
        return

    tenhou_nickname = args[0]
    message = tournament_handler.link_username_and_tenhou_nick(username, tenhou_nickname)
    update.message.reply_text(message)


def new_chat_member(bot, update):
    username = update.message.from_user.username
    logger.info('New member. {}'.format(username))

    message = 'Добро пожаловать в чат онлайн турнира! \n'
    if not username:
        message += u'Для начала установите username в настройках телеграма (Settings -> Username) \n'
        message += u'После этого отправьте команду "/me ваш ник на тенхе" для подтверждения участия.'
    else:
        message += u'Для подтверждения участия отправьте команду "/me ваш ник на тенхе"'

    bot.send_message(chat_id=update.message.chat_id, text=message)


def prepare_next_round(bot, update):
    logger.info('Prepare next round')

    games, message = tournament_handler.prepare_next_round()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def start_games(bot, update):
    logger.info('Start games')

    games = TournamentGame.objects.filter(status=TournamentGame.NEW)
    bot.send_message(chat_id=update.message.chat_id, text='Запускаю игры...')

    for game in games:
        message = tournament_handler.start_game(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)


def start_failed_games(bot, update):
    logger.info('Start failed games')

    games = TournamentGame.objects.filter(status=TournamentGame.FAILED_TO_START)
    bot.send_message(chat_id=update.message.chat_id, text='Запускаю игры...')

    for game in games:
        message = tournament_handler.start_game(game)
        bot.send_message(chat_id=update.message.chat_id, text=message)


def close_registration(bot, update):
    logger.info('Close registration')

    message = tournament_handler.close_registration()
    bot.send_message(chat_id=update.message.chat_id, text=message)


def error_callback(bot, update, error):
    logger.error(error)

    try:
        raise error
    except Unauthorized as e:
        # remove update.message.chat_id from conversation list
        pass
    except BadRequest as e:
        # handle malformed requests - read more below!
        pass
    except TimedOut as e:
        # handle slow connection problems
        pass
    except NetworkError as e:
        # handle other connection problems
        pass
    except ChatMigrated as e:
        # the chat_id of a group has changed, use e.new_chat_id instead
        pass
    except TelegramError as e:
        # handle all other telegram related errors
        pass
