# -*- coding: utf-8 -*-

# Generated by Django 3.2.18 on 2023-03-15 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0031_alter_tournamentregistration_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onlinetournamentregistration',
            name='notes',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Additional info'),
        ),
    ]
