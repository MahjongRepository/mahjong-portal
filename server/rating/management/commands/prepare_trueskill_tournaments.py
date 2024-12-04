# -*- coding: utf-8 -*-
import ujson
from django.core.management.base import BaseCommand
from django.utils import timezone

from tournament.models import Tournament


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open("ts_tournaments.txt", "w") as f:
            tournaments = Tournament.objects.all()
            count = 0
            for tournament in tournaments:
                if tournament.new_pantheon_id is not None and tournament.old_pantheon_id is not None:
                    raise RuntimeError(f"Found not valid tournament with id {tournament.id}")
                if tournament.old_pantheon_id is not None:
                    f.write(ujson.dumps({"type": "old", "id": int(tournament.old_pantheon_id)}))
                    f.write("\r\n")
                    count += 1
                if tournament.new_pantheon_id is not None:
                    f.write(ujson.dumps({"type": "new", "id": int(tournament.new_pantheon_id)}))
                    f.write("\r\n")
                    count += 1
            print(f"Processed {count} tournaments")
