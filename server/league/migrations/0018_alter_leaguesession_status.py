# Generated by Django 3.2.12 on 2022-02-14 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0017_alter_leagueplayer_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaguesession',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[[0, 'New'], [1, 'Planned'], [2, 'Finished']], default=1),
        ),
    ]