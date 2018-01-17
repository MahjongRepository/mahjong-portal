from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rating.calculation.crr import RatingCRRCalculation
from rating.calculation.ema import EmaRatingCalculation
from rating.calculation.rr import RatingRRCalculation
from rating.models import Rating, RatingDelta, RatingResult
from settings.models import TournamentType
from tournament.models import Tournament, TournamentResult


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rr_type = TournamentType.objects.get(slug=TournamentType.RR)
        crr_type = TournamentType.objects.get(slug=TournamentType.CRR)

        rr_tournaments = (Tournament.objects.all()
                                    .exclude(tournament_type__slug=TournamentType.EMA)
                                    .exclude(tournament_type__slug=TournamentType.FOREIGN_EMA)
                                    .exclude(tournament_type__slug=TournamentType.OTHER)
                                    .filter(number_of_players__gte=16)
                                    .filter(has_accreditation=True)
                                    .filter(need_qualification=False))

        for tournament in rr_tournaments:
            tournament.tournament_type = rr_type
            tournament.save()

        crr_tournaments = (Tournament.objects
                                     .exclude(id__in=[x.id for x in rr_tournaments])
                                     .exclude(tournament_type__slug=TournamentType.EMA)
                                     .exclude(tournament_type__slug=TournamentType.FOREIGN_EMA)
                                     .exclude(tournament_type__slug=TournamentType.OTHER))

        for tournament in crr_tournaments:
            tournament.tournament_type = crr_type
            tournament.save()

        print('{0}: End'.format(get_date_string()))
