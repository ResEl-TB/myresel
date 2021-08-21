from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import django_rq
from gestion_personnes.models import LdapUser
from gestion_personnes.models import LdapGroup
from campus import async_tasks

class Mail(models.Model):
    sender = models.CharField(
        max_length=127,
        verbose_name='Envoyeur',
    )

    subject = models.CharField(
        max_length=127,
        verbose_name='Sujet',
    )

    content = models.TextField(
        verbose_name='Contenu',
    )

    moderated = models.BooleanField(
        verbose_name='Modéré',
        default=False,
        editable=False,
    )

    moderated_by = models.CharField(
        max_length=127,
        verbose_name='Modéré par',
        editable=False,
    )

    date = models.DateTimeField(
        verbose_name='Date de réception',
        auto_now_add=True,
        editable=False,
    )

    def __str__(self):
        return self.subject
