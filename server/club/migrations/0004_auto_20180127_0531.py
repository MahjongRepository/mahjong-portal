# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-27 05:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0003_club_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='description_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='club',
            name='description_ru',
            field=models.TextField(blank=True, null=True),
        ),
    ]
