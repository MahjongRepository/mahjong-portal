# -*- coding: utf-8 -*-


class TournamentHandler(object):

    def __init__(self, tournament):
        self.tournament = tournament

    def get_tournament_status(self):
        return 'This is fine'

    def add_game_log(self, log):
        return 'Игра была добавлена. Спасибо.'

    def link_username_and_tenhou_nick(self, telegram_username, tenhou_nickname):
        message = 'Тенхо ник "{}" был ассоциирован с вами. Участие в турнире было подтверждено!'.format(tenhou_nickname)
        return message
