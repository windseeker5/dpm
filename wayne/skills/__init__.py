"""Wayne skill registry.

Adding or changing a skill:
1. Put its trusted query handler in the matching domain module.
2. Add one SkillDefinition to that module's SKILLS list.
3. Import a new domain module below only when creating a new skill category.

The router automatically receives this metadata; no prompt duplication is needed.
"""

from . import activities, bookings, communications, customers, finances, operations, participants, passports, surveys

_ALL = (
    activities.SKILLS
    + participants.SKILLS
    + passports.SKILLS
    + bookings.SKILLS
    + operations.SKILLS
    + customers.SKILLS
    + communications.SKILLS
    + finances.SKILLS
    + surveys.SKILLS
)

SKILLS = {skill.name: skill for skill in _ALL}


def public_catalog(language: str = "en") -> list[dict]:
    """Return compact, single-language metadata for inexpensive AI routing."""
    description_attr = "description_fr" if language == "fr" else "description_en"
    return [
        {
            "name": skill.name,
            "description": getattr(skill, description_attr),
            "parameters": list(skill.parameters),
        }
        for skill in _ALL
    ]
