import random

import ujson as json
from django.core.management.base import BaseCommand

from online.team_seating import TeamSeating
from tournament.models import Tournament


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=int)

    def handle(self, *args, **options):
        tournament_id = options["tournament_id"]
        tournament = Tournament.objects.get(id=tournament_id)
        assert tournament.tournament_type == Tournament.ONLINE

        registrations = tournament.online_tournament_registrations.all()

        pantheon_id_map = {}
        for i, item in enumerate(registrations):
            assert item.player.pantheon_id
            pantheon_id_map[i + 1] = item.player.pantheon_id

        with open(TeamSeating.initial_seating, "r") as f:
            initial_seating = f.read()

        rounds_text = initial_seating.splitlines()
        rounds = []
        for r in rounds_text:
            seating = []
            tables_text = r.split()

            for t in tables_text:
                players_ids = list(set([int(x) for x in t.split("-")]))
                assert len(players_ids) == 4

                random.shuffle(players_ids)
                seating.append([pantheon_id_map[x] for x in players_ids])

            rounds.append(seating)

        data = {"seating": rounds}

        with open(TeamSeating.processed_seating, "w") as f:
            f.write(json.dumps(data))

        print("Seating was saved to {}".format(TeamSeating.processed_seating))

        # from player.models import Player
        # from django.utils.translation import activate
        # activate('ru')
        # for i, round_item in enumerate(rounds):
        #     print(f'\nХанчан {i + 1}\n')
        #     for j, table in enumerate(round_item):
        #         print(f"Стол {j + 1}")
        #         print(', '.join([Player.objects.get(pantheon_id=x).full_name for x in table]))
