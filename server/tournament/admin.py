# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from tournament.models import (
    MsOnlineTournamentRegistration,
    OnlineTournamentConfig,
    OnlineTournamentRegistration,
    Tournament,
    TournamentApplication,
    TournamentRegistration,
    TournamentResult,
)


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        exclude = ["name", "registration_description", "results_description"]


class TournamentAdmin(admin.ModelAdmin):
    form = TournamentForm

    prepopulated_fields = {"slug": ["name_en"]}
    list_display = ["name", "country", "end_date", "is_upcoming", "export"]
    list_filter = ["is_event", "tournament_type", "russian_cup", "country"]
    search_fields = ["name_ru", "name_en"]

    ordering = ["-end_date"]

    filter_horizontal = ["clubs"]

    def export(self, obj):
        return mark_safe(
            '<a href="{}">Export to EMA</a>'.format(
                reverse("export_tournament_results", kwargs={"tournament_id": obj.id})
            )
        )


class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "is_approved",
        "tournament",
        "first_name",
        "last_name",
        "city",
        "phone",
        "player",
        "city_object",
        "allow_to_save_data",
    ]

    raw_id_fields = ["tournament", "player", "city_object"]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter]]


class OnlineTournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "is_approved",
        "tournament",
        "first_name",
        "last_name",
        "city",
        "tenhou_nickname",
        "contact",
        "player",
        "city_object",
        "allow_to_save_data",
    ]

    raw_id_fields = ["tournament", "player", "city_object"]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter]]


class MsOnlineTournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "is_approved",
        "tournament",
        "first_name",
        "last_name",
        "city",
        "ms_friend_id",
        "ms_nickname",
        "contact",
        "player",
        "city_object",
        "allow_to_save_data",
    ]

    raw_id_fields = ["tournament", "player", "city_object"]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter]]


class TournamentApplicationAdmin(admin.ModelAdmin):
    list_display = ["tournament_name", "city", "start_date", "created_on"]


class TournamentResultAdmin(admin.ModelAdmin):
    list_display = ["tournament", "player", "place", "scores"]
    search_fields = [
        "tournament__name",
        "player__last_name_ru",
        "player__first_name_ru",
        "player__last_name_en",
        "player__first_name_en",
        "player_string",
    ]
    raw_id_fields = ["tournament", "player"]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter]]


class OnlineTournamentConfigAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "token",
        "online_config",
    ]


admin.site.register(Tournament, TournamentAdmin)
admin.site.register(OnlineTournamentConfig, OnlineTournamentConfigAdmin)
admin.site.register(TournamentRegistration, TournamentRegistrationAdmin)
admin.site.register(OnlineTournamentRegistration, OnlineTournamentRegistrationAdmin)
admin.site.register(MsOnlineTournamentRegistration, MsOnlineTournamentRegistrationAdmin)
admin.site.register(TournamentApplication, TournamentApplicationAdmin)
admin.site.register(TournamentResult, TournamentResultAdmin)
