# Educate Ken: How Wayne Works

This document explains Wayne in plain language: what we built, where each part lives, how guardrails work, and how to change or add skills.

## 1. What Wayne is

Wayne is the minipass data assistant.

Wayne is **not** a general chatbot and does not generate SQL. He can only select and execute trusted skills that we wrote in Python.

The basic flow is:

```text
Administrator asks a question
             ↓
Local bilingual router tries to recognize it
             ↓
     ┌───────┴────────┐
     │                │
Recognized locally   Ambiguous wording
     │                │
No API call          OpenRouter selects a skill
     │                │
     └───────┬────────┘
             ↓
A trusted Python skill queries SQLite
             ↓
Wayne returns a bilingual answer and optional table
```

OpenRouter never receives:

- The SQLite schema
- Generated SQL
- Database query results
- Participant names, emails, or telephone numbers

OpenRouter receives only the administrator's question and the approved skill catalog. Its only job is to select a skill and parameters.

## 2. Project structure

```text
wayne/
├── README.md              Quick instructions for changing skills
├── __init__.py            Exports Wayne's Flask blueprint
├── client.py              Minimal OpenRouter client and `.env` loading
├── router.py              Language detection, aliases, scope, and skill selection
├── routes.py              Flask page/API routes, responses, and audit logging
├── types.py               Shared SkillDefinition, SkillResult, and RouteDecision types
└── skills/
    ├── __init__.py        Combines every skill into one approved registry
    ├── helpers.py         Shared formatting and activity filters
    ├── activities.py      Activity skills
    ├── participants.py    Participant, signup, and payment-status skills
    ├── passports.py       Passport and remaining-credit skills
    ├── bookings.py        Session, seat, and attendance skills
    ├── finances.py        Revenue and cash-flow skills
    └── surveys.py         Survey skills

wayne UI:
├── templates/analytics_chatbot_simple.html
├── static/css/wayne-chat.css
└── static/js/wayne-chat.js
```

The Flask blueprint is registered in `app.py`:

```python
from wayne import wayne_bp
app.register_blueprint(wayne_bp)
```

The page remains available at `/chatbot/`.

## 3. Where Wayne's personality is defined

Wayne's personality currently has three layers.

### Identity and mission

File: `wayne/router.py`

Constant: `SYSTEM_PROMPT`

This tells OpenRouter:

- His name is Wayne.
- He is the minipass data assistant.
- He only works with approved minipass topics.
- He must select a skill rather than answer the question.
- He must never write SQL.
- He must return constrained JSON.

This is the main agent identity and scope definition.

### Greeting, refusal, and unsupported messages

File: `wayne/routes.py`

Function: `_message()`

This contains Wayne's English and French messages for:

- `greeting` — the administrator says hello.
- `out_of_scope` — the question is unrelated to minipass.
- `unsupported` — the question concerns minipass, but no skill supports it yet.

Change these messages to adjust Wayne's conversational tone.

### Data-answer wording

Files: `wayne/skills/*.py`

Every skill creates its own short English/French answer. For example, `count_passports()` decides how Wayne phrases the passport total.

This keeps answers accurate and inexpensive because OpenRouter does not rewrite database results.

## 4. Where the guardrails are defined

Wayne uses multiple guardrails. We do not rely on one prompt.

### Guardrail 1: Local out-of-scope detection

File: `wayne/router.py`

Function: `_local_decision()`

Known unrelated subjects are rejected locally. Current examples include:

- Weather
- Recipes
- Jokes
- Politics
- Stock prices and the stock market
- Météo, recettes, politique, bourse, and marché boursier

A stock-market question therefore returns Wayne's refusal without querying SQLite or calling OpenRouter.

### Guardrail 2: OpenRouter's strict system prompt

File: `wayne/router.py`

Constant: `SYSTEM_PROMPT`

For ambiguous wording, OpenRouter may return only:

```json
{
  "status": "skill | out_of_scope | unsupported",
  "language": "en | fr",
  "skill": "approved_skill_name_or_null",
  "arguments": {}
}
```

OpenRouter is explicitly told never to answer and never to write SQL.

### Guardrail 3: Server-side skill validation

File: `wayne/router.py`

Even if the model returns a bad or invented skill, Python checks:

```python
if status == "skill" and skill_name not in SKILLS:
    status, skill_name = "unsupported", None
```

Only skills registered in `wayne/skills/__init__.py` can execute.

Arguments are also filtered against the selected skill's approved parameter list. Unknown arguments are discarded.

### Guardrail 4: Model output is never shown as an answer

The OpenRouter response is parsed only as a routing decision. Its text is never displayed directly to the administrator.

This means the model cannot bypass Wayne's scope by returning an essay, stock advice, or invented participant data.

### Guardrail 5: Trusted queries only

The actual database work is written manually inside `wayne/skills/*.py` using SQLAlchemy or fixed, parameterized SQL.

OpenRouter cannot create or modify a database query.

### Guardrail 6: Authentication, CSRF, limits, and audit

File: `wayne/routes.py`

- A valid admin session is required.
- The `/chatbot/ask` request is CSRF-protected.
- Requests are rate-limited.
- Questions are limited to 500 characters.
- Skill results are limited to 200 rows where applicable.
- Every request is written to `QueryLog`.

`QueryLog.generated_sql` is a legacy column name. Wayne stores values such as `skill:list_unpaid_participants` there—never generated SQL.

## 5. Where the skills are defined

Each domain file has trusted handler functions followed by a `SKILLS` list.

Example structure:

