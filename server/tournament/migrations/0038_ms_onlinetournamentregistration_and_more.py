# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tournament", "0037_alter_onlinetournamentregistration_tenhou_nickname"),
    ]

    operations = [
        migrations.CreateModel(
            name='MsOnlineTournamentRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('is_approved', models.BooleanField(default=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='First name')),
                ('last_name', models.CharField(null=True, blank=True, max_length=255, verbose_name='Last name')),
                ('city', models.CharField(max_length=255, verbose_name='City')),
                ('ms_nickname', models.CharField(max_length=255, verbose_name='Majsoul nickname')),
                ('ms_friend_id', models.PositiveIntegerField()),
                ('ms_account_id', models.PositiveIntegerField(null=True)),
                ('contact', models.CharField(help_text='It will be visible only to the administrator', max_length=255, verbose_name='Your contact (email, phone, etc.)')),
                ('city_object', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='settings.City')),
                ('player', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ms_online_tournament_registrations', to='player.Player')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('allow_to_save_data', models.BooleanField(default=False, verbose_name='I allow to store my personal data')),
                ('notes', models.TextField(blank=True, default='', null=True, verbose_name='Team name'))
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='msonlinetournamentregistration',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ms_online_tournament_registrations', to='tournament.Tournament'),
        ),
        migrations.AlterUniqueTogether(
            name='msonlinetournamentregistration',
            unique_together=set([('ms_nickname', 'ms_friend_id', 'tournament')]),
        ),
        migrations.AlterField(
            model_name='msonlinetournamentregistration',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
