# -*- coding: utf-8 -*-

# Generated by Django 3.2 on 2021-04-10 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenhou', '0007_auto_20200222_0840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collectedyakuman',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tenhouaggregatedstatistics',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tenhougamelog',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tenhounickname',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tenhoustatistics',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
