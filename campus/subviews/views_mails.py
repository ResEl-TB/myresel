from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage

from campus.forms import SendMailForm
from campus.models import LdapGroup, Mail

@login_required
def sendMailView(request):
    form = SendMailForm(
        initial={'sender': request.ldap_user.mail or 'test@toi.fr'}
    )

    if request.method == 'POST':
        form = SendMailForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Votre mail sera traité par les modérateurs.'))
            return HttpResponseRedirect(reverse('home'))

    return render(
        request, 
        'campus/mails/send_mail.html',
        {'form': form}
    )

@login_required
def moderateView(request, mail=None):
    if not LdapGroup.get(pk='campusmodo').is_member(request.ldap_user.uid):
        messages.error(request, _("Vous n'êtes pas modérateur campus"))
        return HttpResponseRedirect(reverse('campus:salles:calendar'))

    if mail:
        """
        Specific mail moderation
        """

        instance = get_object_or_404(Mail, id=mail)
        form = SendMailForm(request.POST, instance=instance) if request.method == 'POST' else SendMailForm(instance=instance)

        if request.method == 'POST' and form.is_valid():
            m = form.save()
            m.moderated = True
            m.moderated_by = request.ldap_user.uid
            m.save()

            #TODO : send mail to Sympa
            mail_sympa = EmailMessage(
                subject=m.subject,
                body=m.content,
                from_email=m.sender,
                to=['campus@resel.fr'],
            )
            mail_sympa.send()

            messages.success(request, _("Mail modéré !"))
            return HttpResponseRedirect(reverse('campus:mails:moderate-list'))

        return render(
            request,
            'campus/mails/moderate.html',
            {'form': form}
        )

    else:
        """
        List all the mails that need to be moderated
        """

        return render(
            request,
            'campus/mails/need_moderation.html',
            {'mails': Mail.objects.all().filter(moderated=False).order_by('-pk')}
        )