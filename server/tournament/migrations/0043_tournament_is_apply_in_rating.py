# Generated by Django 4.2.9 on 2024-02-29 20:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tournament", "0042_alter_msonlinetournamentregistration_contact"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournament",
            name="is_apply_in_rating",
            field=models.BooleanField(default=False),
        ),
    ]
