from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from rating.models import Rating, RatingResult


def rating_list(request):
    ratings = Rating.objects.all().order_by('order')

    return render(request, 'rating/list.html', {
        'ratings': ratings,
    })


def rating_details(request, slug):
    rating = get_object_or_404(Rating, slug=slug)

    rating_results = (RatingResult.objects
                                  .filter(rating=rating)
                                  .prefetch_related('player')
                                  .prefetch_related('player__city')
                                  .prefetch_related('player__country')
                                  .order_by('place'))

    return render(request, 'rating/details.html', {
        'rating': rating,
        'rating_results': rating_results,
    })
