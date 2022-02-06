from django.db import models


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
    pantheon_id = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeagueSession(models.Model):
    PLANNED = 0
    FINISHED = 1
    STATUSES = [
        [PLANNED, "Planned"],
        [FINISHED, "Finished"],
    ]
    league = models.ForeignKey(League, on_delete=models.PROTECT, related_name="sessions")
    number = models.PositiveSmallIntegerField()
    status = models.PositiveSmallIntegerField(choices=STATUSES, default=PLANNED)
    start_time = models.DateTimeField()

    class Meta:
        ordering = ["number"]


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


class LeagueGamePlayer(models.Model):
    position = models.PositiveSmallIntegerField()
    game = models.ForeignKey(LeagueGame, on_delete=models.PROTECT, related_name="players")
    team = models.ForeignKey(LeagueTeam, on_delete=models.PROTECT, related_name="games")
    player_pantheon_id = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
