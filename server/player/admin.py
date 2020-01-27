from django import forms
from django.contrib import admin

from player.models import Player, PlayerERMC, PlayerTitle, PlayerWRC
from player.tenhou.models import TenhouNickname


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
    list_filter = ['is_hide', 'country']
    search_fields = ['first_name_ru', 'first_name_en', 'last_name_ru', 'last_name_en', 'ema_id']

    def get_queryset(self, request):
        return Player.objects.all()


class PlayerTitleForm(forms.ModelForm):

    class Meta:
        model = Player
        exclude = ['text']


class PlayerTitleAdmin(admin.ModelAdmin):
    form = PlayerTitleForm

    search_fields = ['player__last_name', 'player__first_name']
    list_display = ['player', 'text', 'background_color', 'text_color']
    raw_id_fields = ['player']


class PlayerERMCAdmin(admin.ModelAdmin):
    search_fields = ['player__first_name_ru', 'player__first_name_en', 'player__last_name_ru', 'player__last_name_en']
    list_display = ['player', 'state', 'federation_member']
    list_filter = ['state']
    raw_id_fields = ['player']



admin.site.register(Player, PlayerAdmin)
admin.site.register(PlayerERMC, PlayerERMCAdmin)
admin.site.register(PlayerWRC, PlayerERMCAdmin)
admin.site.register(PlayerTitle, PlayerTitleAdmin)
