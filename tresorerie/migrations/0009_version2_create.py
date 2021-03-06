# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-22 21:09
from __future__ import unicode_literals

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tresorerie', '0001_version1'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeCustomer',
            fields=[
                ('ldap_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('stripe_id', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='autorisation',
            field=models.CharField(choices=[('FIG', 'FIG'), ('FIP', 'FIP'), ('ALL', 'ALL')], default='ALL', help_text='Définit qui est éligible à ce produit', max_length=3, verbose_name="Authorisation d'achat"),
        ),
        migrations.AddField(
            model_name='transaction',
            name='stripe_id',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AlterField(
            model_name='check',
            name='date_emission',
            field=models.DateField(auto_now_add=True, verbose_name="date d'émission"),
        ),
        migrations.AlterField(
            model_name='product',
            name='prix',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='produit',
            field=models.ManyToManyField(to='tresorerie.Product'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='admin',
            field=models.CharField(max_length=100),
        ),
    ]
