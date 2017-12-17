from decimal import Decimal


class InnerRatingCalculation(object):

    def calculate_tournament_coefficient(self, tournament):
        base = Decimal(1.0)
        calculated = base

        if tournament.number_of_players >= 40:
            calculated += Decimal(0.1)

        if tournament.number_of_players >= 60:
            calculated += Decimal(0.05)

        if tournament.number_of_players >= 80:
            calculated += Decimal(0.05)

        if tournament.number_of_sessions >= 8:
            calculated += Decimal(0.1)

        if tournament.number_of_sessions >= 10:
            calculated += Decimal(0.02)

        if tournament.number_of_sessions >= 12:
            calculated += Decimal(0.03)

        return float(calculated)

    def calculate_base_rank(self, tournament_result):
        number_of_players = tournament_result.tournament.number_of_players
        place = tournament_result.place
        middle = number_of_players / 2

        # first place
        if place == 1:
            return 1000

        # last place
        if place == middle:
            return 0

        if place == number_of_players:
            return -1000

        calculated = round(((number_of_players - place - middle) / (number_of_players - middle - 1)) * 1000)

        return calculated

    def calculate_rating_delta(self, tournament_result):
        tournament_coefficient = self.calculate_tournament_coefficient(tournament_result.tournament)
        base_rank = self.calculate_base_rank(tournament_result)
        return round(tournament_coefficient * base_rank)
