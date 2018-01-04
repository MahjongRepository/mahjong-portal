import csv
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from player.models import Player
from rating.calculation.inner import InnerRatingCalculation
from rating.models import RatingDelta, RatingResult, TournamentCoefficients
from settings.models import TournamentType
from tournament.models import Tournament, TournamentResult


class EmaRatingCalculation(InnerRatingCalculation):

    def get_players(self):
        results = TournamentResult.objects.exclude(tournament__tournament_type__slug=TournamentType.CLUB)
        return list(Player.objects.filter(id__in=results.values_list('player_id', flat=True)))

    def calculate_players_rating_rank(self, rating):
        # f = open('players.csv', 'w')
        # writer = csv.writer(f)
        #
        # writer.writerow([
        #     'игрок',
        #     'итоговые очки',
        #     'всего турниров',
        #     'учитываемых турниров',
        #     'турнирный base rank',
        #     'первая часть',
        #     'вторая часть',
        #     'расчет рейтинга',
        #     'расчет первой части',
        #     'расчет второй части',
        # ])

        # rows = []
        results = []
        two_years_ago = timezone.now().date() - timedelta(days=365 * 2)

        first_part_min_tournaments = 5
        second_part_min_tournaments = 4
        first_part_weight = 50
        second_part_weight = 50

        RatingResult.objects.filter(rating=rating).delete()

        for player in self.players:
            # row = []

            first_part_numerator_calculation = []
            first_part_denominator_calculation = []

            second_part_numerator_calculation = []
            second_part_denominator_calculation = []

            deltas = (RatingDelta.objects
                                 .filter(rating=rating, player=player)
                                 .filter(tournament__end_date__gte=two_years_ago))
            total_tournaments = deltas.count()

            if total_tournaments < 2:
                continue

            # tournaments_results = deltas
            # tournaments_in_rating = total_tournaments

            if total_tournaments <= first_part_min_tournaments:
                tournaments_results = deltas
                # tournaments_in_rating = total_tournaments
            else:
                limit = self._determine_tournaments_number(deltas.count())
                tournaments_results = deltas.order_by('-base_rank')[:limit]
                # tournaments_in_rating = limit

            deltas.update(is_active=False)
            for result in tournaments_results:
                result.is_active = True
                result.save()

            first_part_numerator = 0
            first_part_denominator = 0

            for result in tournaments_results:
                coefficient = TournamentCoefficients.objects.get(rating=rating, tournament=result.tournament)

                first_part_numerator += float(result.delta)
                first_part_denominator += float(self._calculate_percentage(float(coefficient.coefficient), coefficient.age))

                first_part_numerator_calculation.append('{} * {} * {}'.format(result.base_rank, coefficient.coefficient, coefficient.age / 100))
                first_part_denominator_calculation.append('{} * {}'.format(coefficient.coefficient, coefficient.age / 100))

            if len(tournaments_results) < first_part_min_tournaments:
                fill_missed_data = first_part_min_tournaments - len(tournaments_results)
                first_part_denominator += fill_missed_data

                for x in range(0, fill_missed_data):
                    first_part_numerator_calculation.append('0')
                    first_part_denominator_calculation.append('1')

            first_part = first_part_numerator / first_part_denominator

            second_part_numerator = 0
            second_part_denominator = 0

            best_results = deltas.order_by('-base_rank')[:second_part_min_tournaments]
            for result in best_results:
                coefficient = TournamentCoefficients.objects.get(rating=rating, tournament=result.tournament)

                second_part_numerator += float(result.delta)
                second_part_denominator += float(self._calculate_percentage(float(coefficient.coefficient), coefficient.age))

                second_part_numerator_calculation.append('{} * {} * {}'.format(result.base_rank, coefficient.coefficient, coefficient.age / 100))
                second_part_denominator_calculation.append('{} * {}'.format(coefficient.coefficient, coefficient.age / 100))

            if len(tournaments_results) < second_part_min_tournaments:
                fill_missed_data = second_part_min_tournaments - len(best_results)
                second_part_denominator += fill_missed_data

                for x in range(0, fill_missed_data):
                    second_part_numerator_calculation.append('0')
                    second_part_denominator_calculation.append('1')

            second_part = second_part_numerator / second_part_denominator

            score = self._calculate_percentage(first_part, first_part_weight) + self._calculate_percentage(second_part, second_part_weight)

            first_part_calculation = '({}) / ({})'.format(' + '.join(first_part_numerator_calculation), ' + '.join(first_part_denominator_calculation))
            second_part_calculation = '({}) / ({})'.format(' + '.join(second_part_numerator_calculation), ' + '.join(second_part_denominator_calculation))
            rating_calculation = '({}) * {} + ({}) * {}'.format(first_part_calculation, first_part_weight / 100, second_part_calculation, second_part_weight / 100)

            results.append(RatingResult.objects.create(
                rating=rating,
                player=player,
                score=score,
                place=0,
                rating_calculation=rating_calculation
            ))

            # row.append('{} {}'.format(player.last_name_ru, player.first_name_ru))
            # row.append(round(score, 2))
            # row.append(total_tournaments)
            # row.append(tournaments_in_rating)
            # row.append(sorted([float(x.base_rank) for x in tournaments_results], reverse=True))
            # row.append(round(first_part, 2))
            # row.append(round(second_part, 2))
            # row.append('{} * {} + {} * {}'.format(round(first_part, 2), first_part_weight / 100, round(second_part, 2), second_part_weight / 100))
            # row.append('({}) / ({})'.format(' + '.join(first_part_numerator_calculation), ' + '.join(first_part_denominator_calculation)))
            # row.append('({}) / ({})'.format(' + '.join(second_part_numerator_calculation), ' + '.join(second_part_denominator_calculation)))
            #
            # rows.append(row)

        # rows = sorted(rows, key=lambda x: x[1], reverse=True)
        # writer.writerows(rows)
        # f.close()

        place = 1
        results = sorted(results, key=lambda x: x.score, reverse=True)
        for result in results:
            result.place = place
            result.save()

            place += 1

    def tournament_coefficient(self, tournament):
        return self.players_coefficient(tournament) +\
               self.duration_coefficient(tournament) +\
               self.countries_coefficient(tournament) +\
               self.qualification_coefficient(tournament)

    def players_coefficient(self, tournament):
        if tournament.number_of_players <= 40:
            return 0.0
        elif 41 <= tournament.number_of_players <= 80:
            return 0.5
        else:
            return 1.0

    def duration_coefficient(self, tournament):
        diff = relativedelta(tournament.end_date, tournament.start_date)
        days = diff.days + 1
        if days > 3:
            days = 3
        return days

    def countries_coefficient(self, tournament):
        results = TournamentResult.objects.filter(tournament=tournament).values_list('player__country__code', flat=True).distinct()
        number_of_countries = len(results)
        if number_of_countries <= 5:
            return 0.0
        elif 5 < number_of_countries <= 10:
            return 0.5
        else:
            return 1.0

    def qualification_coefficient(self, tournament):
        return tournament.need_qualification and 1 or 0

    def tournament_age(self, tournament):
        today = timezone.now().date()
        end_date = tournament.end_date
        diff = relativedelta(today, end_date)
        months = diff.years * 12 + diff.months + diff.days / 30

        if months <= 12:
            return 100
        elif 12 < months <= 24:
            return 50
        else:
            return 0
