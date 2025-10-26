from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Dict, List

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from character.models import Character
from items.models import Item
from magic.models import Spell
from worlds.models import World, WorldInvitation


def _build_character_growth() -> tuple[str, str]:
    """Return chart labels/data for characters created during the last six weeks."""
    now = timezone.now()
    start_period = now - timedelta(weeks=5)

    aggregated = (
        Character.objects.filter(created_at__gte=start_period)
        .annotate(period=TruncWeek("created_at"))
        .values("period")
        .annotate(total=Count("id"))
    )

    counts: Dict[Any, int] = {}
    for entry in aggregated:
        period = entry.get("period")
        if period is None:
            continue
        period_start = timezone.localtime(period).date()
        counts[period_start] = entry.get("total", 0)

    labels: List[str] = []
    values: List[int] = []
    for offset in range(5, -1, -1):
        reference = now - timedelta(weeks=offset)
        reference = reference - timedelta(days=reference.weekday())
        period_key = reference.date()
        labels.append(date_format(reference, "d E"))
        values.append(counts.get(period_key, 0))

    chart_data = {
        "labels": labels,
        "datasets": [
            {
                "label": str(_("Новые персонажи")),
                "data": values,
                "borderColor": "#6366F1",
                "backgroundColor": "rgba(99, 102, 241, 0.2)",
                "pointRadius": 4,
                "pointHoverRadius": 6,
                "tension": 0.35,
                "fill": True,
            }
        ],
    }

    chart_options = {
        "responsive": True,
        "maintainAspectRatio": False,
        "plugins": {
            "legend": {"display": False},
            "tooltip": {
                "backgroundColor": "rgba(17, 24, 39, 0.85)",
                "displayColors": False,
            },
        },
        "scales": {
            "x": {
                "grid": {"display": False},
                "ticks": {"color": "#6B7280"},
            },
            "y": {
                "grid": {"color": "rgba(209, 213, 219, 0.4)"},
                "ticks": {
                    "precision": 0,
                    "color": "#6B7280",
                },
            },
        },
    }

    return json.dumps(chart_data), json.dumps(chart_options)


def _build_stats() -> List[Dict[str, Any]]:
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    total_characters = Character.objects.count()
    new_characters_week = Character.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    total_worlds = World.objects.count()
    pending_invitations = WorldInvitation.objects.filter(accepted=False).count()

    total_items = Item.objects.count()
    new_items_week = Item.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()

    return [
        {
            "label": _("Пользователи"),
            "value": total_users,
            "icon": "groups",
            "caption": _("активных: %(count)s") % {"count": active_users},
        },
        {
            "label": _("Персонажи"),
            "value": total_characters,
            "icon": "stadia_controller",
            "caption": _("новых за неделю: %(count)s") % {"count": new_characters_week},
        },
        {
            "label": _("Миры"),
            "value": total_worlds,
            "icon": "public",
            "caption": _("приглашений в ожидании: %(count)s")
            % {"count": pending_invitations},
        },
        {
            "label": _("Предметы"),
            "value": total_items,
            "icon": "inventory_2",
            "caption": _("новых за неделю: %(count)s") % {"count": new_items_week},
        },
    ]


def _build_worlds() -> List[World]:
    return list(
        World.objects.annotate(
            player_count=Count("players", distinct=True),
            character_count=Count("characters", distinct=True),
        )
        .order_by("-created_at")[:5]
    )


def _build_quick_links() -> List[Dict[str, str]]:
    return [
        {
            "title": _("Создать персонажа"),
            "description": _("Быстрый переход к форме добавления нового героя."),
            "icon": "face_retouching_natural",
            "url": reverse("admin:character_character_add"),
        },
        {
            "title": _("Добавить заклинание"),
            "description": _("Пополните базу свежей магией в один клик."),
            "icon": "auto_awesome",
            "url": reverse("admin:magic_spell_add"),
        },
        {
            "title": _("Создать предмет"),
            "description": _("Добавьте артефакт или экипировку прямо сейчас."),
            "icon": "shield_with_heart",
            "url": reverse("admin:items_item_add"),
        },
        {
            "title": _("Открыть новый мир"),
            "description": _("Подготовьте площадку для следующей кампании."),
            "icon": "travel_explore",
            "url": reverse("admin:worlds_world_add"),
        },
    ]


def build_dashboard_context() -> Dict[str, Any]:
    chart_data, chart_options = _build_character_growth()

    return {
        "dashboard_stats": _build_stats(),
        "character_growth_data": chart_data,
        "character_growth_options": chart_options,
        "dashboard_worlds": _build_worlds(),
        "latest_spells": Spell.objects.select_related("school", "category")
        .order_by("-id")[:5],
        "latest_items": Item.objects.select_related("rarity", "type")
        .order_by("-created_at")[:5],
        "quick_links": _build_quick_links(),
    }


def _custom_admin_index(self, request, extra_context: Dict[str, Any] | None = None):
    extra_context = extra_context or {}
    extra_context.update(build_dashboard_context())

    response: TemplateResponse = _ORIGINAL_INDEX(request, extra_context=extra_context)
    return response


_ORIGINAL_INDEX = admin.site.index
admin.site.index = _custom_admin_index.__get__(admin.site, admin.sites.AdminSite)
admin.site.index_template = "admin/index.html"


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Read-only admin interface for Django's action log."""

    date_hierarchy = "action_time"
    list_display = (
        "action_time",
        "user",
        "content_type",
        "object_repr",
        "action_flag",
    )
    list_filter = ("action_flag", "user", "content_type")
    ordering = ("-action_time",)
    search_fields = ("object_repr", "change_message", "user__username", "user__email")
    readonly_fields = (
        "action_time",
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
