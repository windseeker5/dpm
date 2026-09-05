"""Formatting and filtering helpers shared by Wayne skills."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from models import Activity

MAX_ROWS = 200


def activity_filter(query, activity_column, activity_name: str | None):
    """Apply a case-insensitive activity-name filter when one was requested."""
    if activity_name:
        query = query.filter(func.lower(activity_column).contains(activity_name.strip().lower()))
    return query


def date_bounds(args: dict) -> tuple[datetime | None, datetime | None]:
    """Return inclusive/exclusive local date bounds for Wayne's common periods."""
    now = datetime.now()
    period = args.get("period")
    year = args.get("year")
    if year is not None:
        try:
            year = int(year)
            if 1900 <= year <= 2100:
                return datetime(year, 1, 1), datetime(year + 1, 1, 1)
        except (TypeError, ValueError):
            pass
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)
    if period == "this_week":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=7)
    if period == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
        return start, end
    if period == "this_year":
        return datetime(now.year, 1, 1), datetime(now.year + 1, 1, 1)
    return None, None


def period_label(args: dict, language: str) -> str:
    if args.get("year"):
        return f" en {args['year']}" if language == "fr" else f" in {args['year']}"
    labels = {
        "today": (" aujourd’hui", " today"),
        "this_week": (" cette semaine", " this week"),
        "this_month": (" ce mois-ci", " this month"),
        "this_year": (" cette année", " this year"),
    }
    french, english = labels.get(args.get("period"), ("", ""))
    return french if language == "fr" else english


def activity_label(activity_name: str | None, language: str) -> str:
    if not activity_name:
        return "toutes les activités" if language == "fr" else "all activities"
    return f"« {activity_name.strip()} »"


def money(value: Any) -> str:
    return f"${float(value or 0):,.2f}"


def display(value: Any) -> Any:
    if value is None:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return value


def rows_from(records) -> list[list[Any]]:
    return [[display(value) for value in record] for record in records]
