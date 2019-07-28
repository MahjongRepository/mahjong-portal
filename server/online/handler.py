# -*- coding: utf-8 -*-
import logging
import random
from datetime import timedelta
from random import randint
from urllib.parse import unquote, urlparse, parse_qs

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from online.models import TournamentPlayers, TournamentStatus, TournamentGame, TournamentGamePlayer
from online.parser import TenhouParser
from online.team_seating import TeamSeating
from player.tenhou.management.commands.add_tenhou_account import get_started_date_for_account
from tournament.models import OnlineTournamentRegistration
from utils.general import make_random_letters_and_digit_string

logger = logging.getLogger()

# in minutes
TOURNAMENT_BREAKS_TIME = [
    5,
    5,
    30,
    5,
    5,
    5
]


class TournamentHandler(object):

    def __init__(self, tournament, lobby, game_type='0001'):
        self.tournament = tournament
        self.lobby = lobby
        self.game_type = game_type
        self.status, _ = TournamentStatus.objects.get_or_create(tournament=self.tournament)

    def get_tournament_status(self):
        if not self.status.current_round:
            confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament).count()
            if self.status.registration_closed:
                return 'Игры скоро начнутся. Подтвержденных игроков: {}.'.format(confirmed_players)
            else:
                return 'Идёт этап подтверждения участия. На данный момент {} подтвержденных игроков.'.format(confirmed_players)

        if self.status.end_break_time:
            now = timezone.now()

            if now > self.status.end_break_time:
                return 'Ждём начала нового тура.'

            minutes_dict = {
                1: 'минуту',
                2: 'минуты',
                3: 'минуты',
                4: 'минуты',
                21: 'минуту',
                22: 'минуты',
                23: 'минуты',
                24: 'минуты',
            }

            seconds_dict = {
                1: 'секунду',
                2: 'секунды',
                3: 'секунды',
                4: 'секунды',
                21: 'секунду',
                22: 'секунды',
                23: 'секунды',
                24: 'секунды',
                31: 'секунду',
                32: 'секунды',
                33: 'секунды',
                34: 'секунды',
                41: 'секунду',
                42: 'секунды',
                43: 'секунды',
                44: 'секунды',
                51: 'секунду',
                52: 'секунды',
                53: 'секунды',
                54: 'секунды',
            }

            delta = self.status.end_break_time - now
            if delta.seconds > 60:
                minutes = round(delta.seconds // 60 % 60, 2)
                seconds = delta.seconds - minutes * 60
                date = '{} {} и {} {}'.format(
                    minutes,
                    minutes_dict.get(minutes, 'минут'),
                    seconds,
                    seconds_dict.get(seconds, 'секунд'),
                )
            else:
                date = '{} {}'.format(
                    delta.seconds,
                    seconds_dict.get(delta.seconds, 'секунд'),
                )

            return 'Перерыв. Следующий тур начнётся через {}.'.format(date)

        active_games_count = (TournamentGame.objects
                              .filter(tournament=self.tournament)
                              .filter(tournament_round=self.status.current_round)
                              .exclude(status=TournamentGame.FINISHED)
                              .exclude(status=TournamentGame.FAILED_TO_START)
                              .count())

        failed_games_count = (TournamentGame.objects
                              .filter(tournament=self.tournament)
                              .filter(tournament_round=self.status.current_round)
                              .filter(status=TournamentGame.FAILED_TO_START)
                              .count())

        if active_games_count or failed_games_count:
            message = 'Тур {}. '.format(self.status.current_round)

            if active_games_count:
                message += 'Активных игр на данный момент: {}. Ждём пока они закончатся.'.format(active_games_count)

            if failed_games_count:
                message += 'Несколько игр не смогли запуститься. Администратор скоро это исправит.'

            return message

        if self.status.current_round == self.tournament.number_of_sessions:
            return 'Турнир завершён. Спасибо за участие!'

        return ''

    def close_registration(self):
        self.status.registration_closed = True
        self.status.save()
        return 'Этап подтверждения участия завершился. Игры начнутся через 10 минут.'

    def add_game_log(self, log_link):
        error_message = 'Это не похоже на лог игры.'

        log_link = log_link.replace('https://', 'http://')
        
        log_link = log_link.strip()
        if not log_link.startswith('http://tenhou.net/'):
            return error_message

        attributes = parse_qs(urlparse(log_link).query)
        
        if 'log' not in attributes:
            return error_message

        log_id = attributes['log'][0]

        try:
            parser = TenhouParser()
            players = parser.get_player_names(log_id)
        except Exception:
            return 'Не получилось. Возможно тенха не успела сохранить игру или вы скопировали не весь log id.'
        
        if TournamentGame.objects.filter(log_id=log_id).exists():
            return 'Игра уже была добавлена в систему. Спасибо.'
        
        games = (TournamentGame.objects
                               .filter(tournament=self.tournament)
                               .filter(game_players__player__tenhou_username__in=players)
                               .filter(tournament_round=self.status.current_round)
                               .distinct())
        if games.count() >= 2:
            logger.error('Log add. Too much games.')
            return 'Призошла ошибка при добавлении лога. Обратитесь к администратору.'
        
        game = games.first()
        
        data = {
            'jsonrpc': '2.0',
            'method': 'addOnlineReplay',
            'params': {
                'eventId': settings.PANTHEON_EVENT_ID,
                'link': log_link
            },
            'id': make_random_letters_and_digit_string()
        }
        
        response = requests.post(settings.PANTHEON_URL, json=data)
        if response.status_code == 500:
            logger.error('Log add. Pantheon 500.')
            return 'Призошла ошибка при добавлении лога. Обратитесь к администратору.'
        
        content = response.json()
        if content.get('error'):
            logger.error('Log add. Pantheon error. {}'.format(content.get('error')))
            return 'Призошла ошибка при добавлении лога. Обратитесь к администратору.'

        game.log_id = log_id
        game.status = TournamentGame.FINISHED
        game.save()

        return 'Игра была добавлена. Спасибо.'

    def link_username_and_tenhou_nick(self, telegram_username, tenhou_nickname):
        if self.status.registration_closed:
            return 'Этап подтверждения участия уже завершился. Зарегистрироваться нельзя.'

        if len(tenhou_nickname) > 8:
            return 'Ник на тенхе не должен быть больше 8 символов.'

        try:
            registration = OnlineTournamentRegistration.objects.get(
                tenhou_nickname=tenhou_nickname,
                tournament=self.tournament
            )
        except OnlineTournamentRegistration.DoesNotExist:
            return 'Вы не были зарегистрированы на турнир заранее. Обратитесь к администратору.'

        if TournamentPlayers.objects.filter(tenhou_username=tenhou_nickname, tournament=self.tournament).exists():
            return 'Ник "{}" уже был зарегистрирован на турнир.'.format(tenhou_nickname)

        account_started_date = get_started_date_for_account(tenhou_nickname)
        if not account_started_date:
            return 'Ником "{}" ещё не играли на тенхе. Вы уверены, что он правильно написан? Регистр важен! Обратитесь к администратору.'.format(
                tenhou_nickname
            )

        pantheon_id = registration.player and registration.player.pantheon_id or None
        team_name = registration.notes

        try:
            TournamentPlayers.objects.get(
                telegram_username=telegram_username,
                tournament=self.tournament,
            )
        except TournamentPlayers.DoesNotExist:
            TournamentPlayers.objects.create(
                telegram_username=telegram_username,
                tenhou_username=tenhou_nickname,
                tournament=self.tournament,
                pantheon_id=pantheon_id,
                team_name=team_name
            )

        message = 'Тенхо ник "{}" был ассоциирован с вами. Участие в турнире было подтверждено!'.format(tenhou_nickname)
        return message

    def prepare_next_round(self):
        if not self.status.current_round:
            self.status.current_round = 0

        if self.status.current_round >= self.tournament.number_of_sessions:
            return [], 'Невозможно запустить новые игры. У турнира закончились туры.'

        current_games = (TournamentGame.objects
                                       .filter(tournament=self.tournament)
                                       .exclude(status=TournamentGame.FINISHED))

        if current_games.exists():
            return [], 'Невозможно запустить новые игры. Старые игры ещё не завершились.'

        confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament)

        missed_id = confirmed_players.filter(pantheon_id=None)
        if missed_id.exists():
            return [], 'Невозможно запустить новые игры. Не у всех игроков стоит pantheon id.'

        with transaction.atomic():
            self.status.current_round += 1
            self.status.end_break_time = None

            pantheon_ids = {}
            for confirmed_player in confirmed_players:
                pantheon_ids[confirmed_player.pantheon_id] = confirmed_player

            sortition = self.make_sortition(list(pantheon_ids.keys()))

            games = []
            for item in sortition:
                # shuffle player winds
                random.shuffle(item)

                try:
                    game = TournamentGame.objects.create(
                        status=TournamentGame.NEW,
                        tournament=self.tournament,
                        tournament_round=self.status.current_round
                    )

                    for wind in range(0, len(item)):
                        player_id = pantheon_ids[item[wind]].id

                        TournamentGamePlayer.objects.create(game=game,
                                                            player_id=player_id,
                                                            wind=wind)
                    games.append(game)
                except Exception as e:
                    logger.error('Failed to prepare a game. Pantheon ids={}'.format(item), exc_info=1)

            # we was able to generate games
            if games:
                self.status.save()

                message = 'Тур {}. Игры сформированы.'.format(self.status.current_round)
            else:
                message = 'Игры не запустились. Требуется вмешательство администратора.'

        return games, message

    def make_sortition(self, pantheon_ids):
        if self.status.current_round == 1:
            return self._random_sortition(pantheon_ids)
        else:
            return self._pantheon_swiss_sortition()

    def start_game(self, game):
        """
        Send request to tenhou.net and start a new game in lobby
        """
        
        players = game.game_players.all().order_by('wind')
        
        player_names = [x.player.tenhou_username for x in players]

        url = 'http://tenhou.net/cs/edit/start.cgi'
        data = {
            'L': self.lobby,
            'R2': self.game_type,
            'RND': 'default',
            'WG': 1,
            'M': '\r\n'.join([x for x in player_names])
        }
        
        headers = {
            'Origin': 'http://tenhou.net',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://tenhou.net/cs/edit/?{}'.format(self.lobby),
        }
        
        try:
            response = requests.post(url, data=data, headers=headers, allow_redirects=False)
            location = unquote(response.headers['location'])
            result = location.split('{}&'.format(self.lobby))[1]

            if result.startswith('FAILED'):
                game.status = TournamentGame.FAILED_TO_START

                message = 'Стол: {} не получилось запустить.'.format(u', '.join(player_names))
                message += ' Стол был отодвинут в конец очереди.'
            elif result.startswith('MEMBER NOT FOUND'):
                game.status = TournamentGame.FAILED_TO_START

                message = 'Стол: {} не получилось запустить.'.format(u', '.join(player_names))
                missed_players = [x for x in result.split('\r\n')[1:] if x]

                tg_usernames = (TournamentPlayers.objects
                                .filter(tenhou_username__in=missed_players)
                                .filter(tournament=self.tournament)
                                .values_list('telegram_username', flat=True))
                tg_usernames = ['@' + x for x in tg_usernames]

                message += ' Отсутствующие игроки: {}'.format(', '.join(tg_usernames))
                message += ' Стол был отодвинут в конец очереди.'
            else:
                game.status = TournamentGame.STARTED

                message = 'Стол: {} запущен.'.format(u', '.join(player_names))
        except:
            message = 'Стол: {} не получилось запустить. Требуется вмешательство администратора.'.format(
                u', '.join(player_names)
            )
            game.status = TournamentGame.FAILED_TO_START
        
        game.save()
        
        return message

    def check_round_was_finished(self):
        finished_games = (TournamentGame.objects
                                        .filter(tournament=self.tournament)
                                        .filter(status=TournamentGame.FINISHED)
                                        .filter(tournament_round=self.status.current_round))
        games = (TournamentGame.objects
                               .filter(tournament=self.tournament)
                               .filter(tournament_round=self.status.current_round))

        if finished_games.count() == games.count() and not self.status.end_break_time:
            if self.status.current_round == self.tournament.number_of_sessions:
                return 'Все туры были завершены. Спасибо за участие!'
            else:
                index = self.status.current_round - 1
                break_minutes = TOURNAMENT_BREAKS_TIME[index]
                self.status.end_break_time = timezone.now() + timedelta(minutes=break_minutes)
                self.status.save()
                return 'Все игры успешно завершились. Следующий тур начнётся через {} минут.\n\n Игровое лобби: http://tenhou.net/3/?{}'.format(
                    break_minutes,
                    settings.TOURNAMENT_PUBLIC_LOBBY
                )
        else:
            return None

    def new_chat_member(self, username):
        if not self.status.current_round:
            message = 'Добро пожаловать в чат онлайн турнира! \n'
            if not username:
                message += u'Для начала установите username в настройках телеграма (Settings -> Username). Инструкция: http://telegramzy.ru/nik-v-telegramm/ \n'
                message += u'После этого отправьте команду "/me ваш ник на тенхе" для подтверждения участия.'
            else:
                message += u'Для подтверждения участия отправьте команду "/me ваш ник на тенхе"'
            return message
        else:
            message = 'Добро пожаловать в чат онлайн турнира! \n\n'
            message += 'Статистику турнира можно посмотреть вот тут: https://gui.mjtop.net/eid{}/stat \n'.format(settings.PANTHEON_EVENT_ID)
            return message

    def _pantheon_swiss_sortition(self):
        data = {
            'jsonrpc': '2.0',
            'method': 'generateSwissSeating',
            'params': {
                'eventId': settings.PANTHEON_EVENT_ID,
            },
            'id': make_random_letters_and_digit_string()
        }

        headers = {
            'X-Auth-Token': settings.PANTHEON_ADMIN_TOKEN,
        }

        response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
        if response.status_code == 500:
            logger.error('Make sortition. Pantheon 500.')
            return []

        content = response.json()
        if content.get('error'):
            logger.error('Make sortition. Pantheon error. {}'.format(content.get('error')))
            return []

        return content['result']

    def _random_sortition(self, pantheon_ids):
        # default random.shuffle function doesn't produce good results
        # so, let's use our own shuffle implementation
        for i in range(len(pantheon_ids)):
            swap = randint(0, len(pantheon_ids) - 1)
            temp = pantheon_ids[swap]
            pantheon_ids[swap] = pantheon_ids[i]
            pantheon_ids[i] = temp
        return list(self._split_to_chunks(pantheon_ids))

    def _split_to_chunks(self, items):
        n = 4
        for i in range(0, len(items), n):
            yield items[i:i + n]
