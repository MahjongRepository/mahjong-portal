# -*- coding: utf-8 -*-

from django.contrib import admin

from player.tenhou.models import TenhouAggregatedStatistics, TenhouStatistics


class TenhouStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        "player",
        "player_city",
        "tenhou_object",
        "rank",
        "lobby",
        "played_games",
        "average_place",
        "last_played_date",
    ]
    list_filter = ["lobby", "stat_type"]

    def player(self, obj):
        return obj.tenhou_object.player.full_name

    def player_city(self, obj):
        return obj.tenhou_object.player.city

    def rank(self, obj):
        return obj.tenhou_object.get_rank_display()

    rank.short_description = "Rank"
    rank.admin_order_field = "tenhou_object__rank"

    def last_played_date(self, obj):
        return obj.tenhou_object.last_played_date


class TenhouAggregatedStatisticsAdmin(admin.ModelAdmin):
    list_display = ["player", "tenhou_object", "rank", "game_players", "played_games", "pt"]

    list_filter = ["tenhou_object__is_active"]
    search_fields = [
        "tenhou_object__player__first_name_ru",
        "tenhou_object__player__last_name_ru",
        "tenhou_object__player__first_name_en",
        "tenhou_object__player__last_name_en",
    ]

    def player(self, obj):
        return obj.tenhou_object.player


admin.site.register(TenhouStatistics, TenhouStatisticsAdmin)
admin.site.register(TenhouAggregatedStatistics, TenhouAggregatedStatisticsAdmin)
