# Wayne skills

Wayne is the minipass data assistant. He only answers questions about data stored in minipass.

## How routing works

1. `router.py` matches common English/French questions locally for zero AI tokens.
2. Obvious minipass questions without a supported skill get a local explanation instead of an AI call.
3. Only unusual wording goes to OpenRouter, using a compact single-language skill list.
4. OpenRouter may select an approved skill and arguments. It never sees the schema, writes SQL, or receives query results.
5. Successful AI routing decisions are cached in memory so repeated questions use zero additional tokens.
6. The selected trusted Python skill reads the database and formats the answer.

Wayne safely handles empty or truncated model output, retries it once, and then returns useful example questions instead of appearing broken. A per-process daily request limit provides a final spending safeguard.

## Change an existing skill

Open the matching file under `wayne/skills/`:

- `participants.py` — people, signups, paid/unpaid lists
- `passports.py` — passport counts and credits
- `activities.py` — activity lists
- `bookings.py` — sessions, seats, attendance
- `finances.py` — revenue and cash flow
- `surveys.py` — survey totals

Each skill has two nearby pieces:

```python
def count_passports(args, language):
    # Trusted SQLAlchemy query and bilingual result formatting
    ...

SkillDefinition(
    name="count_passports",
    description_en="...",
    description_fr="...",
    examples=(...),
    parameters={...},
    handler=count_passports,
)
```

Edit the handler to change what it calculates. Edit `SkillDefinition` to change how Wayne understands when to use it.

## Add a skill

1. Add a trusted handler to the matching domain file.
2. Add its `SkillDefinition` to that file's `SKILLS` list.
3. Optionally add obvious bilingual keywords to `_local_decision()` in `wayne/router.py` to avoid an OpenRouter call.
4. Add a new module to `wayne/skills/__init__.py` only when creating a new domain category.

## `.env`

```env
OPENROUTER_API_KEY=your-key
# Prefer a cheap, non-reasoning model that supports JSON output.
OPENROUTER_MODEL=openai/gpt-4.1-nano
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DAILY_REQUEST_LIMIT=50
OPENROUTER_MAX_TOKENS=300
```

The key is required only for questions the local router cannot match. Set the daily limit to `0` to disable OpenRouter completely. The limit is per application process; also configure an account-level spending limit in OpenRouter for production protection.
