from devices.models import LdapDevice
from gestion_personnes.models import LdapUser


def resel_context(request):
    """
    This context processor objective is to get information about the machine
    network status.
    :param request:
    :return: dict : a context with the machine ip, if the ip belongs to the
    resel and the machine status
    """

    context = dict(request.network_data)

    context['need_to_pay'] = False
    context['has_paid_cotiz'] = None
    if request.user.is_authenticated():
        user = LdapUser.get(pk=request.user.username)
        context['need_to_pay'] = user.need_to_pay()
        context['ldapuser'] = user
        context['has_paid_cotiz'] = user.need_to_pay()
    elif request.network_data['zone'] != "Internet":
        try:
            # FIXME: here 2 requests to the Ldap each time...
            device = LdapDevice.get(request.network_data['ip'])
            owner_short_uid = device.owner.split(",")[0][4:]
            user = LdapUser.get(uid=owner_short_uid)
            context['has_paid_cotiz'] = user.need_to_pay()
        except:
            context['has_paid_cotiz'] = 'success'

    return context
