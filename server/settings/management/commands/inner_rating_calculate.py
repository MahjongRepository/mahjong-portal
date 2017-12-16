from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.models import Rating, RatingDelta


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        RatingDelta.objects.all().delete()

        rating = Rating.objects.get(type=Rating.INNER)
        calculator = InnerRatingCalculation()
        players = Player.all_objects.all().prefetch_related('tournament_results')

        for player in players:
            tournament_results = player.tournament_results.all().prefetch_related('tournament')
            for result in tournament_results:
                rating_delta = calculator.calculate_rating_delta(result)

                RatingDelta.objects.create(tournament=result.tournament,
                                           rating=rating,
                                           player=player,
                                           delta=rating_delta)

        for player in players:
            two_years_ago = timezone.now() - timedelta(days=365 * 2)
            last_results = (RatingDelta.objects
                                       .filter(player=player)
                                       .filter(tournament__date__gte=two_years_ago)
                                       .order_by('-tournament__date')
                                       [:5])

            score = last_results.aggregate(Sum('delta'))['delta__sum']

            last_results_ids = [x.id for x in last_results]

            # we need it to display on user page active deltas
            RatingDelta.objects.filter(player=player).update(is_active=False)
            RatingDelta.objects.filter(id__in=last_results_ids).update(is_active=True)

            player.inner_rating_score = score or 0
            player.save()

        players = Player.all_objects.all().order_by('-inner_rating_score')
        place = 1

        for player in players:
            player.inner_rating_place = place
            player.save()

            place += 1

        print('{0}: End'.format(get_date_string()))
