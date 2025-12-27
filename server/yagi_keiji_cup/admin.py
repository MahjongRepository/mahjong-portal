# -*- coding: utf-8 -*-

from django.contrib import admin

from yagi_keiji_cup.models import YagiKeijiCupSettings, YagiKeijiCupResults


class YagiKeijiCupSettingsAdmin(admin.ModelAdmin):
    list_display = ["is_hidden", "tenhou_tournament", "majsoul_tournament"]
    raw_id_fields = ["tenhou_tournament", "majsoul_tournament"]

class YagiKeijiCupResultsAdmin(admin.ModelAdmin):
    list_display = ["team_name", "tenhou_player_place", "tenhou_player", "majsoul_player_place", "majsoul_player", "team_scores"]
    raw_id_fields = ["tenhou_player", "majsoul_player"]


admin.site.register(YagiKeijiCupSettings, YagiKeijiCupSettingsAdmin)
admin.site.register(YagiKeijiCupResults, YagiKeijiCupResultsAdmin)
