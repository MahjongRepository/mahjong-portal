# -*- coding: utf-8 -*-

# Generated by Django 4.2.2 on 2024-01-06 10:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("online", "0021_alter_tournamentplayers_ms_username_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournamentplayers",
            name="ms_account_id",
            field=models.IntegerField(null=True),
        ),
    ]
