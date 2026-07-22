# -*- coding: utf-8 -*-
import ujson
from django.core.management.base import BaseCommand
from django.utils import timezone

from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    OLD_PANTHEON_TYPE = "old"
    NEW_PANTHEON_TYPE = "new"

    def handle(self, *args, **options):
        with open("ts_tournaments.txt", "w") as f:
            tournaments = Tournament.objects.all()
            count = 0
            new_pantheon_tournaments = []
            old_pantheon_tournaments = []
            for tournament in tournaments:
                tournament_results_count = TournamentResult.objects.filter(tournament=tournament.id).count()
                if tournament_results_count > 0:
                    if tournament.new_pantheon_id is not None and tournament.old_pantheon_id is not None:
                        raise RuntimeError(f"Found not valid tournament with id {tournament.id}")
                    if tournament.old_pantheon_id is not None:
                        old_pantheon_tournaments.append(tournament)
                        count += 1
                    if tournament.new_pantheon_id is not None:
                        new_pantheon_tournaments.append(tournament)
                        count += 1

            new_pantheon_tournaments = sorted(new_pantheon_tournaments, key=lambda x: x.new_pantheon_id, reverse=False)
            old_pantheon_tournaments = sorted(old_pantheon_tournaments, key=lambda x: x.old_pantheon_id, reverse=False)

            self.write_tournaments_rows_to_file(new_pantheon_tournaments, self.NEW_PANTHEON_TYPE, f)
            self.write_tournaments_rows_to_file(old_pantheon_tournaments, self.OLD_PANTHEON_TYPE, f)

            print(f"Processed {count} tournaments")

    def write_tournaments_rows_to_file(self, tournaments, pantheon_type, f):
        for tournament in tournaments:
            f.write(
                ujson.dumps(
                    {
                        "type": pantheon_type,
                        "id": self.extract_pantheon_id(tournament, pantheon_type),
                        "name": tournament.name,
                    }
                )
            )
            f.write("\r\n")

    def extract_pantheon_id(self, tournament, pantheon_type):
        if pantheon_type == self.NEW_PANTHEON_TYPE:
            return int(tournament.new_pantheon_id)
        if pantheon_type == self.OLD_PANTHEON_TYPE:
            return int(tournament.old_pantheon_id)
