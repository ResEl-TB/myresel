from ckeditor.fields import RichTextField
from django.db import models


class News(models.Model):
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'

    titre = models.CharField(max_length=100)
    contenu = RichTextField()

    def __str__(self):
        return self.titre