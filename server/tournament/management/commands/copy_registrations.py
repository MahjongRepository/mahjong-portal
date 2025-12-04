# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils import timezone

from tournament.models import MsOnlineTournamentRegistration, OnlineTournamentRegistration, Tournament


def get_date_string():
    return timezone.now().strftime("%H:%M:%S")


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--main-tournament", type=int)
        parser.add_argument("--first-donor-tournament", type=int)
        parser.add_argument("--second-donor-tournament", type=int)

    def handle(self, *args, **options):
        print("{0}: Start copy players registrations".format(get_date_string()))
        main_tournament_id = int(options.get("main_tournament"))
        main_tournament = Tournament.objects.get(id=main_tournament_id)

        first_donor_tournament_id = int(options.get("first_donor_tournament"))
        first_donor_tournament = Tournament.objects.get(id=first_donor_tournament_id)

        registrations = self.load_registrations(first_donor_tournament)
        for registration in registrations:
            self.copy_registration(main_tournament, registration)

        second_donor_tournament_id = int(options.get("second_donor_tournament"))
        second_donor_tournament = Tournament.objects.get(id=second_donor_tournament_id)

        registrations = self.load_registrations(second_donor_tournament)
        for registration in registrations:
            self.copy_registration(main_tournament, registration)

        print("{0}: Finish copy players registrations".format(get_date_string()))

    def load_registrations(self, tournament):
        if tournament.is_majsoul_tournament:
            return MsOnlineTournamentRegistration.objects.filter(tournament=tournament, is_approved=True)
        else:
            return OnlineTournamentRegistration.objects.filter(tournament=tournament, is_approved=True)

    def copy_registration(self, tournament, registration):
        if tournament.is_online():
            if tournament.is_majsoul_tournament:
                MsOnlineTournamentRegistration.objects.get_or_create(
                    tournament=tournament,
                    user=registration.user,
                    first_name=registration.first_name,
                    last_name=registration.last_name,
                    city=registration.city,
                    player=registration.player,
                    city_object=registration.city_object,
                    allow_to_save_data=registration.allow_to_save_data,
                    notes=registration.notes,
                    is_approved=registration.is_approved,
                    confirm_code=registration.confirm_code,
                )
            else:
                OnlineTournamentRegistration.objects.get_or_create(
                    tournament=tournament,
                    user=registration.user,
                    first_name=registration.first_name,
                    last_name=registration.last_name,
                    city=registration.city,
                    player=registration.player,
                    city_object=registration.city_object,
                    allow_to_save_data=registration.allow_to_save_data,
                    notes=registration.notes,
                    is_approved=registration.is_approved,
                    confirm_code=registration.confirm_code,
                )
