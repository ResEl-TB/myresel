from devices.models import LdapDevice
from gestion_personnes.models import LdapUser
from pages.views import StatusPageXhr

def get_network_status():
    services = StatusPageXhr.get_services()
    services_status = StatusPageXhr.load_services_status(services)
    return (services_status['global_status'],
            services_status['global_status_text'])

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
    context['has_paid_cotiz'] = 'success'
    context['i_network_status'], context['i_network_status_text'] = get_network_status()
    if request.user.is_authenticated():
        user = LdapUser.get(pk=request.user.username)
        context['need_to_pay'] = user.need_to_pay()
        context['ldapuser'] = user
        context['has_paid_cotiz'] = user.need_to_pay()
    ## FIXME: The code down here is bullshit so if somebody want to fix it go on
    ## But not on my watch
    # elif request.network_data['zone'] != "Internet":
    #     try:
    #         # FIXME: here 2 requests to the Ldap each time...
    #         device = LdapDevice.get(request.network_data['ip'])
    #         owner_short_uid = device.owner.split(",")[0][4:]
    #         user = LdapUser.get(uid=owner_short_uid)
    #         context['has_paid_cotiz'] = user.need_to_pay()
    #     except:
    #         pass
    return context
