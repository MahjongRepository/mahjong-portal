# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-06-16 12:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0016_auto_20180406_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournamentapplication',
            name='number_of_games',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Number of hanchans'),
            preserve_default=False,
        ),
    ]