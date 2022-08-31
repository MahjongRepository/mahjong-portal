from django.core.cache import cache
from django.db import models

from account.models import User


class League(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    slug = models.SlugField()
    start_date = models.DateField()
    end_date = models.DateField()
    games = models.SmallIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def players(self):
        return LeaguePlayer.objects.filter(team__league=self)


class LeagueTeam(models.Model):
    name = models.CharField(max_length=255)
    number = models.PositiveSmallIntegerField(null=True, blank=True)
    league = models.ForeignKey(League, on_delete=models.PROTECT, related_name="teams")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return self.name


class LeaguePlayer(models.Model):
    name = models.CharField(max_length=255)
    tenhou_nickname = models.CharField(max_length=8, null=True, blank=True)
    team = models.ForeignKey(LeagueTeam, on_delete=models.PROTECT, related_name="players")
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)
    is_captain = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_captain", "name"]

    def __str__(self):
        return self.name


class LeagueSession(models.Model):
    NEW = 0
    PLANNED = 1
    FINISHED = 2
    STATUSES = [
        [NEW, "New"],
        [PLANNED, "Planned"],
        [FINISHED, "Finished"],
    ]
    league = models.ForeignKey(League, on_delete=models.PROTECT, related_name="sessions")
    number = models.PositiveSmallIntegerField()
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=PLANNED)
    start_time = models.DateTimeField()

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Session: {self.number}"

    def missing_teams_for_session(self):
        all_teams = cache.get("all_league_teams")
        if not all_teams:
            all_teams = LeagueTeam.objects.all()
            cache.set("all_league_teams", all_teams, timeout=60 * 60 * 24)

        playing_team_ids = []
        for game in self.games.all():
            for game_slot in game.slots.all():
                if game_slot.team_id not in playing_team_ids:
                    playing_team_ids.append(game_slot.team_id)

        return [x for x in all_teams if x.id not in playing_team_ids]

    def all_games(self):
        if hasattr(self, "custom_games"):
            return self.custom_games
        return self.games.all()


class LeagueGame(models.Model):
    NEW = 0
    STARTED = 1
    FINISHED = 2
    STATUSES = [
        [NEW, "New"],
        [STARTED, "Started"],
        [FINISHED, "Finished"],
    ]
    session = models.ForeignKey(LeagueSession, on_delete=models.PROTECT, related_name="games")
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=NEW)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"Game: {self.id}"

    def is_new(self):
        return self.status == LeagueGame.NEW


class LeagueGameSlot(models.Model):
    position = models.PositiveSmallIntegerField()
    game = models.ForeignKey(LeagueGame, on_delete=models.PROTECT, related_name="slots")
    team = models.ForeignKey(LeagueTeam, on_delete=models.PROTECT, related_name="games")
    assigned_player = models.ForeignKey(
        LeaguePlayer, on_delete=models.PROTECT, related_name="games", null=True, blank=True
    )

    class Meta:
        ordering = ["position"]

    @property
    def assigned_player_short_name(self):
        return self.assigned_player.name.split(" ")[0]
