from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from account.forms import UserCreationForm
from account.models import AttachingPlayerRequest
from player.models import Player


def account_settings(request):
    return render(request, "account/settings.html")


def sign_up(request):
    form = UserCreationForm()
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    return render(request, "account/sign_up.html", {"form": form})


@login_required
@require_POST
def request_player_and_user_connection(request, slug):
    player = get_object_or_404(Player, slug=slug)
    contacts = request.POST.get("contacts")
    if not contacts:
        return redirect("player_details", slug)

    AttachingPlayerRequest.objects.create(user=request.user, player=player, contacts=contacts)
    messages.success(request, _("Request was created."))
    return redirect("player_details", player.slug)
