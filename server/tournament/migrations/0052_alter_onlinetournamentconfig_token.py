# Generated by Django 5.1.6 on 2025-03-02 21:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tournament", "0051_alter_tournament_is_command"),
    ]

    operations = [
        migrations.AlterField(
            model_name="onlinetournamentconfig",
            name="token",
            field=models.CharField(max_length=2048, unique=True),
        ),
    ]
