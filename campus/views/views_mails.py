# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage

import json
from campus.async_tasks import notify_moderator
from campus.forms import SendMailForm
from campus.models import LdapGroup, Mail, LdapUser


@login_required
def send_email_view(request):
    form = SendMailForm(
        initial={'sender': request.ldap_user.mail}
    )

    if request.method == 'POST':
        form = SendMailForm(
            request.POST,
            initial={'sender': request.ldap_user.mail})
        if form.is_valid():
            m = form.save()

            # Send confirmation mail
            mail = EmailMessage(
                subject="Votre mail a été soumis à la modération",
                body="Bonjour,\n\n" +
                     "Vous trouverez ci-joint une copie du mail qui est actuellement en cours de modération :\n\n" +
                     "--------------------------------------\n" +
                     m.content + "\n\n" +
                     "--------------------------------------\n" +
                     "Cordialement,\n" +
                     "~ le gentil bot ResEl ~\n\n"
                     "Ce mail a été envoyé automatiquement, merci de ne pas y répondre.\n",
                from_email="secretaire@resel.fr",
                to=[m.sender]
            )
            mail.send()

            # Send moderators email
            moderators_emails_addresses = [
                LdapUser.get(pk=mod.split(',')[0].split('uid=')[1]).mail
                for mod in LdapGroup.get(pk='campusmodo').members
            ]

            for mod_email in moderators_emails_addresses:
                notify_moderator(mod_email, m.pk)

            messages.success(request, _('Votre mail sera traité par les modérateurs.'))
            return HttpResponseRedirect(reverse('home'))

    return render(
        request,
        'campus/mails/send_mail.html',
        {'form': form}
    )

@login_required
def moderate_view(request):
    """
    View to moderate emails
    :param request:
    :return:
    """
    if not request.ldap_user.is_campus_moderator():
        messages.error(request, _("Vous n'êtes pas modérateur campus"))
        return HttpResponseRedirect(reverse('campus:home'))

    if request.is_ajax():
        if request.method == 'GET':
            """
            GET call, to get infos of the mail
            """
            mailid = request.GET.get('id')
            m = get_object_or_404(Mail, id=mailid)
            response_data = {
                'sender': m.sender,
                'subject': m.subject,
                'content': m.content,
            }
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )

        """
        Moderating the mail
        """
        mailid = request.POST.get('id')
        instance = get_object_or_404(Mail, id=mailid)
        form = SendMailForm(request.POST, instance=instance)

        if form.is_valid():
            m = form.save()
            m.moderated = True
            m.moderated_by = request.ldap_user.uid
            m.save()

            mail_sympa = EmailMessage(
                subject=m.subject,
                body=m.content,
                from_email=m.sender,
                to=['campus-brest@resel.fr'],
            )
            mail_sympa.send()

            messages.success(request, _("E-mail modéré, n'oubliez pas d'aller faire la double modération sur https://mliste.resel.fr !"))
            return HttpResponse()

    return render(
        request,
        'campus/mails/need_moderation.html',
        {'mails': Mail.objects.all().filter(moderated=False).order_by('-pk')}
    )

@login_required
def rejectView(request, mail):
    if request.is_ajax():
        m = Mail.objects.get(pk=mail)
        explanation = request.POST.get('explanation') or 'aucun motif'

        if not m.moderated:
            # Notify the sender of the rejection
            notify = EmailMessage(
                subject="Votre mail campus a été rejeté",
                body="Bonjour,\n\n" +
                     "Votre mail a été rejeté pour le motif suivant :\n" +
                     explanation + "\n\n" +
                     "Cordialement,\n" +
                     "~ le gentil bot ResEl ~",
                from_email="secretaire@resel.fr",
                reply_to="support@resel.fr",
                to=[m.sender]
            )
            notify.send()

            # Delete the mail
            m.delete()

        return HttpResponse()
