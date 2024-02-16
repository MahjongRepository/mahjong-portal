# -*- coding: utf-8 -*-

from django.core.management import BaseCommand

from player.mahjong_soul.models import MSAccount
from tournament.models import MsOnlineTournamentRegistration


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=str)

    def handle(self, *args, **options):
        tournament_id = options.get("tournament_id")

        registrations = MsOnlineTournamentRegistration.objects.filter(
            tournament_id=tournament_id, is_validated=True, allow_to_save_data=True
        )

        if registrations:
            print(f"found {len(registrations)} validated registrations")
            for registration in registrations:
                MSAccount.objects.get_or_create(
                    player=registration.player,
                    account_id=registration.ms_account_id,
                    account_name=registration.ms_nickname,
                )
                print(f"ms account {registration.ms_nickname}[{registration.ms_account_id}] added")
        else:
            print("validated registrations not found")
