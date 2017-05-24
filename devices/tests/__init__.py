from myresel import settings
from devices.models import LdapDevice

def register_device(mac=None):
    if mac is None:
        mac = settings.DEBUG_SETTINGS['mac']
    device = LdapDevice()
    device.mac_address=mac
    device.host = 'pcamanoury5'
    device.owner = "uid=amanoury,ou=people,dc=maisel,dc=enst-bretagne,dc=fr"
    device.save()

