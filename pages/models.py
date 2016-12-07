from ckeditor.fields import RichTextField
from django.db import models
from django.contrib.auth.models import User


class News(models.Model):
    class Meta:
        verbose_name = 'news'
        verbose_name_plural = 'news'

    title = models.CharField(max_length=100)
    content = RichTextField()
    author = models.ForeignKey(User, null=True, blank=True, editable=False)
    date = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title

class Faq(models.Model):
    question_text = models.CharField(max_length=200)
    response = RichTextField()
    author = models.ForeignKey(User, null=True, blank=True, editable=False)
    date = models.DateTimeField(auto_now=True)
    vote = models.IntegerField(default=0)

    def upvote(self):
        self.vote += 1
        self.save()


    def __str__(self):
        return self.question_text
