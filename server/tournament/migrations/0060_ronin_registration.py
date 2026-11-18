from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tournament", "0059_tournamentresult_player_pantheon_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="onlinetournamentregistration",
            name="ronin_id",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Ronin ID"),
        ),
        migrations.AddField(
            model_name="tournament",
            name="is_ronin_tournament",
            field=models.BooleanField(default=False),
        ),
    ]
