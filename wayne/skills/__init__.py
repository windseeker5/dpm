"""Wayne skill registry.

Adding or changing a skill:
1. Put its trusted query handler in the matching domain module.
2. Add one SkillDefinition to that module's SKILLS list.
3. Import a new domain module below only when creating a new skill category.

The router automatically receives this metadata; no prompt duplication is needed.
"""

from . import activities, bookings, finances, participants, passports, surveys

_ALL = (
    activities.SKILLS
    + participants.SKILLS
    + passports.SKILLS
    + bookings.SKILLS
    + finances.SKILLS
    + surveys.SKILLS
)

SKILLS = {skill.name: skill for skill in _ALL}


def public_catalog() -> list[dict]:
    """Return only the compact metadata OpenRouter needs for skill selection."""
    return [
        {
            "name": skill.name,
            "description_en": skill.description_en,
            "description_fr": skill.description_fr,
            "parameters": skill.parameters,
            "examples": list(skill.examples),
        }
        for skill in _ALL
    ]
