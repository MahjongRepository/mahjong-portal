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
        return f"{self.name} (#{self.league_id})"


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
        ordering = ["-id"]

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
