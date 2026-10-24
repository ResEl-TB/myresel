import uuid

from django.db import migrations

import fonctions.fields


class Migration(migrations.Migration):
    """Garde la colonne uuid en char(32) avec Django 5 (sans effet sur les bases existantes)."""

    dependencies = [
        ('tresorerie', '0014_auto_20210721_0824'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='uuid',
            field=fonctions.fields.Char32UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
