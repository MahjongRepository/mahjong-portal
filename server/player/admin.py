from django.contrib import admin

from player.models import Player


class PlayerAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'city']
    list_filter = ['is_hide']
    search_fields = ['first_name_ru', 'first_name_en', 'last_name_ru', 'last_name_en']

    def get_queryset(self, request):
        return Player.all_objects.all()


admin.site.register(Player, PlayerAdmin)
