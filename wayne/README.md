# Wayne skills

Wayne is the minipass data assistant. He only answers questions about data stored in minipass.

## How routing works

1. `router.py` matches common English/French questions locally.
2. Only unmatched wording goes to OpenRouter.
3. OpenRouter may select an approved skill and arguments. It never sees the schema, writes SQL, or receives query results.
4. The selected trusted Python skill reads the database and formats the answer.

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
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

The key is required only for questions the local router cannot match.
