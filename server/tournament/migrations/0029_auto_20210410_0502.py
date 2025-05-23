# -*- coding: utf-8 -*-

# Generated by Django 3.2 on 2021-04-10 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0028_auto_20210211_0456'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onlinetournamentregistration',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='onlinetournamentregistration',
            name='notes',
            field=models.TextField(blank=True, default='', null=True, verbose_name='Team name'),
        ),
        migrations.AlterField(
            model_name='tournament',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tournamentapplication',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tournamentregistration',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tournamentresult',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
