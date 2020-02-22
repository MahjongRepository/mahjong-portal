from django.core.management.base import BaseCommand

from rating.models import RatingDate, RatingResult, RatingDelta, Rating
from tournament.models import Tournament


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("tournament_id", type=int)
        parser.add_argument("rating_type", type=str)

    def handle(self, *args, **options):
        tournament_id = options["tournament_id"]
        rating_type = options["rating_type"]

        rating = Rating.objects.get(slug=rating_type)
        tournament = Tournament.objects.get(id=tournament_id)

        RatingDate.objects.filter(date__gte=tournament.end_date, rating=rating).delete()
        RatingResult.objects.filter(date__gte=tournament.end_date, rating=rating).delete()
        RatingDelta.objects.filter(date__gte=tournament.end_date, rating=rating).delete()
