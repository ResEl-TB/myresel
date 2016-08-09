import operator

from ckeditor_uploader.fields import RichTextUploadingField
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify


# Classe pour les catégories d'article
# Le name et la description sont plutôt explicites
# La priority est l'ordre d'apparition des catégories dans la navbar
# Le slug sert de nom transformé pour que django puisse
# a partir d'une url avec, trouver cette category

class Category(models.Model):
    priority = models.IntegerField(default=0)
    nbToDisplay = models.IntegerField(default=0)
    name = models.CharField(max_length=64, unique=True)
    description = RichTextUploadingField()
    fa_icon_name = models.CharField(max_length=64, blank=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    def get_articles_and_links(self, in_resel=False):
        try:
            articles = [el for el in self.article_set.all() if not el.show_only_if_in_resel or in_resel]
            links = [el for el in self.link_set.all() if not el.show_only_if_in_resel or in_resel]
            stuff = list(articles)+list(links)
            stuff.sort(key=operator.attrgetter('priority'), reverse=True)

            return stuff
        except:
            return []

    def get_articles_and_links_to_display(self):
        stuff = self.get_articles_and_links()

        if self.nbToDisplay == 0:
            return stuff
        return stuff[:self.nbToDisplay]
    

    def is_display_truncated(self):
        try:
            return len(self.article_set.all())+len(self.link_set.all()) > self.nbToDisplay
        except:
            return False

    # Override

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "Catégorie"
        
    
# Classe pour les articles
# La category, le name et le texte sont plutôt explicites
# La priority est l'ordre d'apparition dans la catégorie
# Le slug sert de nom transformé pour que django puisse
# a partir d'une url avec, trouver cette category

class Article(models.Model):
    priority = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    show_only_if_in_resel = models.BooleanField(default=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, null=True)
    text = RichTextUploadingField()
    date_creation = models.DateField(auto_now_add=True)
    date_last_edit = models.DateField(auto_now=True)
    glyphicon_name = models.CharField(max_length=64, blank=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Article, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('wiki:show-article', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "Article"


# Classe pour les liens
# La category, le name, le description et le url sont plutôt explicites
# La priority est l'ordre d'apparition dans la catégorie
# La fa_icon_name est le nom de l'icone font-awesome décorant le lien
# Le slug sert de nom transformé pour que django puisse
# a partir d'une url avec, trouver cette category

class Link(models.Model):
    priority = models.IntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    show_only_if_in_resel = models.BooleanField(default=False)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, null=True)
    url = models.URLField()
    fa_icon_name = models.CharField(max_length=64, blank=True)
    glyphicon_name = models.CharField(max_length=64, blank=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Link, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return self.url

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = "Lien"