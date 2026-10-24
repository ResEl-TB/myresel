from django.db import models


class Char32UUIDField(models.UUIDField):
    """
    UUIDField stocké en char(32), comme avant Django 5.0.

    Depuis Django 5.0, UUIDField est une colonne UUID native sur MariaDB 10.7+ et Django envoie
    des valeurs de 36 caractères : les colonnes créées avant restent en char(32) (« Data too long »).
    Voir les notes de version de Django 5.0, « Migrating existing UUIDField on MariaDB 10.7+ ».
    """
    def db_type(self, connection):
        return "char(32)"

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super().get_db_prep_value(value, connection, prepared)
        if value is not None:
            value = value.hex
        return value
