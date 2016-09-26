# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-26 08:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tresorerie', '0011_version2_finalize'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='date',
            new_name='date_creation',
        ),
        migrations.AddField(
            model_name='transaction',
            name='date_paiement',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='facture',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='Chemin de la facture en pdf'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='statut',
            field=models.CharField(choices=[('A', 'En attente'), ('N', 'Non payée'), ('P', 'Payée'), ('E', 'Erreur')], default='N', max_length=3, verbose_name='Statut de la transaction'),
        ),
    ]
