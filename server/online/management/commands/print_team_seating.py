import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import activate

from online.models import TournamentPlayers
from online.team_seating import TeamSeating
from player.models import Player
from player.tenhou.models import TenhouAggregatedStatistics, TenhouNickname
from tournament.models import OnlineTournamentRegistration


class Command(BaseCommand):
    help = "Run only locally, it modifies players data"

    def handle(self, *args, **options):
        activate("ru")

        tenhou_nicknames = {}
        players = TournamentPlayers.objects.filter(tournament_id=settings.TOURNAMENT_ID)
        # player = Player.objects.all().first()

        for tournament_player in players:
            try:
                tenhou_obj = TenhouNickname.objects.get(tenhou_username=tournament_player.tenhou_username)
                stat_obj = tenhou_obj.aggregated_statistics.filter(
                    game_players=TenhouAggregatedStatistics.FOUR_PLAYERS
                ).first()
                tenhou_nicknames[tournament_player.tenhou_username] = stat_obj.rank
            except TenhouNickname.DoesNotExist:
                pass
                # player_games, account_start_date, four_players_rate =
                # download_all_games_from_nodochi(tournament_player.tenhou_username)
                #
                # is_main = False
                # tenhou_object = TenhouNickname.objects.create(
                #     is_main=is_main, player=player, tenhou_username=tournament_player.tenhou_username,
                #     username_created_at=account_start_date
                # )
                #
                # save_played_games(tenhou_object, player_games)
                # stat_obj = recalculate_tenhou_statistics_for_four_players(tenhou_object, player_games, four_players_rate)
                #
                # sleep(2)

        for nickname in tenhou_nicknames.keys():
            dan = 0
            stat_rank = tenhou_nicknames[nickname]
            if stat_rank >= 10:
                dan = stat_rank - 9
            else:
                if stat_rank == 0:
                    stat_rank = 1

                dan = stat_rank / 10

            tenhou_nicknames[nickname] = dan

        with open(TeamSeating.processed_seating) as f:
            data = json.loads(f.read())

        for round_index in range(7):
            print(f"Раунд/Hanchan {round_index + 1}")
            print("")

            seating = data["seating"][round_index]

            for table_index, table in enumerate(seating):
                print(f"Стол/Table {table_index + 1}")

                player_names = []
                # replace team numbers with pantheon ids
                dans = 0
                for x in range(0, 4):
                    pantheon_id = data["team_players_map"][str(table[x])]
                    tournament_player = TournamentPlayers.objects.get(
                        tournament_id=settings.TOURNAMENT_ID, pantheon_id=pantheon_id
                    )
                    last_name, first_name = self.get_player_name(tournament_player)
                    player_names.append(f"{last_name} {first_name}")

                    dans += tenhou_nicknames[tournament_player.tenhou_username]

                print(f"{','.join(player_names)},{(dans/4):.2f}")

            print("")

    def get_player_name(self, tournament_player):
        if tournament_player.pantheon_id:
            try:
                player = Player.objects.get(pantheon_id=tournament_player.pantheon_id)
                return player.last_name, player.first_name
            except Player.DoesNotExist:
                pass

        try:
            registration = OnlineTournamentRegistration.objects.filter(
                tenhou_nickname=tournament_player.tenhou_username
            ).last()
            if registration and registration.player:
                return registration.player.last_name, registration.player.first_name
        except (OnlineTournamentRegistration.DoesNotExist, Player.DoesNotExist):
            pass

        result = OnlineTournamentRegistration.objects.filter(tenhou_nickname=tournament_player.tenhou_username).last()
        if result:
            return result.last_name, result.first_name

        return None, None
