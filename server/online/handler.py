# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from random import randint
from urllib.parse import urlencode, quote, unquote, urlparse, parse_qs

import requests
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from online.models import TournamentPlayers, TournamentStatus, TournamentGame, TournamentGamePlayer
from online.parser import TenhouParser
from rating.utils import make_random_letters_and_digit_string

logger = logging.getLogger()

BOT_NICKNAMES = [
    u'おねえさん',
    u"<('o'<)",
    u'нани'
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
            return 'Идёт этап подтверждения участия. На данный момент {} подтвержденных игроков.'.format(confirmed_players)

        if self.status.end_break_time:
            delta = self.status.end_break_time - timezone.now()
            if delta.seconds > 60:
                minutes = round(delta.seconds // 60.0, 2)
            else:
                minutes = round(delta.seconds * 0.0166, 2)
            return 'Перерыв. Следующий тур {} начнётся через {} минут'.format(self.status.current_round + 1, minutes)

        active_games_count = (TournamentGame.objects
                              .filter(tournament=self.tournament)
                              .filter(tournament_round=self.status.current_round)
                              .exclude(status=TournamentGame.FINISHED)
                              .count())

        if active_games_count:
            return 'Тур {}. Активных игр на данный момент: {}. Ждём пока они закончатся.'.format(
                self.status.current_round,
                active_games_count
            )

    def add_game_log(self, log_link):
        error_message = 'Это не похоже на лог игры.'
        
        log_link = log_link.strip()
        if not log_link.startswith('http://tenhou.net/'):
            return error_message

        attributes = parse_qs(urlparse(log_link).query)
        
        if 'log' not in attributes:
            return error_message

        log_id = attributes['log'][0]

        parser = TenhouParser()
        players = parser.get_player_names(log_id)
        
        if TournamentGame.objects.filter(log_id=log_id).exists():
            return 'Игра уже была добавлена в систему другим игроком. Спасибо.'
        
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

    def link_username_and_tenhou_nick(self, telegram_username, tenhou_username):
        try:
            confirmation = TournamentPlayers.objects.get(telegram_username=telegram_username,
                                                         tournament=self.tournament)
            confirmation.tenhou_username = tenhou_username
            confirmation.save()
        except TournamentPlayers.DoesNotExist:
            TournamentPlayers.objects.create(telegram_username=telegram_username, tenhou_username=tenhou_username,
                                             tournament=self.tournament)

        message = 'Тенхо ник "{}" был ассоциирован с вами. Участие в турнире было подтверждено!'.format(tenhou_username)
        return message

    def start_next_round(self):
        """
        Increment round number, add bots (if needed) and make games
        """
        
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
        missed_players = confirmed_players.count() % 4
        if missed_players:
            missed_players = 4 - missed_players

        confirmed_players = list(confirmed_players)

        with transaction.atomic():
            # add bots to the tournament
            for x in range(0, missed_players):
                bot_replacement = TournamentPlayers.objects.create(telegram_username=BOT_NICKNAMES[x],
                                                                   tenhou_username=BOT_NICKNAMES[x],
                                                                   tournament=self.tournament)
                confirmed_players.append(bot_replacement)

            self.status.current_round += 1
            self.status.end_break_time = None
            self.status.save()

            player_ids = [x.id for x in confirmed_players]
            sortition = self.make_sortition(player_ids)

            games = []
            for item in sortition:
                game = TournamentGame.objects.create(
                    tournament=self.tournament,
                    tournament_round=self.status.current_round
                )

                for wind in range(0, len(item)):
                    TournamentGamePlayer.objects.create(game=game,
                                                        player_id=item[wind],
                                                        wind=wind)
                games.append(game)

        return games, 'Тур {}. Запускаю игры...'.format(self.status.current_round)

    def make_sortition(self, player_ids):
        """
        For now let's just use random sortition.
        This method prepared list of games with players.
        """
        number_of_players = len(player_ids)

        if number_of_players % 4 != 0:
            raise ValueError('Not correct number of players for sortition. It had to be multiples of 4')

        def shuffle_wall(rand_seeds):
            # for better shuffling we had to do it manually
            # shuffle() didn't make results to be really random
            for x in range(0, number_of_players):
                src = x
                dst = rand_seeds[x]

                swap = results[x]
                results[src] = results[dst]
                results[dst] = swap

        results = [i for i in range(0, number_of_players)]
        rand_one = [randint(0, number_of_players - 1) for _ in range(0, number_of_players)]
        rand_two = [randint(0, number_of_players - 1) for _ in range(0, number_of_players)]

        shuffle_wall(rand_one)
        shuffle_wall(rand_two)

        number_of_games = number_of_players // 4
        sortition = []
        for x in range(0, number_of_games):
            position = x * 4
            sortition.append([
                player_ids[position],
                player_ids[position + 1],
                player_ids[position + 2],
                player_ids[position + 3],
            ])

        return sortition

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
            
            tg_usernames = TournamentPlayers.objects.filter(tenhou_username__in=missed_players).values_list('telegram_username', flat=True)
            tg_usernames = ['@' + x for x in tg_usernames]
            
            message += ' Отсутствующие игроки: {}'.format(', '.join(tg_usernames))
            message += ' Стол был отодвинут в конец очереди.'
        else:
            game.status = TournamentGame.STARTED
            
            message = 'Стол: {} запущен.'.format(u', '.join(player_names))
        
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

        if finished_games.count() == games.count():
            break_minutes = 5
            self.status.end_break_time = timezone.now() + timedelta(minutes=break_minutes)
            self.status.save()
            return 'Все игры успешно завершились. Следующий тур начнётся через {} минут.'.format(break_minutes)
        else:
            return None
