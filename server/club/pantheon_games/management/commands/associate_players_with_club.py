from django.core.management.base import BaseCommand
from django.utils import timezone

from club.models import Club
from club.pantheon_games.models import PantheonEvent, PantheonPlayer, PantheonSession, PantheonSessionResult
from player.models import Player


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    # We had to run this command
    # to set pantheon ids to users

    def add_arguments(self, parser):
        parser.add_argument("--club-id", type=int, default=None)

    def handle(self, *args, **options):
        print("{0}: Start".format(get_date_string()))

        club_id = options.get("club_id")

        if club_id:
            clubs = Club.objects.filter(id=club_id)
        else:
            clubs = Club.objects.exclude(pantheon_ids__isnull=True)

        for club in clubs:
            event_ids = club.pantheon_ids.split(",") + [club.current_club_rating_pantheon_id]
            print("")
            print("Processing: id={}, {}".format(club.id, club.name))
            print("Events: {}".format(event_ids))

            self._associate_players(club, event_ids)

        print("")
        print("{0}: End".format(get_date_string()))

    def _associate_players(self, club, event_ids):
        print("Associating players...")

        club.players.clear()

        player_ids = []
        events = PantheonEvent.objects.filter(id__in=event_ids)
        for event in events:
            sessions = PantheonSession.objects.filter(event=event, status=PantheonSession.FINISHED)

            for session in sessions:
                player_ids.extend([x.player_id for x in session.players.all()])

        player_ids = list(set(player_ids))
        players = PantheonPlayer.objects.filter(id__in=player_ids)

        missed_players = []
        # set pantheon ids
        for pantheon_player in players:
            temp = pantheon_player.display_name.split(" ")
            last_name = temp[0].title()
            first_name = len(temp) > 1 and temp[1].title() or ""

            player = None

            # it could be that pantheon and portal has different names
            # so lets try to load player with pantheon id
            if not player:
                try:
                    player = Player.objects.get(pantheon_id=pantheon_player.id)
                except Player.DoesNotExist:
                    pass

            # let's try to match player by first and last name
            if not player:
                try:
                    player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name)
                    player.pantheon_id = pantheon_player.id
                    player.save()
                except Player.DoesNotExist:
                    pass
                except Player.MultipleObjectsReturned:
                    # if we have multiple players with same name
                    # let's try to add city to query
                    try:
                        player = Player.objects.get(first_name_ru=first_name, last_name_ru=last_name, city=club.city)
                    except (Player.DoesNotExist, Player.MultipleObjectsReturned):
                        # two players with same name from the same city
                        # we can't handle it automatically
                        pass

            if player:
                club.players.add(player)
            else:
                games_count = PantheonSessionResult.objects.filter(player_id=pantheon_player.id).count()
                if games_count >= 10:
                    missed_players.append(
                        {
                            "pantheon_id": pantheon_player.id,
                            "name": pantheon_player.display_name,
                            "games_count": games_count,
                        }
                    )

        missed_players = sorted(missed_players, key=lambda x: -x["games_count"])
        for missed_player in missed_players:
            print(
                f"Missed player: id={missed_player['pantheon_id']}, {missed_player['name']}, Games: {missed_player['games_count']} "
            )

        print("Associating completed")
