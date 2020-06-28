from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from online.models import (
    TournamentGame,
    TournamentGamePlayer,
    TournamentNotification,
    TournamentPlayers,
    TournamentStatus,
)
from player.models import Player
from tournament.models import OnlineTournamentRegistration, Tournament


class TournamentGameForm(forms.ModelForm):
    class Meta:
        model = TournamentGame
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tournament"].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE)


class TournamentPlayersForm(forms.ModelForm):
    class Meta:
        model = TournamentPlayers
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tournament"].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE).order_by(
            "-start_date"
        )


class TournamentStatusAdmin(admin.ModelAdmin):
    list_display = ["tournament", "current_round", "end_break_time"]


class TournamentPlayersAdmin(admin.ModelAdmin):
    form = TournamentPlayersForm
    list_display = [
        "tournament",
        "player",
        "username",
        "tenhou_username",
        "pantheon_id",
        "team_name",
        "team_number",
        "add_to_pantheon_action",
        "disable_in_pantheon_sortition",
    ]

    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter], "added_to_pantheon", "enabled_in_pantheon"]

    def player(self, obj):
        if obj.pantheon_id:
            try:
                return Player.objects.get(pantheon_id=obj.pantheon_id)
            except Player.DoesNotExist:
                pass

        try:
            registration = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
            if registration and registration.player:
                return registration.player
        except (OnlineTournamentRegistration.DoesNotExist, Player.DoesNotExist):
            pass

        result = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
        if result:
            return "[{} {}]".format(result.last_name, result.first_name)

        return None

    def add_to_pantheon_action(self, obj):
        if not obj.pantheon_id:
            return mark_safe('<span style="background-color: red; padding: 5px;">MISSED PANTHEON ID</span>')

        if not obj.added_to_pantheon:
            url = reverse("add_user_to_the_pantheon", kwargs={"record_id": obj.id})
            return mark_safe('<a href="{}" class="button">Add to pantheon</a>'.format(url))

        return "Added"

    def disable_in_pantheon_sortition(self, obj):
        if obj.enabled_in_pantheon:
            url = reverse("disable_user_in_pantheon", kwargs={"record_id": obj.id})
            return mark_safe('<a href="{}" class="button">Disable</a>'.format(url))

        return mark_safe('<span style="background-color: red; padding: 5px;">Disabled</span>')

    def username(self, obj):
        if obj.telegram_username:
            return f"{obj.telegram_username} (tg)"

        if obj.discord_username:
            return f"{obj.discord_username} (ds)"


class TournamentGamePlayerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get("instance")
        if instance:
            self.fields["player"].queryset = TournamentPlayers.objects.filter(
                tournament=instance.player.tournament
            ).order_by("-id")

    class Meta:
        model = TournamentGamePlayer
        exclude = []


class TournamentGamePlayerInline(admin.TabularInline):
    form = TournamentGamePlayerForm
    model = TournamentGamePlayer
    can_delete = False
    extra = 0
    readonly_fields = ["wind"]


class TournamentGameAdmin(admin.ModelAdmin):
    form = TournamentGameForm
    inlines = [TournamentGamePlayerInline]
    list_display = ["tournament", "tournament_round", "status", "log_id", "created_on", "updated_on"]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter], "status", "tournament_round"]


class TournamentNotificationAdmin(admin.ModelAdmin):
    list_display = [
        "tournament",
        "notification_type",
        "destination",
        "is_processed",
        "message_kwargs",
        "created_on",
        "updated_on",
    ]
    list_filter = [["tournament", admin.RelatedOnlyFieldListFilter], "is_processed", "failed", "destination"]


admin.site.register(TournamentStatus, TournamentStatusAdmin)
admin.site.register(TournamentPlayers, TournamentPlayersAdmin)
admin.site.register(TournamentGame, TournamentGameAdmin)
admin.site.register(TournamentNotification, TournamentNotificationAdmin)
