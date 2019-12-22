from django.core.management.base import BaseCommand

from rating.models import RatingDate, RatingResult, RatingDelta
from tournament.models import Tournament


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', type=int)

    def handle(self, *args, **options):
        tournament_id = options['tournament_id']
        tournament = Tournament.objects.get(id=tournament_id)

        RatingDate.objects.filter(date__gte=tournament.end_date).delete()
        RatingResult.objects.filter(date__gte=tournament.end_date).delete()
        RatingDelta.objects.filter(date__gte=tournament.end_date).delete()
