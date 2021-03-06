# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-26 17:26
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('name_fr', models.CharField(max_length=64, null=True, unique=True)),
                ('name_en', models.CharField(max_length=64, null=True, unique=True)),
                ('description', models.CharField(max_length=255, null=True)),
                ('description_fr', models.CharField(max_length=255, null=True)),
                ('description_en', models.CharField(max_length=255, null=True)),
                ('text', ckeditor_uploader.fields.RichTextUploadingField()),
                ('text_fr', ckeditor_uploader.fields.RichTextUploadingField(null=True)),
                ('text_en', ckeditor_uploader.fields.RichTextUploadingField(null=True)),
                ('date_creation', models.DateField(auto_now_add=True)),
                ('date_last_edit', models.DateField(auto_now=True)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True)),
                ('name_fr', models.CharField(max_length=64, null=True, unique=True)),
                ('name_en', models.CharField(max_length=64, null=True, unique=True)),
                ('description', ckeditor_uploader.fields.RichTextUploadingField()),
                ('description_fr', ckeditor_uploader.fields.RichTextUploadingField(null=True)),
                ('description_en', ckeditor_uploader.fields.RichTextUploadingField(null=True)),
                ('fa_icon_name', models.CharField(blank=True, max_length=64)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Catégorie',
            },
        ),
        migrations.AddField(
            model_name='article',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wiki.Category'),
        ),
    ]
