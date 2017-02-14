# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-02-14 12:55
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Mail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender', models.CharField(max_length=15, verbose_name='Envoyeur')),
                ('subject', models.CharField(max_length=50, verbose_name='Sujet')),
                ('content', models.TextField(verbose_name='Contenu')),
                ('moderated', models.BooleanField(default=False, editable=False, verbose_name='Modéré')),
                ('moderated_by', models.CharField(editable=False, max_length=15, verbose_name='Modéré par')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='Date de réception')),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(choices=[('F', 'Foyer'), ('S', 'École'), ('O', 'Extérieur'), ('C', 'Campus')], help_text='emplacement de la salle', max_length=1, verbose_name='Emplacement')),
                ('name', models.CharField(help_text='nom de la salle', max_length=20, verbose_name='Nom de la salle')),
                ('mailing_list', models.EmailField(blank=True, help_text='mailing-list à contacter pour réserver cette salle', max_length=254)),
                ('private', models.BooleanField(default=False, help_text='indique si la salle est privée ou non', verbose_name='Salle privée / club')),
                ('clubs', models.TextField(blank=True, help_text='indique à quel(s) club(s) appartient la salle, un par ligne', verbose_name='club(s)')),
            ],
            options={
                'verbose_name': 'salle',
            },
        ),
        migrations.CreateModel(
            name='RoomAdmin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rooms', models.ManyToManyField(to='campus.Room', verbose_name='Salles accessibles')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'administrateur des salles',
                'verbose_name_plural': 'administrateurs des salles',
            },
        ),
        migrations.CreateModel(
            name='RoomBooking',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(help_text="description de l'évènement")),
                ('start_time', models.DateTimeField(db_index=True, help_text="début de l'évènement", verbose_name="Début de l'evènement")),
                ('end_time', models.DateTimeField(db_index=True, help_text="fin de l'évènement", verbose_name="Fin de l'évènement")),
                ('user', models.CharField(help_text='utilisateur ayant fait la demande de réservation', max_length=50, verbose_name='Utilisateur')),
                ('booking_type', models.CharField(choices=[('party', 'Soirée'), ('club', 'Activité de club'), ('meeting', 'Réunion'), ('training', 'Formation'), ('event', 'Évènement'), ('sport', 'Sport'), ('arts', 'Art et culture'), ('trip', 'Sortie'), ('other', 'Autre'), ('hidden', 'Ne pas afficher sur le calendrier')], help_text="type d'évènement", max_length=50, verbose_name='Type')),
                ('displayable', models.BooleanField(default=True, help_text='affiche ou non cet évènement sur le calendrier', verbose_name='Affichable')),
                ('recurring_rule', models.CharField(choices=[('NONE', 'Pas de récurrence'), ('DAILY', 'Quotidient'), ('WEEKLY', 'Hebdomadaire')], default='NONE', help_text='Type de recurrence', max_length=10)),
                ('end_recurring_period', models.DateTimeField(blank=True, db_index=True, help_text='Cette date est ignorée pour les événements uniques.', null=True, verbose_name='fin de la récurrence')),
                ('room', models.ManyToManyField(db_index=True, help_text="indique dans quelle salle se déroule l'évènement", to='campus.Room', verbose_name='Salle(s)')),
            ],
            options={
                'verbose_name': 'réservation',
            },
        ),
    ]
