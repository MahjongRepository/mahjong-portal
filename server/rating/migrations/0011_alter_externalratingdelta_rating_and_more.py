# Generated by Django 4.2.16 on 2024-12-06 19:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("rating", "0010_externalratingdelta_base_rank"),
    ]

    operations = [
        migrations.AlterField(
            model_name="externalratingdelta",
            name="rating",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rating.externalrating"),
        ),
        migrations.AlterField(
            model_name="externalratingtournament",
            name="rating",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rating.externalrating"),
        ),
    ]
