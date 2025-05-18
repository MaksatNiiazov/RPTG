# admin.py
from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Folder, Article
from unfold.admin import ModelAdmin


@admin.register(Folder)
class FolderAdmin(ModelAdmin, DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = ("tree_actions", "indented_title", "order", "slug", "path")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}

    class Media:
        css = {
            "all": ("mptt/draggable-admin.css",)
        }
        js = (
            "admin/js/vendor/jquery/jquery.js",
            "mptt/draggable-admin.js",
        )


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = ("title", "folder", "order", "created_at")
    list_editable = ("order",)
    list_filter = ("folder",)
    prepopulated_fields = {"slug": ("title",)}

