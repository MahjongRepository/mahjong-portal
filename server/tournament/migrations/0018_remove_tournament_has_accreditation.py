# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-06-16 13:12
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0017_tournamentapplication_number_of_games'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tournament',
            name='has_accreditation',
        ),
    ]