# Generated by Django 2.2.6 on 2020-02-22 08:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tenhou', '0006_auto_20190328_0949'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tenhounickname',
            options={'ordering': ['-username_created_at']},
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='average_place',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='end_pt',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='four_games_rate',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='month_average_place',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='month_played_games',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='played_games',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='pt',
        ),
        migrations.RemoveField(
            model_name='tenhounickname',
            name='rank',
        ),
    ]