from django.db import models
from ckeditor.fields import RichTextField

class News(models.Model):
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'

    titre = models.CharField(max_length = 100)
    contenu = RichTextField()

    def __str__(self):
        return self.titre