# -*- coding: utf-8 -*-

from django.core.management import BaseCommand

from tournament.models import MsOnlineTournamentRegistration


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=str)

    def handle(self, *args, **options):
        tournament_id = options.get("tournament_id")

        registrations = MsOnlineTournamentRegistration.objects.filter(tournament_id=tournament_id, is_validated=False)

        if registrations:
            print(f"found {len(registrations)} not validated registrations")
        else:
            print("all registrations is validated")
