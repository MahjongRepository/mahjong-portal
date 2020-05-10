from django.contrib.postgres.fields import JSONField
from django.db import models

from mahjong_portal.models import BaseModel
from tournament.models import Tournament


class TournamentStatus(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    current_round = models.PositiveSmallIntegerField(null=True, blank=True)
    end_break_time = models.DateTimeField(null=True, blank=True)
    registration_closed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.tournament.name


class TournamentPlayers(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    telegram_username = models.CharField(max_length=32, null=True, blank=True)
    discord_username = models.CharField(max_length=32, null=True, blank=True)
    tenhou_username = models.CharField(max_length=8)

    pantheon_id = models.PositiveIntegerField(null=True, blank=True)
    added_to_pantheon = models.BooleanField(default=False)
    enabled_in_pantheon = models.BooleanField(default=True)

    team_name = models.CharField(max_length=1000, null=True, blank=True)
    team_number = models.PositiveIntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.tenhou_username


class TournamentGame(BaseModel):
    NEW = 0
    STARTED = 1
    FAILED_TO_START = 2
    FINISHED = 3

    STATUSES = [[NEW, "New"], [STARTED, "Started"], [FAILED_TO_START, "Failed to start"], [FINISHED, "Finished"]]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    tournament_round = models.PositiveSmallIntegerField(null=True, blank=True)
    log_id = models.CharField(max_length=32, null=True, blank=True)

    status = models.PositiveSmallIntegerField(choices=STATUSES, default=NEW)

    class Meta:
        ordering = ["-tournament", "-tournament_round", "status"]

    def __unicode__(self):
        return "{}, {}, {}".format(self.id, self.get_status_display(), self.tournament_round)


class TournamentGamePlayer(BaseModel):
    player = models.ForeignKey(TournamentPlayers, on_delete=models.CASCADE)
    game = models.ForeignKey(TournamentGame, on_delete=models.CASCADE, related_name="game_players")
    wind = models.PositiveSmallIntegerField(null=True, blank=True, default=None)

    def __unicode__(self):
        return "{}, {}, {}, {}".format(
            self.player.__unicode__(), self.wind, self.player.pantheon_id, self.player.team_name
        )


class TournamentNotification(BaseModel):
    TELEGRAM = 0
    DISCORD = 1
    DESTINATIONS = [[TELEGRAM, "Telegram"], [DISCORD, "Discord"]]

    GAME_STARTED = "game_started"
    GAME_FAILED = "game_failed"
    GAME_FAILED_NO_MEMBERS = "game_failed_no_members"
    GAME_ENDED = "game_ended"
    GAMES_PREPARED = "games_prepared"
    CONFIRMATION_STARTED = "confirmation_started"
    CONFIRMATION_ENDED = "confirmation_ended"
    ROUND_FINISHED = "round_finished"
    TOURNAMENT_FINISHED = "tournament_finished"

    NOTIFICATION_TYPES = [
        [GAME_STARTED, GAME_STARTED],
        [GAME_FAILED, GAME_FAILED],
        [GAME_FAILED_NO_MEMBERS, GAME_FAILED_NO_MEMBERS],
        [GAME_ENDED, GAME_ENDED],
        [CONFIRMATION_STARTED, CONFIRMATION_STARTED],
        [CONFIRMATION_ENDED, CONFIRMATION_ENDED],
        [GAMES_PREPARED, GAMES_PREPARED],
        [ROUND_FINISHED, ROUND_FINISHED],
        [TOURNAMENT_FINISHED, TOURNAMENT_FINISHED],
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    notification_type = models.CharField(choices=NOTIFICATION_TYPES, max_length=300)
    message_kwargs = JSONField(blank=True)

    destination = models.PositiveSmallIntegerField(choices=DESTINATIONS)
    is_processed = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_on"]

    def __unicode__(self):
        return f"{self.tournament.name} - {self.get_notification_type_display()}"
