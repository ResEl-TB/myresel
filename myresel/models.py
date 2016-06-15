from django.db import models
from ckeditor.fields import RichTextField

class News(models.Model):
    titre = models.CharField(max_length = 100)
    contenu = RichTextField()

    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'

    def __str__(self):
        return self.titre