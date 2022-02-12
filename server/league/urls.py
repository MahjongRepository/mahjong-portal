from django.urls import path

from league.views import league_confirm_slot, league_details, league_schedule, league_teams, start_game

urlpatterns = [
    path("<str:slug>/", league_details, name="league_details"),
    path("<str:slug>/teams/", league_teams, name="league_teams"),
    path("<str:slug>/schedule/", league_schedule, name="league_schedule"),
    path("confirm-slot/<int:slot_id>/", league_confirm_slot, name="league_confirm_slot"),
    path("start-game/<int:game_id>/", start_game, name="start_game"),
]
