Versions : CI / flea / skynet
=============================

Relevé du 23/10/2026.

| | CI | flea (preprod) | skynet (prod) |
|---|---|---|---|
| Debian | 13.7 | 13.7 | ? |
| Python | 3.11.17 | 3.11.8 | ? |
| Django | 4.2.30 | 4.2.30 | 3.2.25 |
| MariaDB | 11.8 | 11.8.6 | ? (hôte `mysql`) |
| Redis | 8.0 | 8.0.2 | 8.10.2 (hôte `mysql`) |

# Relever les versions (flea, skynet)

```bash
cat /etc/debian_version
cd /srv/www/resel.fr && sudo -u www-data env/bin/python manage.py shell -c "
import sys, django, redis; from django.conf import settings as s; from django.db import connection as c
cur = c.cursor(); cur.execute('SELECT VERSION()'); print(cur.fetchone()[0])
print(sys.version.split()[0], django.__version__)
print(redis.Redis(host=s.REDIS_HOST, port=s.REDIS_PORT, password=s.REDIS_PASSWORD or None).info()['redis_version'])
"
```
