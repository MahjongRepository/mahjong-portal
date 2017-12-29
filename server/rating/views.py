from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from player.models import Player
from rating.models import Rating, RatingResult


def rating_list(request, slug):
    rating = get_object_or_404(Rating, slug=slug)

    rating_results = RatingResult.objects.filter(rating=rating).order_by('place')

    page = request.GET.get('page')
    paginator = Paginator(rating_results, 25)

    try:
        rating_results = paginator.page(page)
    except PageNotAnInteger:
        rating_results = paginator.page(1)
    except EmptyPage:
        rating_results = paginator.page(paginator.num_pages)

    return render(request, 'rating/list.html', {
        'rating': rating,
        'rating_results': rating_results,
    })
