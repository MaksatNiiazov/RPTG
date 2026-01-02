# admin.py
from time import timezone

from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin
from .models import Folder, Article, ImprovementProposal
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
    filter_horizontal = ("related_articles",)


@admin.register(ImprovementProposal)
class ImprovementProposalAdmin(ModelAdmin):
    list_display = (
        "short_article", "submitter_name", "status", "submitted_at", "reviewed_at"
    )
    list_filter  = ("status",)
    search_fields = ("suggestion", "submitter_name", "submitter_email")
    readonly_fields = ("submitted_at",)

    fieldsets = (
        (None, {
            "fields": (
                "article", "suggestion",
            )
        }),
        ("Автор", {
            "fields": (
                "submitter_name", "submitter_email",
            )
        }),
        ("Статус обработки", {
            "classes": ("collapse",),
            "fields": (
                "status", "reviewed_at",
            )
        }),
    )

    def short_article(self, obj):
        return obj.article and obj.article.title or "—"
    short_article.short_description = "Статья"

    def save_model(self, request, obj, form, change):
        # При выставлении статуса проверяем дату обзора
        if change and "status" in form.changed_data and not obj.reviewed_at:
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)