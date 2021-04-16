from django.shortcuts import render


def wiki_home(request):
    return render(request, "wiki/home.html", {"page": "wiki"})
