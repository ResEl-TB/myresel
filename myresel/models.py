from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.
class Billet(models.Model):
    titre = models.CharField(max_length = 100)
    contenu = RichTextField()

    def __str__(self):
        return self.titre