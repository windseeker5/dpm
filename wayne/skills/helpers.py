"""Formatting and filtering helpers shared by Wayne skills."""

from typing import Any

from sqlalchemy import func

from models import Activity

MAX_ROWS = 200


def activity_filter(query, activity_column, activity_name: str | None):
    """Apply a case-insensitive activity-name filter when one was requested."""
    if activity_name:
        query = query.filter(func.lower(activity_column).contains(activity_name.strip().lower()))
    return query


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
