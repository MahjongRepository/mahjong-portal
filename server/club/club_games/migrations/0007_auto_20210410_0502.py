# -*- coding: utf-8 -*-

# Generated by Django 3.2 on 2021-04-10 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club_games', '0006_auto_20180811_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clubrating',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='clubsession',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='clubsessionresult',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='clubsessionsyncdata',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
