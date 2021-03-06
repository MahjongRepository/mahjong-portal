# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-06-30 13:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenhou', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectedYakuman',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField()),
                ('log_id', models.CharField(max_length=44)),
                ('yakuman_list', models.CharField(max_length=60)),
            ],
            options={
                'db_table': 'portal_collected_yakuman',
            },
        ),
        migrations.CreateModel(
            name='TenhouGameLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lobby', models.PositiveSmallIntegerField(choices=[[0, 'Kyu lobby'], [1, 'Dan lobby'], [2, 'Upperdan lobby'], [3, 'Phoenix lobby']])),
                ('place', models.PositiveSmallIntegerField()),
                ('game_length', models.PositiveSmallIntegerField()),
                ('delta', models.SmallIntegerField(default=0)),
                ('game_date', models.DateTimeField()),
                ('game_rules', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'portal_tenhou_game_log',
                'ordering': ['game_date'],
            },
        ),
        migrations.CreateModel(
            name='TenhouStatistics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lobby', models.PositiveSmallIntegerField(choices=[[0, 'Kyu lobby'], [1, 'Dan lobby'], [2, 'Upperdan lobby'], [3, 'Phoenix lobby']])),
                ('stat_type', models.PositiveSmallIntegerField(choices=[[0, 'All time'], [1, 'Current month']], default=0)),
                ('played_games', models.PositiveIntegerField(default=0)),
                ('average_place', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('first_place', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('second_place', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('third_place', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('fourth_place', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
            options={
                'db_table': 'portal_tenhou_statistics',
                'ordering': ['lobby'],
            },
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='latest_twenty_places',
        ),
        migrations.AddField(
            model_name='tenhoustatistics',
            name='tenhou_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='tenhou.TenhouNickname'),
        ),
        migrations.AddField(
            model_name='tenhougamelog',
            name='tenhou_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='game_logs', to='tenhou.TenhouNickname'),
        ),
        migrations.AddField(
            model_name='collectedyakuman',
            name='tenhou_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='yakumans', to='tenhou.TenhouNickname'),
        ),
        migrations.AlterUniqueTogether(
            name='tenhougamelog',
            unique_together=set([('tenhou_object', 'game_date')]),
        ),
    ]
