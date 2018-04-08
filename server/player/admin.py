from django import forms
from django.contrib import admin

from player.models import Player, TenhouNickname


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


admin.site.register(Player, PlayerAdmin)
