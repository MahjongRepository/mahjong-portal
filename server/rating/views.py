from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from rating.models import Rating, RatingResult


def rating_list(request):
    ratings = Rating.objects.all().order_by('order')

    return render(request, 'rating/list.html', {
        'ratings': ratings,
        'page': 'rating'
    })


def rating_details(request, slug):
    rating = get_object_or_404(Rating, slug=slug)

    rating_results = (RatingResult.objects
                                  .filter(rating=rating)
                                  .prefetch_related('player')
                                  .prefetch_related('player__city')
                                  .prefetch_related('player__country')
                                  .order_by('place'))

    render_as_json = request.GET.get('json')
    if render_as_json is not None:
        data = []
        for rating_result in rating_results:
            data.append({
                'id': rating_result.player.id,
                'place': rating_result.place,
                'scores': float(rating_result.score),
                'name': rating_result.player.full_name,
                'city': rating_result.player.city.name
            })
        return JsonResponse(data, safe=False)
    else:
        return render(request, 'rating/details.html', {
            'rating': rating,
            'rating_results': rating_results,
            'page': 'rating'
        })
