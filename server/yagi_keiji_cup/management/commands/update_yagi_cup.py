# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from online.models import TournamentPlayers
from utils.new_pantheon import get_rating_table
from yagi_keiji_cup.models import YagiKeijiCupResults, YagiKeijiCupSettings


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):

    TEAM_MAPPING_TENHOU_PLAYER_KEY = "tenhou_player"
    TEAM_MAPPING_MAJSOUL_PLAYER_KEY = "majsoul_player"

    def handle(self, *args, **options):
        print("{0}: Start update Yagi Kaiji Cup results".format(get_date_string()))

        yagi_settings = None
        try:
            yagi_settings = YagiKeijiCupSettings.objects.get(is_main=True)
        except YagiKeijiCupSettings.DoesNotExist:
            yagi_settings = None

        if yagi_settings:
            tenhou_tournament_players = TournamentPlayers.objects.filter(
                tournament=yagi_settings.tenhou_tournament, is_disable=False
            )
            majsoul_tournament_players = TournamentPlayers.objects.filter(
                tournament=yagi_settings.majsoul_tournament, is_disable=False
            )

            team_mapping = {}
            player_team_mapping = {}
            for player in tenhou_tournament_players:
                if player.team_name and player.team_name not in team_mapping:
                    team_mapping[player.team_name] = {self.TEAM_MAPPING_TENHOU_PLAYER_KEY: player}
                    player_team_mapping[int(player.pantheon_id)] = player.team_name
            for player in majsoul_tournament_players:
                if player.team_name and player.team_name not in team_mapping:
                    team_mapping[player.team_name] = {self.TEAM_MAPPING_MAJSOUL_PLAYER_KEY: player}
                    player_team_mapping[int(player.pantheon_id)] = player.team_name
                else:
                    if player.team_name:
                        team_mapping[player.team_name][self.TEAM_MAPPING_MAJSOUL_PLAYER_KEY] = player
                        player_team_mapping[int(player.pantheon_id)] = player.team_name

            tenhou_pantheon_tournament_id = yagi_settings.tenhou_tournament.new_pantheon_id
            majsoul_pantheon_tournament_id = yagi_settings.majsoul_tournament.new_pantheon_id

            tenhou_results = get_rating_table(tenhou_pantheon_tournament_id).list
            # tenhou_results = sorted(tenhou_results, key=lambda x: x.rating, reverse=True)

            majsoul_results = get_rating_table(majsoul_pantheon_tournament_id).list

            teams_results = {}
            self.prepare_player_result(tenhou_results, player_team_mapping, team_mapping, teams_results)
            self.prepare_player_result(majsoul_results, player_team_mapping, team_mapping, teams_results)

        self.calculate_result(teams_results, team_mapping)
        print("{0}: Finish update Yagi Kaiji Cup results".format(get_date_string()))

    def prepare_player_result(self, tournament_results, player_team_mapping, team_mapping, teams_results):
        place = 1
        for result in tournament_results:
            if result.id in player_team_mapping:
                team_name = player_team_mapping[result.id]
                if team_name in team_mapping:
                    player = team_mapping[team_name][self.TEAM_MAPPING_TENHOU_PLAYER_KEY]
                    teams_results[team_name] = {
                        "tenhou_player": {"place": place, "player": player, "game_count": result.games_played}
                    }
            place += 1

    def calculate_result(self, teams_results, team_mapping):
        if len(teams_results) > 0:
            with transaction.atomic():
                # clear previous results
                YagiKeijiCupResults.objects.all().delete()
                for team, result in teams_results.items():
                    if (
                        self.TEAM_MAPPING_TENHOU_PLAYER_KEY in team_mapping[team]
                        and self.TEAM_MAPPING_MAJSOUL_PLAYER_KEY in team_mapping[team]
                    ):
                        tenhou_player = team_mapping[team][self.TEAM_MAPPING_TENHOU_PLAYER_KEY]
                        majsoul_player = team_mapping[team][self.TEAM_MAPPING_MAJSOUL_PLAYER_KEY]

                        tenhou_player_place = result["tenhou_player"]["place"]
                        tenhou_player_game_count = result["tenhou_player"]["game_count"]

                        majsoul_player_place = result["majsoul_player"]["place"]
                        majsoul_player_game_count = result["majsoul_player"]["game_count"]

                        team_scores = self.calculate_team_scors(4, tenhou_player_place, majsoul_player_place)

                        ykc_result = YagiKeijiCupResults.objects.create(
                            team_name=team,
                            tenhou_player_place=tenhou_player_place,
                            tenhou_player_game_count=tenhou_player_game_count,
                            tenhou_player=tenhou_player,
                            majsoul_player_place=majsoul_player_place,
                            majsoul_player_game_count=majsoul_player_game_count,
                            majsoul_player=majsoul_player,
                            team_scores=team_scores,
                        )
                        ykc_result.save()

    def calculate_team_scors(self, players_count, tenhou_player_place, majsoul_player_place):
        scores = (
            players_count
            - (tenhou_player_place + majsoul_player_place + 0.1 * min(tenhou_player_place, majsoul_player_place)) / 2
        ) * 10
        return scores
