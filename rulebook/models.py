# models.py
from django.db import models
from django.utils.text import slugify
from unidecode import unidecode
from mptt.models import MPTTModel, TreeForeignKey
import markdown

from django.conf import settings

MD_EXTENSIONS = getattr(settings, "MARKDOWN_EXTENSIONS", [
    "markdown.extensions.extra",
    "markdown.extensions.tables",
    "markdown.extensions.admonition",
    "markdown.extensions.codehilite",
])


class Folder(MPTTModel):
    name = models.CharField("Название", max_length=200)
    slug = models.SlugField("URL-имя", max_length=200, blank=True)
    parent = TreeForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE, verbose_name="Родитель"
    )
    order = models.PositiveIntegerField("Порядок", default=0)
    path = models.CharField("Путь", max_length=1000, editable=False)

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        unique_together = (('parent', 'slug'),)
        ordering = ['tree_id', 'lft']
        verbose_name = "Папка"
        verbose_name_plural = "Папки"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))[:200]
        super().save(*args, **kwargs)
        ancestors = self.get_ancestors(include_self=True)
        self.path = "/" + "/".join(a.slug for a in ancestors) + "/"
        super().save(update_fields=['path'])

    def __str__(self):
        return self.name


class Article(models.Model):
    folder = models.ForeignKey(
        Folder, related_name="articles",
        on_delete=models.CASCADE, verbose_name="Папка"
    )
    title = models.CharField("Заголовок", max_length=250)
    slug = models.SlugField("URL-имя", max_length=250, blank=True)
    content_markdown = models.TextField("Markdown")
    content_html = models.TextField("HTML", editable=False)
    order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        unique_together = (('folder', 'slug'),)
        ordering = ['folder__id', 'order']
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.title))[:250]
        self.content_html = markdown.markdown(
            self.content_markdown,
            extensions=MD_EXTENSIONS,
            output_format="html5"
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
