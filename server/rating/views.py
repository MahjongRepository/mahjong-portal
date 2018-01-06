from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404

from rating.models import Rating, RatingResult


def rating_list(request):
    ratings = Rating.objects.all().order_by('order')

    return render(request, 'rating/list.html', {
        'ratings': ratings,
    })


def rating_details(request, slug, page=None):
    rating = get_object_or_404(Rating, slug=slug)

    rating_results = RatingResult.objects.filter(rating=rating).order_by('place')

    page = page or 1
    one_page = True

    if page != 'all':
        one_page = False

        paginator = Paginator(rating_results, 25)

        try:
            rating_results = paginator.page(page)
        except PageNotAnInteger:
            rating_results = paginator.page(1)
        except EmptyPage:
            rating_results = paginator.page(paginator.num_pages)

    return render(request, 'rating/details.html', {
        'rating': rating,
        'rating_results': rating_results,
        'one_page': one_page
    })
