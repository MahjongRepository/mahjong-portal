# Generated by Django 4.2.2 on 2023-09-10 06:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("player", "0012_auto_20210410_0502"),
    ]

    operations = [
        migrations.AddField(
            model_name="playertitle",
            name="url",
            field=models.URLField(blank=True, null=True),
        ),
    ]