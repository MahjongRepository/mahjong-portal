# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-02-19 00:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenhou', '0004_tenhougamelog_next_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenhounickname',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]