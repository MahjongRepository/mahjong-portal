from django.contrib import admin

from club.club_games.models import ClubSessionResult


class ClubSessionResultAdmin(admin.ModelAdmin):
    list_display = ['player', 'player_string', 'club']
    search_fields = ['player_string']
    ordering = ['-club_session__club__name', 'player_string',]

    def club(self, obj):
        return obj.club_session.club.name

    def get_queryset(self, request):
        qs = super(ClubSessionResultAdmin, self).get_queryset(request)
        return qs.filter(player=None)


admin.site.register(ClubSessionResult, ClubSessionResultAdmin)
