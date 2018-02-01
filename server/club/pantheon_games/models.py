from django.db import models


class PantheonPlayer(models.Model):
    ident = models.CharField(max_length=255)
    alias = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'player'


class PantheonEvent(models.Model):
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    timezone = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'event'


class PantheonSession(models.Model):
    FINISHED = 'finished'

    event = models.ForeignKey(PantheonEvent)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=255)
    representational_hash = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'session'


class PantheonSessionResult(models.Model):
    event = models.ForeignKey(PantheonEvent)
    session = models.ForeignKey(PantheonSession, related_name='results')
    player = models.ForeignKey(PantheonPlayer)
    score = models.PositiveIntegerField()
    place = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'session_results'


class PantheonSessionPlayer(models.Model):
    session = models.ForeignKey(PantheonSession, related_name='players')
    player = models.ForeignKey(PantheonPlayer)
    # django wanted on primary key
    # but pantheon table didn't have it
    order = models.PositiveSmallIntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'session_player'


class PantheonRound(models.Model):
    RON = 'ron'
    MULTI_RON = 'multiron'

    session = models.ForeignKey(PantheonSession, related_name='rounds')
    winner = models.ForeignKey(PantheonPlayer, related_name='win_rounds')
    loser = models.ForeignKey(PantheonPlayer, related_name='lose_rounds')
    event = models.ForeignKey(PantheonEvent)
    dora = models.PositiveIntegerField()
    multi_ron = models.PositiveIntegerField()
    round = models.PositiveIntegerField()
    open_hand = models.PositiveIntegerField()
    outcome = models.CharField(max_length=255)
    yaku = models.CharField(max_length=255)
    riichi = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'round'
