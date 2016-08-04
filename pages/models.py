from ckeditor.fields import RichTextField
from django.db import models
from django.contrib.auth.models import User


class News(models.Model):
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'

    title = models.CharField(max_length=100)
    content = RichTextField()
    author = models.ForeignKey(User, null=True, blank=True)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre