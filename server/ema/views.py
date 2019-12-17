from django.shortcuts import render

from rating.models import RatingResult, Rating


def best_countries(request):
    ema_ratings = RatingResult.objects.filter(
        rating__type=Rating.EMA,
        is_last=True
    ).prefetch_related('player', 'rating', 'player__country')

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
            'number_of_players': len(data['players_rating']),
            'country_rating': sum([x['score'] for x in best_3]) / 3,
            'best_3': best_3,
        })

    # for x in countries:
    #     for j in x['best_3']:
    #         print(j['player'])

    countries = sorted(countries, key=lambda x: x['country_rating'], reverse=True)
    return render(request, 'ema/best_countries.html', {'countries': countries})
