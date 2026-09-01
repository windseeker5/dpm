"""Small shared types for Wayne's trusted skill system."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class SkillDefinition:
    """Metadata plus the trusted Python handler for one skill."""

    name: str
    description_en: str
    description_fr: str
    examples: tuple[str, ...]
    parameters: dict[str, str]
    handler: Callable[[dict[str, Any], str], "SkillResult"]


@dataclass
class SkillResult:
    """A safe, display-ready result returned by a skill."""

    answer: str
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)


@dataclass
class RouteDecision:
    """The router's constrained decision. It never contains SQL."""

    status: str
    language: str
    skill: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    source: str = "local"
    model: str | None = None
    tokens_used: int = 0
