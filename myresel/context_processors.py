from fonctions import network, ldap


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
    if request.user.is_authenticated():
        context['need_to_pay'] = ldap.need_to_pay(request.user.username)

    return context
