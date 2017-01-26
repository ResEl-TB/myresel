# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-12-09 14:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campus', '0001_working_room_booking'),
    ]

    operations = [
        migrations.AddField(
            model_name='roomadmin',
            name='rooms',
            field=models.ManyToManyField(to='campus.Room', verbose_name='Salles accessibles'),
        ),
    ]
