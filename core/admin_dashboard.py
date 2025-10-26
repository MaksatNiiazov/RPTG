from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Dict, List, Tuple

from django.contrib import admin
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


def _build_stats() -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
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

    stats = [
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

    metrics = {
        "total_users": total_users,
        "active_users": active_users,
        "total_characters": total_characters,
        "new_characters_week": new_characters_week,
        "total_worlds": total_worlds,
        "pending_invitations": pending_invitations,
        "total_items": total_items,
        "new_items_week": new_items_week,
    }

    return stats, metrics


def _build_worlds() -> List[World]:
    return list(
        World.objects.annotate(
            player_count=Count("players", distinct=True),
            character_count=Count("characters", distinct=True),
        )
        .order_by("-created_at")[:5]
    )


def _build_recent_activity() -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    for character in (
        Character.objects.select_related("world")
        .order_by("-created_at")
        .only("name", "created_at", "world__name")[:4]
    ):
        entries.append(
            {
                "title": character.name,
                "subtitle": _("Персонаж")
                + (
                    f" · {character.world.name}"
                    if getattr(character, "world", None)
                    else ""
                ),
                "icon": "stadia_controller",
                "accent": "text-primary-500 dark:text-primary-300",
                "timestamp": character.created_at,
            }
        )

    for item in (
        Item.objects.select_related("rarity", "type")
        .order_by("-created_at")
        .only("name", "created_at", "rarity__name", "type__name")[:4]
    ):
        details: List[str] = []
        if getattr(item, "rarity", None):
            details.append(item.rarity.name)
        if getattr(item, "type", None):
            details.append(item.type.name)
        subtitle = _("Предмет")
        if details:
            subtitle = f"{subtitle} · {' · '.join(details)}"

        entries.append(
            {
                "title": item.name,
                "subtitle": subtitle,
                "icon": "inventory_2",
                "accent": "text-amber-500 dark:text-amber-300",
                "timestamp": item.created_at,
            }
        )

    for world in World.objects.order_by("-created_at").only("name", "created_at")[:4]:
        entries.append(
            {
                "title": world.name,
                "subtitle": _("Мир"),
                "icon": "public",
                "accent": "text-secondary-500 dark:text-secondary-300",
                "timestamp": world.created_at,
            }
        )

    entries.sort(key=lambda entry: entry.get("timestamp") or timezone.now(), reverse=True)

    return entries[:6]


def _build_summary(metrics: Dict[str, int]) -> Dict[str, str]:
    return {
        "subtitle": _("Панель управления"),
        "title": _("Мастерская приключений"),
        "description": _(
            "%(worlds)s миров, %(characters)s персонажей и %(items)s предметов готовы к обновлениям."
        )
        % {
            "worlds": metrics["total_worlds"],
            "characters": metrics["total_characters"],
            "items": metrics["total_items"],
        },
        "note": _(
            "За неделю создано %(characters)s персонажей и %(items)s предметов, активных игроков: %(users)s."
        )
        % {
            "characters": metrics["new_characters_week"],
            "items": metrics["new_items_week"],
            "users": metrics["active_users"],
        },
    }


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
    stats, metrics = _build_stats()

    return {
        "dashboard_stats": stats,
        "dashboard_summary": _build_summary(metrics),
        "weekly_highlights": {
            "characters": metrics["new_characters_week"],
            "items": metrics["new_items_week"],
        },
        "character_growth_data": chart_data,
        "character_growth_options": chart_options,
        "dashboard_worlds": _build_worlds(),
        "latest_spells": Spell.objects.select_related("school", "category")
        .order_by("-id")[:5],
        "latest_items": Item.objects.select_related("rarity", "type")
        .order_by("-created_at")[:5],
        "quick_links": _build_quick_links(),
        "recent_activity": _build_recent_activity(),
    }


def _custom_admin_index(self, request, extra_context: Dict[str, Any] | None = None):
    extra_context = extra_context or {}
    extra_context.update(build_dashboard_context())

    response: TemplateResponse = _ORIGINAL_INDEX(request, extra_context=extra_context)
    return response


_ORIGINAL_INDEX = admin.site.index
admin.site.index = _custom_admin_index.__get__(admin.site, admin.sites.AdminSite)
admin.site.index_template = "admin/index.html"
