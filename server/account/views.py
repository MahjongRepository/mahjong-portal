from django.contrib.auth import login
from django.shortcuts import redirect, render

from account.forms import UserCreationForm


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
