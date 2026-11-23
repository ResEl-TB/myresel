from django.db import models


# pylint-django 2.8 + astroid 4 remplacent la MRO des sous-classes de champs par uuid.UUID (faux positifs
# no-member / unexpected-keyword-arg), cf. pylint-dev/pylint-django#477.
# shortcut: disables locaux, à retirer quand pylint-django#488 sera publié
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
        value = super().get_db_prep_value(value, connection, prepared)  # pylint: disable=no-member
        if value is not None:
            value = value.hex
        return value
