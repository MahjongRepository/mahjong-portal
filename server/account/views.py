from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from account.forms import LoginForm
from account.models import AttachingPlayerRequest, User
from league.models import LeaguePlayer
from player.models import Player


def do_login(request):
    form = LoginForm(initial={"next": request.GET.get("next", "/")})
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            pantheon_id = form.user_data["id"]
            try:
                user = User.objects.get(new_pantheon_id=pantheon_id)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=form.user_data["email"],
                    email=form.user_data["email"],
                    password=None,
                )
                user.new_pantheon_id = pantheon_id
                user.save()

            login(request, user)

            try:
                league_player = LeaguePlayer.objects.get(name=form.user_data["title"])
                league_player.user = user
                league_player.save()
            except LeaguePlayer.DoesNotExist:
                pass

            return redirect(form.cleaned_data["next"])

    return render(request, "account/login.html", {"form": form})


def account_settings(request):
    return render(request, "account/settings.html")


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
