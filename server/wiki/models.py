from django.conf import settings

from mahjong_portal.models import BaseModel
from django.db import models


class ArticleVersion(BaseModel):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True, default='')


class Article(models.Model):
    language = models.CharField(choices=settings.LANGUAGES)
    versions = models.ManyToManyField(ArticleVersion)
