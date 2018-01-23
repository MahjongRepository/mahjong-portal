# -*- coding: utf-8 -*-
from random import randint

from django.db import transaction
from django.db.models import Q

from online.models import TournamentPlayers, TournamentStatus, TournamentGame, TournamentGamePlayer

BOT_NICKNAMES = [
    u'あげる',
    u'くれる',
    u'寂しい'
]


class TournamentHandler(object):

    def __init__(self, tournament):
        self.tournament = tournament
        self.status, _ = TournamentStatus.objects.get_or_create(tournament=self.tournament)

    def get_tournament_status(self):
        if not self.status.current_round:
            confirmed_players = TournamentPlayers.objects.filter(tournament=self.tournament).count()
            return 'Идёт этап подтверждения участия. На данный момент {} подтвержденных игроков.'.format(confirmed_players)

        active_games_count = TournamentGame.objects.filter(tournament=self.tournament).exclude(status=TournamentGame.FINISHED).count()

        return 'Тур {}. Активных игр на данный момент: {}. Ждём пока они закончатся.'.format(self.status.current_round, active_games_count)

    def add_game_log(self, log):
        log = log.strip()
        if not log.strartwith('http://tenhou.net/'):
            return 'Отправленная ссылка не выглядит как ссыдка на лог игры.'

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
        if not self.status.current_round:
            self.status.current_round = 0

        if self.status.current_round >= self.tournament.number_of_sessions:
            return [], 'Невозможно запустить новые игры. У турнира закончились туры.'

        current_games = (TournamentGame.objects
                                       .filter(tournament=self.tournament)
                                       .filter(Q(status=TournamentGame.NEW) | Q(status=TournamentGame.FAILED_TO_START)))

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
        players = game.game_players.all().order_by('wind')
        message = 'Стол: {} запущен.'.format(u', '.join([x.player.tenhou_username for x in players]))
        return message

