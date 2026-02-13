# -*- coding: utf-8 -*-

from django.contrib import admin

from player.mahjong_soul.models import MSAccount, MSAccountStatistic, MSPointsHistory


class MSAccountAdmin(admin.ModelAdmin):
    list_display = ["account_id", "account_name", "player"]
    search_fields = [
        "account_id",
        "account_name",
        "player__first_name_ru",
        "player__first_name_en",
        "player__last_name_ru",
        "player__last_name_en",
    ]
    raw_id_fields = ["player"]


class MSAccountStatisticAdmin(admin.ModelAdmin):
    list_display = ["account", "game_type", "rank", "points"]
    search_fields = ["account__account_id", "account__account_name"]
    list_filter = ["game_type"]


class MSPointsHistoryAdmin(admin.ModelAdmin):
    list_display = ["stat_object", "rank", "points", "created_on"]
    search_fields = ["stat_object__account__account_id", "stat_object__account__account_name"]
    list_filter = ["stat_object__account"]


admin.site.register(MSAccount, MSAccountAdmin)
admin.site.register(MSAccountStatistic, MSAccountStatisticAdmin)
admin.site.register(MSPointsHistory, MSPointsHistoryAdmin)
