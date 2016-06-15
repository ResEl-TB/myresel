from django.db import models
from django.template.defaultfilters import slugify
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.urlresolvers import reverse

# Classe pour les catégories d'article
# Le name et la description sont plutôt explicites
# Le slug sert de nom transformé pour que django puisse
# a partir d'une url avec, trouver cette category

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = RichTextUploadingField()
    fa_icon_name = models.CharField(max_length=64, blank=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Catégorie"
        
    
# Classe pour les articles
# La category, le name et le texte sont plutôt explicites
# Le slug sert de nom transformé pour que django puisse
# a partir d'une url avec, trouver cette category

class Article(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=255, null=True)
    text = RichTextUploadingField()
    date_creation = models.DateField(auto_now_add=True)
    date_last_edit = models.DateField(auto_now=True)
    slug = models.SlugField(max_length=255, blank=True, unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Article, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse ('custom-pages:show-article', args = [self.category.slug, self.slug])

    def __str__(self):
        return self.name
