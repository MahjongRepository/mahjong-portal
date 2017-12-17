from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.models import Rating, RatingDelta
from tournament.models import Tournament, TournamentResult


INCLUDED_YEARS = 2
TOURNAMENT_RESULTS = 10


def get_date_string():
    return timezone.now().strftime('%H:%M:%S')


class Command(BaseCommand):

    def handle(self, *args, **options):
        print('{0}: Start'.format(get_date_string()))

        rating = Rating.objects.get(type=Rating.INNER)

        RatingDelta.objects.filter(rating=rating).delete()
        Player.objects.all().update(inner_rating_place=None)
        Player.objects.all().update(inner_rating_score=None)

        calculator = InnerRatingCalculation()

        tournaments = Tournament.objects.all().order_by('date')

        processed = 1
        total = tournaments.count()
        for tournament in tournaments:
            print('Process {}/{}'.format(processed, total))

            results = (TournamentResult.objects
                                       .filter(tournament=tournament)
                                       .prefetch_related('tournament')
                                       .prefetch_related('player'))
            for result in results:
                player = result.player
                rating_delta = calculator.calculate_rating_delta(result)

                place_before = 0
                if RatingDelta.objects.filter(player=player, rating=rating).exists():
                    place_before = player.inner_rating_place

                RatingDelta.objects.create(tournament=result.tournament,
                                           tournament_place=result.place,
                                           rating=rating,
                                           player=player,
                                           delta=rating_delta,
                                           rating_place_before=place_before)

                if not player.inner_rating_score:
                    player.inner_rating_score = 0

                player.inner_rating_score += rating_delta
                player.save()

            self.recalculate_players_positions(tournament, rating)

            processed += 1

        print('{0}: End'.format(get_date_string()))

    def recalculate_players_positions(self, tournament, rating):
        self.chose_active_tournament_results(tournament, rating)

        players = Player.all_objects.all().order_by('-inner_rating_score')

        deltas = RatingDelta.objects.filter(tournament=tournament, rating=rating).prefetch_related('player')
        for delta in deltas:
            for player in players:
                if player.id == delta.player_id:
                    delta.rating_place_after = player.inner_rating_place
                    delta.save()

    def chose_active_tournament_results(self, tournament, rating):
        players = Player.all_objects.all()

        for player in players:
            two_years_ago = tournament.date - timedelta(days=365 * INCLUDED_YEARS)
            last_results = (RatingDelta.objects
                                       .filter(player=player)
                                       .filter(rating=rating)
                                       .filter(tournament__date__gte=two_years_ago)
                                       .order_by('-tournament__date')[:TOURNAMENT_RESULTS])

            score = last_results.aggregate(Sum('delta'))['delta__sum']

            last_results_ids = [x.id for x in last_results]

            # we need it to display on user page active deltas
            RatingDelta.objects.filter(player=player, rating=rating).update(is_active=False)
            RatingDelta.objects.filter(id__in=last_results_ids, rating=rating).update(is_active=True)

            player.inner_rating_score = score
            player.save()

        players = Player.all_objects.all().order_by('-inner_rating_score')
        place = 1

        for player in players:
            player.inner_rating_place = place
            player.save()

            place += 1
