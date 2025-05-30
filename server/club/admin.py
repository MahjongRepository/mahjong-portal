# -*- coding: utf-8 -*-

from django import forms
from django.contrib import admin

from club.models import Club


class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        exclude = ["name"]


class ClubAdmin(admin.ModelAdmin):
    form = ClubForm
    prepopulated_fields = {"slug": ["name_en"]}

    list_display = ["name", "city"]
    search_fields = ["name"]

    filter_horizontal = ["players"]

    fieldsets = [
        [
            None,
            {
                "fields": [
                    "name_ru",
                    "name_en",
                    "slug",
                    "description_ru",
                    "description_en",
                ]
            },
        ],
        ["Contacts", {"fields": ["website"]}],
        ["Location", {"fields": ["country", "city", "lat", "lng", "timezone"]}],
        ["System", {"fields": ["current_club_rating_pantheon_id", "pantheon_ids"]}],
    ]


admin.site.register(Club, ClubAdmin)
