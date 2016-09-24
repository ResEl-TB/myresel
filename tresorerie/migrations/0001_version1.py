# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-24 08:31
from __future__ import unicode_literals

import datetime

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):


    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('utilisateur', models.CharField(blank=True, max_length=50)),
                ('moyen', models.CharField(choices=[('L', 'Liquide'), ('C', 'Chèque'), ('CB', 'Carte bancaire')], max_length=2, verbose_name='moyen de paiement')),
                ('date', models.DateField(auto_now_add=True)),
                ('total', models.FloatField(default=0)),
                ('commentaire', models.TextField(blank=True, null=True)),
                ('admin', models.CharField(default='resel.fr', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='MonthlyPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=50)),
                ('months_to_pay', models.IntegerField()),
                ('months_paid', models.IntegerField(default=0)),
                ('customer', models.CharField(max_length=50)),
                ('last_paid', models.DateField(default=django.utils.timezone.now)),
                ('amount_to_pay', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'banque',
            },
        ),
        migrations.CreateModel(
            name='Check',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.IntegerField(verbose_name='numéro')),
                ('nom', models.CharField(max_length=100)),
                ('date_emission', models.DateField(default=datetime.date(2016, 9, 17), verbose_name="date d'émission")),
                ('montant', models.FloatField()),
                ('encaisse', models.BooleanField(default=False, editable=False, verbose_name='encaissé')),
                ('date_encaissement', models.DateField(blank=True, null=True)),
                ('banque', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tresorerie.Bank')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tresorerie.Transaction')),
            ],
            options={
                'verbose_name': 'chèque',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
                ('prix', models.FloatField()),
                ('type_produit', models.CharField(choices=[('A', 'Adhésion'), ('M', 'Matériel'), ('F', "Frais d'accès")], max_length=1, verbose_name='type de produit')),
                ('duree', models.IntegerField(blank=True, help_text="durée en mois des frais d'accès (si type = frais d'accès, laisser vide sinon)", validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(12)], verbose_name='durée')),
            ],
            options={
                'verbose_name': 'produit',
            },
        ),
        migrations.AlterModelOptions(
            name='monthlypayment',
            options={'verbose_name': 'paiement mensuel', 'verbose_name_plural': 'paiements mensuels'},
        ),
        migrations.AddField(
            model_name='transaction',
            name='produit',
            field=models.ManyToManyField(null=True, to='tresorerie.Product'),
        ),
    ]