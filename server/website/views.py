from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import translation
from django.utils.translation import get_language
from django.views.decorators.cache import cache_page
from haystack.forms import ModelSearchForm

from player.models import Player, TenhouNickname
from rating.models import Rating, RatingResult
from settings.models import City
from tournament.models import Tournament
from utils.tenhou.latest_tenhou_games import get_latest_wg_games


def home(request):
    rating = Rating.objects.get(type=Rating.RR)
    rating_results = (RatingResult.objects
                                  .filter(rating=rating)
                                  .prefetch_related('player')
                                  .prefetch_related('player__city')
                                  .order_by('place'))[:16]

    upcoming_tournaments = (Tournament.objects
                                      .filter(is_upcoming=True)
                                      .exclude(tournament_type=Tournament.FOREIGN_EMA)
                                      .prefetch_related('city')
                                      .order_by('start_date'))

    return render(request, 'website/home.html', {
        'page': 'home',
        'rating_results': rating_results,
        'rating': rating,
        'upcoming_tournaments': upcoming_tournaments
    })


def about(request):
    template = 'about_en.html'
    if get_language() == 'ru':
        template = 'about_ru.html'

    return render(request, 'website/{}'.format(template), {
        'page': 'about'
    })


def contacts(request):
    template = 'contacts_en.html'
    if get_language() == 'ru':
        template = 'contacts_ru.html'

    return render(request, 'website/{}'.format(template), {
        'page': 'contacts'
    })


def search(request):
    query = request.GET.get('q', '')

    search_form = ModelSearchForm(request.GET, load_all=True)
    results = search_form.search()

    query_list = [x.object for x in results]
    players = [x for x in query_list if x.__class__ == Player]

    return render(request, 'website/search.html', {
        'players': players,
        'search_query': query
    })


def city_page(request, slug):
    city = get_object_or_404(City, slug=slug)

    tournaments = Tournament.objects.filter(city=city).order_by('-end_date').prefetch_related('city')

    # small queries optimizations
    rating_results = RatingResult.objects.filter(player__city=city, rating__type=Rating.RR)
    players = Player.objects.filter(city=city).prefetch_related('city')
    for player in players:
        player.rating_result = None

        for rating_result in rating_results:
            if rating_result.player_id == player.id:
                player.rating_result = rating_result

    players = sorted(players, key=lambda x: (x.rating_result and -x.rating_result.score or 0, x.full_name))

    return render(request, 'website/city.html', {
        'city': city,
        'players': players,
        'tournaments': tournaments
    })


def players_api(request):
    translation.activate('ru')

    players = (Player.objects
               .filter(country__code='RU')
               .prefetch_related('city')
               .prefetch_related('tenhou')
               .order_by('id'))

    data = []
    for player in players:
        tenhou_query = player.tenhou.filter(is_main=True).first()
        tenhou_data = None
        if tenhou_query:
            tenhou_data = {
                'username': tenhou_query.tenhou_username,
                'rank': tenhou_query.get_rank_display(),
                'date': tenhou_query.username_created_at.strftime('%Y-%m-%d')
            }

        data.append({
            'id': player.id,
            'name': player.full_name,
            'city': player.city and player.city.name or '',
            'ema_id': player.ema_id or '',
            'tenhou': tenhou_data
        })
    return JsonResponse(data, safe=False)


def online_tournament_rules(request):
    return render(request, 'website/rules.html')


@cache_page(30)
def get_current_tenhou_games(request):
    watching_nicknames = TenhouNickname.objects.all().values_list('tenhou_username', flat=True)
    # let's find players from our database that are playing right now
    found_players = []
    our_players_games = {}
    high_level_games = {}

    games = get_latest_wg_games()
    for game in games:
        for player in game['players']:
            # we found a player from our database
            if player['name'] in watching_nicknames:
                player['is_hirosima'] = len(game['players']) == 3
                found_players.append(player)
                our_players_games[game['game_id']] = game

            if player['dan'] >= 18:
                high_level_games[game['game_id']] = game

    player_profiles = {}

    for player in found_players:
        tenhou_object = TenhouNickname.objects.get(tenhou_username=player['name'])

        if not player['is_hirosima']:
            tenhou_object.four_games_rate = player['rate']
            tenhou_object.save()

        player_profiles[player['name']] = tenhou_object.player

    return render(request, 'website/tenhou_games.html', {
        'our_players_games': our_players_games.values(),
        'high_level_games': high_level_games.values(),
        'player_profiles': player_profiles
    })
