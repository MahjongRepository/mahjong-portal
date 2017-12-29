from django import forms
from django.contrib import admin

from player.models import Player


class PlayerForm(forms.ModelForm):

    class Meta:
        model = Player
        exclude = ['first_name', 'last_name']


class PlayerAdmin(admin.ModelAdmin):
    form = PlayerForm

    prepopulated_fields = {'slug': ['last_name_en', 'first_name_en']}

    list_display = ['last_name', 'first_name', 'city']
    list_filter = ['is_hide']
    search_fields = ['first_name_ru', 'first_name_en', 'last_name_ru', 'last_name_en']

    def get_queryset(self, request):
        return Player.all_objects.all()


admin.site.register(Player, PlayerAdmin)
