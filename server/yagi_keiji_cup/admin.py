# -*- coding: utf-8 -*-

from django.contrib import admin

from yagi_keiji_cup.models import YagiKeijiCupSettings


class YagiKeijiCupSettingsAdmin(admin.ModelAdmin):
    list_display = ["is_hidden", "tenhou_tournament", "majsoul_tournament"]
    raw_id_fields = ["tenhou_tournament", "majsoul_tournament"]


admin.site.register(YagiKeijiCupSettings, YagiKeijiCupSettingsAdmin)
