import uuid

from django.db import migrations

import fonctions.fields


class Migration(migrations.Migration):
    """Garde les codes UUID en char(32) avec Django 5 (sans effet sur les bases existantes)."""

    dependencies = [
        ('gestion_personnes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermetadata',
            name='email_validation_code',
            field=fonctions.fields.Char32UUIDField(default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='usermetadata',
            name='reset_pwd_code',
            field=fonctions.fields.Char32UUIDField(default=uuid.uuid4),
        ),
    ]
