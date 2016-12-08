from django.db import models

class Mail(models.Model):
    class Meta:
        permissions = (
            ('can_moderate', 'Can moderate mail'),
        )

    sender = models.CharField(
        max_length=15,
        verbose_name='Envoyeur',
        editable=False,
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

class MailModerator(models.Model):
    class Meta:
        verbose_name = 'modérateur de mails'
        verbose_name_plural = 'modérateurs de mails'

    uid = models.CharField(
        max_length=15,
        verbose_name='nom d\'utilisateur',
    )