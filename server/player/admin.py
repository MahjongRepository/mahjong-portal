from django import forms
from django.contrib import admin

from player.models import Player, TenhouNickname, TenhouStatistics


class PlayerForm(forms.ModelForm):

    class Meta:
        model = Player
        exclude = ['first_name', 'last_name']


class TenhouNicknameInline(admin.TabularInline):
    model = TenhouNickname
    extra = 1


class PlayerAdmin(admin.ModelAdmin):
    form = PlayerForm
    inlines = [
        TenhouNicknameInline
    ]

    prepopulated_fields = {'slug': ['last_name_en', 'first_name_en']}

    list_display = ['last_name', 'first_name', 'city', 'pantheon_id']
    list_filter = ['is_hide']
    search_fields = ['first_name_ru', 'first_name_en', 'last_name_ru', 'last_name_en', 'ema_id']

    def get_queryset(self, request):
        return Player.all_objects.all()


class TenhouStatisticsAdmin(admin.ModelAdmin):
    list_display = ['player', 'tenhou_object', 'lobby', 'rank', 'played_games', 'average_place', 'last_played_date']
    list_filter = ['lobby']

    def player(self, obj):
        return obj.tenhou_object.player.full_name

    def rank(self, obj):
        return obj.tenhou_object.get_rank_display()
    rank.short_description = 'Rank'
    rank.admin_order_field = 'tenhou_object__rank'

    def last_played_date(self, obj):
        return obj.tenhou_object.last_played_date


admin.site.register(Player, PlayerAdmin)
admin.site.register(TenhouStatistics, TenhouStatisticsAdmin)
