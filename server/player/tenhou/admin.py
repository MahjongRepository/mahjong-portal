from django.contrib import admin

from player.tenhou.models import TenhouStatistics


class TenhouStatisticsAdmin(admin.ModelAdmin):
    list_display = ['player', 'player_city', 'tenhou_object', 'rank', 'lobby', 'played_games', 'average_place',
                    'last_played_date']
    list_filter = ['lobby', 'stat_type']

    def player(self, obj):
        return obj.tenhou_object.player.full_name

    def player_city(self, obj):
        return obj.tenhou_object.player.city

    def rank(self, obj):
        return obj.tenhou_object.get_rank()
    rank.short_description = 'Rank'
    rank.admin_order_field = 'tenhou_object__rank'

    def last_played_date(self, obj):
        return obj.tenhou_object.last_played_date


admin.site.register(TenhouStatistics, TenhouStatisticsAdmin)
