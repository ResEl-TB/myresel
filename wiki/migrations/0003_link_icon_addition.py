# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-03-20 10:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_auto_20160809_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='icon',
            field=models.ImageField(blank=True, default='static/images/icons/placeholder.png', upload_to='image/service_icons'),
        ),
        migrations.AddField(
            model_name='link',
            name='icon',
            field=models.ImageField(blank=True, default='static/images/icons/placeholder.png', upload_to='image/service_icons'),
        ),
    ]
