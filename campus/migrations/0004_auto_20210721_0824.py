# Generated by Django 2.2.24 on 2021-07-21 06:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('campus', '0003_add_booking_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roomadmin',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='utilisateur'),
        ),
    ]
