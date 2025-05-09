# -*- coding: utf-8 -*-

from django.shortcuts import render

from player.models import PlayerTitle


def titles_list(request):
    titles = PlayerTitle.objects.exclude(is_hide=True).order_by("created_on").all()
    player_titles = {}
    for title in titles:
        if title.player:
            if title.player.id in player_titles:
                player_titles[title.player.id]["titles"].append(title)
                player_titles[title.player.id]["titles"].sort(key=lambda title: title.order, reverse=False)
            else:
                player_titles[title.player.id] = {"player": title.player, "titles": [title]}

    return render(request, "title/list.html", {"titles": player_titles.items(), "page": "titles"})
