import datetime

from django.shortcuts import render

from rating.models import RatingResult, Rating
from rating.utils import get_latest_rating_date


def best_countries(request):
    rating = Rating.objects.get(type=Rating.EMA)
    today, rating_date = get_latest_rating_date(rating)
    ema_ratings = RatingResult.objects.filter(
        rating=rating,
        date=rating_date
    ).prefetch_related('player', 'rating', 'player__country')
    countries = _get_countries_data(ema_ratings)
    return render(request, 'ema/best_countries.html', {'countries': countries})


def ema_quotas(request):
    """
    More details:
    http://mahjong-europe.org/ranking/BasicsQuotas.html
    """
    total_seats = 70
    scores_required = 700

    # European and World champions
    available_seats = total_seats - 2

    ema_ratings = RatingResult.objects.filter(
        rating__type=Rating.EMA,
        date=datetime.date(2020, 1, 1)
    ).prefetch_related('player', 'rating', 'player__country')
    countries_data = _get_countries_data(ema_ratings)

    for rank, data in enumerate(countries_data):
        data['b_quota'] = 0
        data['country_players'] = len(data['players_rating'])
        data['country_required_rating_players'] = len(
            [x for x in data['players_rating'] if x['score'] >= scores_required]
        )

    quotas = {}

    # First, seats will be given to all countries in descending order of ranking
    countries_data = sorted(countries_data, key=lambda x: x['country_rating'], reverse=True)
    for rank, data in enumerate(countries_data):
        country = data['country']

        available_seats -= 1
        quotas[country.code] = {
            'country': country,
            'rank': rank + 1,
            'seats': 1
        }

    # After this, seats will be given to all countries with a player with >700 points, in
    # descending order of country ranking (part A3)
    for data in countries_data:
        country = data['country']
        if data['country_required_rating_players'] == 0:
            continue

        available_seats -= 1
        quotas[country.code]['seats'] += 1

    # Then seats will be given to the top 3 ranked countries in the EMA, in descending
    # order of country ranking (part A2)
    top_countries = 3
    for data in countries_data[:top_countries]:
        country = data['country']
        available_seats -= 1
        quotas[country.code]['seats'] += 1

    # Finally, any leftover seats will be distributed using part B of the quota formula.
    total_players = sum([data['country_players'] for data in countries_data])
    total_required_rating_players = sum([data['country_required_rating_players'] for data in countries_data])

    n = 0
    while n < available_seats:
        n += 1

        for data in countries_data:
            country_players = data['country_players']
            country_required_rating_players = data['country_required_rating_players']

            b1 = country_players / total_players
            b2 = country_required_rating_players / total_required_rating_players
            b3 = (b1 + b2) / 2
            data['b_coefficient'] = b3 * n

        # Increase the B-quota of the country with the largest B3*N that is also smaller than its
        # current B-quota by 1
        countries_data = sorted(countries_data, key=lambda x: x['b_coefficient'] - x['b_quota'], reverse=True)
        for data in countries_data:
            if data['b_quota'] <= data['b_coefficient']:
                data['b_quota'] += 1
                break

    total_quotas = 0
    countries_data = sorted(countries_data, key=lambda x: x['country_rating'])
    for data in countries_data:
        country = data['country']
        quotas[country.code]['seats'] += data['b_quota']

        total_quotas += quotas[country.code]['seats']

    quotas = sorted(quotas.values(), key=lambda x: x['rank'])

    return render(request, 'ema/quotas.html', {
        'quotas': quotas,
        'total_quotas': total_quotas
    })


def _get_countries_data(ema_ratings):
    countries_temp = {}
    for rating in ema_ratings:
        country_code = rating.player.country.code
        if country_code not in countries_temp:
            countries_temp[country_code] = {
                'country': rating.player.country,
                'players_rating': []
            }

        countries_temp[country_code]['players_rating'].append({
            'player': rating.player,
            'score': rating.score,
        })

    countries = []
    for data in countries_temp.values():
        best_3 = sorted(data['players_rating'], key=lambda x: x['score'], reverse=True)[:3]
        countries.append({
            'country': data['country'],
            'players_rating': data['players_rating'],
            'number_of_players': len(data['players_rating']),
            'country_rating': sum([x['score'] for x in best_3]) / 3,
            'best_3': best_3,
        })

    countries = sorted(countries, key=lambda x: x['country_rating'], reverse=True)
    return countries