```python
def count_passports(args, language):
    # Trusted SQLAlchemy query
    # Bilingual answer formatting
    return SkillResult(answer=answer, columns=columns, rows=rows)


SKILLS = [
    SkillDefinition(
        name="count_passports",
        description_en="Count passports, optionally for an activity.",
        description_fr="Compter les passeports, avec activité facultative.",
        examples=("How many passports?", "Combien de passeports?"),
        parameters={"activity": "Optional activity name"},
        handler=count_passports,
    )
]
```

The `SkillDefinition` metadata tells OpenRouter when to choose the skill. The handler contains the trusted query and final answer.

### Current skills

#### `wayne/skills/activities.py`

- `list_activities`

#### `wayne/skills/participants.py`

- `count_participants`
- `count_signups`
- `list_unpaid_participants`
- `list_paid_participants`

#### `wayne/skills/passports.py`

- `count_passports`
- `list_active_passports`
- `list_exhausted_passports`

#### `wayne/skills/bookings.py`

- `available_session_seats`
- `session_attendance`

#### `wayne/skills/finances.py`

- `activity_revenue`
- `financial_summary`

#### `wayne/skills/surveys.py`

- `survey_summary`

The central approved registry is built in `wayne/skills/__init__.py`:

```python
SKILLS = {skill.name: skill for skill in _ALL}
```

If a skill is not in that registry, Wayne cannot run it.

## 6. Where aliases and bilingual expressions are defined

There are two kinds of aliases.

### Fast local aliases

File: `wayne/router.py`

Function: `_local_decision()`

The tuples inside this function define common equivalent expressions. Examples:

```python
("how many", "count", "combien", "nombre")
("unpaid", "not paid", "non pay", "impaye", "pas paye")
("cash flow", "tresorerie", "sommaire financier")
("attendance", "attended", "presence", "present")
```

These aliases avoid an OpenRouter call entirely.

To support a new obvious phrase, add it to the appropriate tuple. The router removes accents and converts text to lowercase before matching, so `trésorerie` can match `tresorerie`.

### OpenRouter aliases and examples

Files: `wayne/skills/*.py`

Fields:

- `description_en`
- `description_fr`
- `examples`
- `parameters`

These teach OpenRouter how to map less predictable wording to an existing skill.

Use local aliases for frequent, obvious wording. Use skill descriptions/examples for flexible natural-language interpretation.

## 7. Language handling

File: `wayne/router.py`

Function: `detect_language()`

Constant: `FRENCH_MARKERS`

Wayne detects French using common minipass words such as `combien`, `activité`, `inscription`, `passeport`, `payé`, `revenu`, and `sondage`.

The selected language is passed into the skill handler. The handler then chooses its French or English answer and column labels.

## 8. OpenRouter configuration and cost control

Configuration is in `.env`:

```env
OPENROUTER_API_KEY=hidden-key
OPENROUTER_MODEL=deepseek/deepseek-v4-flash
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

File: `wayne/client.py`

The selected model is `deepseek/deepseek-v4-flash`, the same model used by Liquidator. It is inexpensive and more than capable of selecting one skill from a short catalog.

Wayne reloads `.env` before reading OpenRouter configuration, so debug-mode configuration changes do not require a manual application restart.

### How Wayne saves tokens

- Common questions never call OpenRouter.
- OpenRouter receives a compact skill catalog, not the database schema.
- The model returns at most a small JSON decision.
- SQLite performs all counting and calculations.
- Python formats the final answer.
- There is no second model call to rewrite results.

## 9. Example request flows

### Common question: no OpenRouter cost

```text
Question: "Combien de passeports?"
Local alias: "combien" + "passeports"
Skill: count_passports
SQLite result: 360
Wayne: "Il y a 360 passeport(s) pour toutes les activités."
```

### Ambiguous wording: one small OpenRouter call

```text
Question: "Pourrais-tu me donner le volume global des adhésions enregistrées?"
Local router: no confident match
OpenRouter: selects count_signups
Python validates the skill
Trusted skill queries SQLite
Wayne returns the result
```

### Out-of-scope question

```text
Question: "Should I buy this stock?"
Local guardrail recognizes stock-market wording
Status: out_of_scope
Wayne refuses
No database query
No OpenRouter call
```

### Missing minipass capability

```text
Question: "Compare survey satisfaction by participant age"
No existing skill can perform that analysis
Status: unsupported
Wayne explains that the skill has not been added yet
```

## 10. How to change an existing skill

1. Find the domain file under `wayne/skills/`.
2. Find the handler function.
3. Change only its trusted query or answer formatting.
4. Update its `SkillDefinition` descriptions/examples if its purpose changed.
5. Test the English and French versions directly against SQLite.

Example: unpaid registrations live in:

```text
wayne/skills/participants.py
→ list_unpaid_participants()
→ _list_by_payment()
```

## 11. How to add a new skill

Example: add `count_unpaid_signups`.

1. Add a trusted handler to `wayne/skills/participants.py`.
2. Add a `SkillDefinition` to that file's `SKILLS` list.
3. Add common English/French aliases to `_local_decision()` if the question should avoid OpenRouter.
4. Verify the result against SQLite.
5. Verify one English and one French question through `/chatbot/`.

Do not add generated SQL, raw schema access, or a second model call.

## 12. The main rule to remember

Wayne is not trusted because the prompt says he is safe.

Wayne is trusted because the code gives the model only one limited decision:

> Select one approved skill—or refuse.

Python controls the skill registry, arguments, database query, formatting, authentication, row limits, and audit trail.
