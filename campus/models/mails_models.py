from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import django_rq
from gestion_personnes.models import LdapUser
from gestion_personnes.models import LdapGroup
from campus import async_tasks

class Mail(models.Model):
    sender = models.CharField(
        max_length=15,
        verbose_name='Envoyeur',
    )

    subject = models.CharField(
        max_length=50,
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
        max_length=15,
        verbose_name='Modéré par',
        editable=False,
    )

    date = models.DateTimeField(
        verbose_name='Date de réception',
        auto_now_add=True,
        editable=False,
    )

@receiver(post_save, sender=Mail, dispatch_uid='notify_campus_moderators')
def notify_mods(sender, instance, created, **kwargs):
    """
    Send an email to campus moderators when the model is created
    """
    if created:
        for member in LdapGroup.get(pk='campusmodo').members:
            moderator = LdapUser.get(pk=member.split(',')[0].split('uid=')[1])
            queue = django_rq.get_queue()
            queue.enqueue_call(
                async_tasks.notify_moderator,
                args=(moderator.mail, instance.pk),
            )