from fonctions import network, ldap


def resel_context(request):
    """
    This context processor objective is to get information about the machine
    network status.
    :param request:
    :return: dict : a context with the machine ip, if the ip belongs to the resel and the machine status
    """
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']

    status = None
    ip_in_resel = network.is_resel_ip(ip)
    if ip_in_resel:
        status = ldap.get_status(ip)
    return {
        'machine_ip': ip,
        'is_ip_in_resel': ip_in_resel,
        'machine_status': status,
    }
