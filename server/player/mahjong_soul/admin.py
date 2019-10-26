from django.contrib import admin

from player.mahjong_soul.models import MSAccount, MSAccountStatistic, MSPointsHistory


class MSAccountAdmin(admin.ModelAdmin):
    list_display = ['account_id', 'account_name', 'player']


class MSAccountStatisticAdmin(admin.ModelAdmin):
    list_display = ['account', 'game_type', 'rank', 'points']
    list_filter = ['game_type']


class MSPointsHistoryAdmin(admin.ModelAdmin):
    list_display = ['stat_object', 'rank', 'points', 'created_on']
    list_filter = ['stat_object__account']


admin.site.register(MSAccount, MSAccountAdmin)
admin.site.register(MSAccountStatistic, MSAccountStatisticAdmin)
admin.site.register(MSPointsHistory, MSPointsHistoryAdmin)
