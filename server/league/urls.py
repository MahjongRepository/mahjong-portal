from django.urls import path

from league.views import league_details, league_schedule, league_teams

urlpatterns = [
    path("<str:slug>/", league_details, name="league_details"),
    path("<str:slug>/teams/", league_teams, name="league_teams"),
    path("<str:slug>/schedule/", league_schedule, name="league_schedule"),
]
