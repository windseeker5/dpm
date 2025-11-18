# Chatbot Enhancement Plan: Bilingual + Semantic Intelligence

**Created**: 2025-01-17
**Status**: Proposal - Ready for Review
**Estimated Effort**: 4-6 hours
**Priority**: High (Addresses French query failures + wrong table/column selection)

---

## Executive Summary

Enhance the existing Minipass chatbot with French language support and semantic business term understanding without requiring an MCP server. This plan builds on the current prompt-based architecture while addressing two critical issues:

1. **French queries fail** - Users cannot ask questions in French
2. **Wrong table/column selection** - Business terms like "cash flow" don't map to correct database columns

## Current State Analysis

### What's Working Well
- ✅ Schema-aware prompt engineering with live database introspection
- ✅ Multi-provider AI system (Gemini → Groq fallback)
- ✅ Strong security validation (read-only, table whitelisting)
- ✅ Good observability (QueryLog, ChatUsage tracking)
- ✅ Production-ready error handling

### Critical Gaps
- ❌ **No French language support** - zero translation or bilingual capabilities
- ❌ **No semantic aliases** - "cash flow" doesn't map to `passport.sold_amt`
- ❌ **No business context** - AI doesn't understand Minipass-specific terminology
- ❌ **Stateless queries** - each question processed in isolation

### Research Findings

**Current Architecture**: Located in `chatbot_v2/`
- **query_engine.py** (435 lines) - Core SQL generation engine
- **routes_simple.py** (409 lines) - Flask endpoints
- **security.py** (303 lines) - SQL validation
- **providers/gemini.py** (262 lines) - Primary AI provider

**Key Insight**: The system uses schema-aware prompting with few-shot examples. Adding a semantic layer + bilingual support requires minimal changes to this proven architecture.

---

## Recommended Solution: Enhanced Prompt Engineering

### Why NOT Build an MCP Server?

**MCP Server Approach** (what your colleague built):
- ⏱️ **2+ days development** - build entire server, define tools, write handlers
- 🔧 **High maintenance** - every schema change requires server updates
- 🎯 **Over-engineered** - excellent for complex structured operations, overkill for SELECT queries
- 💰 **Ongoing cost** - server hosting, monitoring, updates

**Enhanced Prompting Approach** (recommended):
- ⏱️ **4-6 hours development** - modify existing system
- 🔧 **Low maintenance** - update prompts when needed
- 🎯 **Right-sized** - leverages existing AI capabilities
- 💰 **Same cost** - free tier Gemini/Groq

**Decision**: Stick with current architecture, add semantic intelligence layer.

---

## Implementation Plan

### Phase 1: Semantic Alias System (1.5 hours)

**Create**: `chatbot_v2/semantic_layer.py` (NEW FILE)

Build a comprehensive mapping system for:
- French ↔ English table/column names
- Business concepts → actual database structures
- Common query patterns → correct SQL approaches

**Key Components**:

```python
# chatbot_v2/semantic_layer.py

BUSINESS_GLOSSARY = {
    # === REVENUE / CASH FLOW (CRITICAL) ===
    # This is the MAIN issue - users ask for "cash flow" but need sold_amt
    "cash flow": {
        "column": "passport.sold_amt",
        "filter": "passport.paid = 1",
        "context": "Actual revenue received from sold passports"
    },
    "flux de trésorerie": {
        "column": "passport.sold_amt",
        "filter": "passport.paid = 1",
        "context": "Revenu réel reçu des passeports vendus"
    },
    "revenue": {
        "column": "passport.sold_amt",
        "filter": "passport.paid = 1",
        "note": "NOT passport_type.price_per_user (that's listed price)"
    },
    "revenu": {
        "column": "passport.sold_amt",
        "filter": "passport.paid = 1",
        "note": "PAS passport_type.price_per_user (c'est le prix affiché)"
    },

    # === FRENCH TABLE NAMES ===
    "utilisateurs": "user",
    "utilisateur": "user",
    "clients": "user",
    "client": "user",

    "activités": "activity",
    "activité": "activity",

    "passeports": "passport",
    "passeport": "passport",

    "inscriptions": "signup",
    "inscription": "signup",

    "revenus": "income",
    "dépenses": "expense",
    "dépense": "expense",

    "sondages": "survey",
    "sondage": "survey",

    # === FRENCH COLUMN NAMES ===
    "nom": "name",
    "courriel": "email",
    "téléphone": "phone",
    "adresse": "address",
    "montant": "amount",
    "prix": "price",
    "date": "date",
    "statut": "status",
    "payé": "paid",

    # === BUSINESS CONCEPTS ===
    "customers": "user",
    "participants": "user",
    "membres": "user",
    "members": "user",

    "sales": "passport WHERE paid = 1",
    "ventes": "passport WHERE paid = 1",

    "unpaid": "paid = 0",
    "non payé": "paid = 0",

    "this month": "DATE(created_at) >= DATE('now', 'start of month')",
    "ce mois": "DATE(created_at) >= DATE('now', 'start of month')",

    "this year": "DATE(created_at) >= DATE('now', 'start of year')",
    "cette année": "DATE(created_at) >= DATE('now', 'start of year')",
}

COMMON_PATTERNS = {
    # Pattern detection for better context
    "financial_query": [
        r"(cash flow|flux.*trésorerie|revenue|revenu|sales|ventes|income)",
        "Use passport.sold_amt for actual revenue, not passport_type.price_per_user"
    ],
    "user_lookup": [
        r"(user|utilisateur|customer|client|participant|member|membre)",
        "Join through user table, include name and email"
    ],
    "payment_status": [
        r"(unpaid|non.*payé|not.*paid|pending|en.*attente)",
        "Check passport.paid = 0 or signup.paid = 0"
    ],
    "time_based": [
        r"(month|mois|year|année|week|semaine|today|aujourd'hui)",
        "Use DATE() functions with 'now' for current periods"
    ],
}

def detect_language(question: str) -> str:
    """Detect if question is in French or English"""
    french_indicators = [
        r'\b(quel|quelle|quels|quelles|comment|combien|où|quand|pourquoi)\b',
        r'\b(mon|ma|mes|notre|nos|votre|vos|leur|leurs)\b',
        r'\b(est|sont|a|ont|était|étaient)\b',
        r'\b(de|du|des|le|la|les|un|une)\b',
    ]

    for pattern in french_indicators:
        if re.search(pattern, question, re.IGNORECASE):
            return "fr"
    return "en"

def apply_semantic_aliases(question: str, language: str) -> tuple[str, list[str]]:
    """
    Apply semantic aliases to user question
    Returns: (enhanced_question, context_hints)
    """
    enhanced = question
    hints = []

    # Apply glossary replacements
    for term, replacement in BUSINESS_GLOSSARY.items():
        if re.search(r'\b' + re.escape(term) + r'\b', question, re.IGNORECASE):
            if isinstance(replacement, dict):
                hints.append(replacement['context'])
                enhanced = re.sub(
                    r'\b' + re.escape(term) + r'\b',
                    replacement['column'],
                    enhanced,
                    flags=re.IGNORECASE
                )
            else:
                enhanced = re.sub(
                    r'\b' + re.escape(term) + r'\b',
                    replacement,
                    enhanced,
                    flags=re.IGNORECASE
                )

    # Detect query pattern and add context
    for pattern_name, (regex, hint) in COMMON_PATTERNS.items():
        if re.search(regex, question, re.IGNORECASE):
            hints.append(hint)

    return enhanced, hints
```

**Testing Strategy**:
```python
# Examples to test
test_cases = [
    ("Quel est mon flux de trésorerie par activité?", "fr"),
    ("What is my cash flow per activity?", "en"),
    ("Show me unpaid customers", "en"),
    ("Montre-moi les clients non payés", "fr"),
]
```

---

### Phase 2: Enhanced System Prompt (1 hour)

**Modify**: `chatbot_v2/query_engine.py`

**Current**: `_create_system_prompt()` method (lines 261-307)

**Changes**:

1. **Add Bilingual Schema Section**:
```python
# After existing schema injection, add:
BILINGUAL COLUMN ALIASES:
  French → English
  - nom → name
  - courriel → email
  - téléphone → phone
  - montant → amount
  - payé → paid

BILINGUAL TABLE ALIASES:
  French → English
  - utilisateurs/utilisateur/clients/client → user
  - activités/activité → activity
  - passeports/passeport → passport
  - inscriptions/inscription → signup
```

2. **Add Business Context Section**:
```python
MINIPASS BUSINESS CONTEXT:
  CRITICAL - Revenue Calculations:
  - "Revenue", "cash flow", "sales" = passport.sold_amt (actual amount paid)
  - "Listed price" = passport_type.price_per_user (advertised price)
  - ALWAYS use passport.sold_amt for financial reporting
  - ALWAYS filter by passport.paid = 1 for actual revenue

  Payment Status:
  - passport.paid = 1 means paid, 0 means unpaid
  - signup.paid = 1 means paid, 0 means unpaid

  Revenue by Activity:
  - JOIN passport with activity
  - SUM(passport.sold_amt) WHERE passport.paid = 1
  - GROUP BY activity.name

  User Data:
  - ALWAYS join through user table for name/email
  - user.email is unique identifier
```

3. **Add French Examples to Few-Shot Learning**:
```python
# Add 2-3 French examples to existing 4 English examples

Q: "Quel est mon flux de trésorerie ce mois?"
A: SELECT SUM(p.sold_amt) as flux_tresorerie
   FROM passport p
   WHERE p.paid = 1
   AND DATE(p.paid_date) >= DATE('now', 'start of month')

Q: "Montre-moi les utilisateurs qui n'ont pas payé"
A: SELECT u.name, u.email, p.sold_amt
   FROM passport p
   JOIN user u ON p.user_id = u.id
   WHERE p.paid = 0
   LIMIT 100

Q: "Combien de revenus par activité cette année?"
A: SELECT a.name as activité, SUM(p.sold_amt) as revenu
   FROM passport p
   JOIN activity a ON p.activity_id = a.id
   WHERE p.paid = 1
   AND DATE(p.paid_date) >= DATE('now', 'start of year')
   GROUP BY a.id, a.name
   ORDER BY revenu DESC
```

**Code Implementation**:
```python
# In query_engine.py, modify _create_system_prompt()

def _create_system_prompt(self, schema: Dict[str, List[Dict[str, str]]],
                          language: str = "en",
                          context_hints: list[str] = None) -> str:
    """
    Create system prompt with schema, bilingual support, and business context

    Args:
        schema: Database schema from _get_database_schema()
        language: "en" or "fr"
        context_hints: Additional context from semantic layer
    """

    # ... existing schema injection code ...

    # NEW: Add bilingual aliases
    bilingual_section = self._get_bilingual_aliases_section()

    # NEW: Add business context
    business_context = self._get_business_context_section()

    # NEW: Add context hints if provided
    hints_section = ""
    if context_hints:
        hints_section = f"\nQUERY CONTEXT:\n" + "\n".join(f"- {hint}" for hint in context_hints)

    # NEW: Add language-specific examples
    if language == "fr":
        examples = self._get_french_examples()
    else:
        examples = self._get_english_examples()  # existing examples

    prompt = f"""You are an expert SQL assistant for a Minipass activity management platform.

DATABASE SCHEMA:
{schema_text}

{bilingual_section}

{business_context}

{hints_section}

RULES:
{existing_rules}

EXAMPLES:
{examples}

Now generate the SQL query for the following question."""

    return prompt
```

---

### Phase 3: Query Pre-processor (1 hour)

**Create**: `chatbot_v2/query_preprocessor.py` (NEW FILE)

This module sits between the user's question and the AI query engine.

```python
# chatbot_v2/query_preprocessor.py

from typing import Dict, List, Tuple
from .semantic_layer import detect_language, apply_semantic_aliases, BUSINESS_GLOSSARY

class QueryPreprocessor:
    """
    Pre-processes user questions before sending to AI for SQL generation.
    Handles language detection, semantic aliases, and context enrichment.
    """

    def __init__(self):
        self.supported_languages = ['en', 'fr']

    def process(self, user_question: str) -> Dict[str, any]:
        """
        Main processing pipeline

        Args:
            user_question: Raw question from user

        Returns:
            {
                'original_question': str,
                'enhanced_question': str,
                'language': 'en' | 'fr',
                'context_hints': List[str],
                'detected_intent': str,
                'confidence': float
            }
        """
        # 1. Detect language
        language = detect_language(user_question)

        # 2. Apply semantic aliases
        enhanced_question, context_hints = apply_semantic_aliases(user_question, language)

        # 3. Detect query intent
        intent = self._detect_intent(user_question)

        # 4. Add intent-specific hints
        if intent == 'financial':
            context_hints.append("IMPORTANT: Use passport.sold_amt for revenue, not passport_type.price_per_user")
        elif intent == 'user_lookup':
            context_hints.append("Include user.name and user.email in results")
        elif intent == 'payment_status':
            context_hints.append("Check passport.paid or signup.paid (1=paid, 0=unpaid)")

        return {
            'original_question': user_question,
            'enhanced_question': enhanced_question,
            'language': language,
            'context_hints': context_hints,
            'detected_intent': intent,
            'confidence': self._calculate_confidence(user_question, enhanced_question)
        }

    def _detect_intent(self, question: str) -> str:
        """Classify query intent"""
        question_lower = question.lower()

        if any(term in question_lower for term in
               ['cash flow', 'flux', 'revenue', 'revenu', 'sales', 'ventes', 'income']):
            return 'financial'

        if any(term in question_lower for term in
               ['user', 'utilisateur', 'customer', 'client', 'participant', 'member']):
            return 'user_lookup'

        if any(term in question_lower for term in
               ['unpaid', 'non payé', 'pending', 'attente', 'not paid']):
            return 'payment_status'

        if any(term in question_lower for term in
               ['activity', 'activité', 'event', 'événement']):
            return 'activity_query'

        return 'general'

    def _calculate_confidence(self, original: str, enhanced: str) -> float:
        """
        Calculate confidence that we understood the query correctly
        Higher confidence if we applied aliases and detected intent
        """
        if original == enhanced:
            return 0.5  # No aliases applied

        # More changes = more confident we understood
        changes = sum(1 for a, b in zip(original.split(), enhanced.split()) if a != b)
        return min(0.5 + (changes * 0.1), 1.0)
```

---

### Phase 4: Integration & Testing (1.5 hours)

**Modify**: `chatbot_v2/routes_simple.py`

**Integration Point**: `/chatbot/ask` endpoint (line 76)

```python
# chatbot_v2/routes_simple.py

from .query_preprocessor import QueryPreprocessor

preprocessor = QueryPreprocessor()

@chatbot_bp.route('/chatbot/ask', methods=['POST'])
def ask_question():
    """Process user question with bilingual support"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()

        # ... existing validation ...

        # NEW: Pre-process question
        processed = preprocessor.process(user_question)

        logger.info(f"Query preprocessing: {processed}")

        # NEW: Use enhanced question for SQL generation
        result = query_engine.process_question(
            question=processed['enhanced_question'],
            language=processed['language'],
            context_hints=processed['context_hints']
        )

        # NEW: Add language info to response
        result['language'] = processed['language']
        result['original_question'] = processed['original_question']

        # ... existing conversation saving ...

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in chatbot ask: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

**Modify**: `chatbot_v2/query_engine.py`

Update `process_question()` method signature:

```python
def process_question(self,
                     question: str,
                     language: str = "en",
                     context_hints: List[str] = None) -> Dict[str, any]:
    """
    Process natural language question into SQL query

    Args:
        question: Enhanced question from preprocessor
        language: Detected language ("en" or "fr")
        context_hints: Additional context from semantic analysis
    """
    # Generate system prompt with new parameters
    system_prompt = self._create_system_prompt(
        schema=self._get_database_schema(),
        language=language,
        context_hints=context_hints
    )

    # ... rest of existing logic ...
```

**Create**: `test/test_chatbot_bilingual.py` (NEW FILE)

Comprehensive test suite:

```python
import unittest
from chatbot_v2.query_preprocessor import QueryPreprocessor
from chatbot_v2.semantic_layer import detect_language, apply_semantic_aliases

class TestBilingualChatbot(unittest.TestCase):
    """Test bilingual chatbot functionality"""

    def setUp(self):
        self.preprocessor = QueryPreprocessor()

    # === LANGUAGE DETECTION TESTS ===

    def test_detect_french_question(self):
        """Should detect French questions"""
        questions = [
            "Quel est mon flux de trésorerie?",
            "Combien d'utilisateurs?",
            "Montre-moi les activités",
        ]
        for q in questions:
            self.assertEqual(detect_language(q), "fr", f"Failed for: {q}")

    def test_detect_english_question(self):
        """Should detect English questions"""
        questions = [
            "What is my cash flow?",
            "Show me all users",
            "How many activities?",
        ]
        for q in questions:
            self.assertEqual(detect_language(q), "en", f"Failed for: {q}")

    # === SEMANTIC ALIAS TESTS ===

    def test_cash_flow_alias_french(self):
        """Should map 'flux de trésorerie' to correct column"""
        question = "Quel est mon flux de trésorerie?"
        enhanced, hints = apply_semantic_aliases(question, "fr")

        self.assertIn("passport.sold_amt", enhanced)
        self.assertTrue(any("revenue" in h.lower() for h in hints))

    def test_cash_flow_alias_english(self):
        """Should map 'cash flow' to correct column"""
        question = "What is my cash flow per activity?"
        enhanced, hints = apply_semantic_aliases(question, "en")

        self.assertIn("passport.sold_amt", enhanced)
        self.assertTrue(any("revenue" in h.lower() for h in hints))

    def test_table_name_aliases_french(self):
        """Should translate French table names"""
        test_cases = [
            ("utilisateurs", "user"),
            ("activités", "activity"),
            ("passeports", "passport"),
            ("inscriptions", "signup"),
        ]
        for french, english in test_cases:
            question = f"Montre-moi les {french}"
            enhanced, _ = apply_semantic_aliases(question, "fr")
            self.assertIn(english, enhanced)

    # === INTENT DETECTION TESTS ===

    def test_financial_intent_detection(self):
        """Should detect financial queries"""
        questions = [
            "What is my revenue?",
            "Quel est mon revenu?",
            "Show me sales this month",
            "Flux de trésorerie par activité",
        ]
        for q in questions:
            result = self.preprocessor.process(q)
            self.assertEqual(result['detected_intent'], 'financial')

    def test_user_lookup_intent(self):
        """Should detect user lookup queries"""
        questions = [
            "Show me all customers",
            "Montre-moi les utilisateurs",
            "List all participants",
            "Qui sont mes clients?",
        ]
        for q in questions:
            result = self.preprocessor.process(q)
            self.assertEqual(result['detected_intent'], 'user_lookup')

    # === INTEGRATION TESTS ===

    def test_preprocessing_pipeline_french(self):
        """Test complete preprocessing for French question"""
        question = "Quel est mon flux de trésorerie par activité ce mois?"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'fr')
        self.assertEqual(result['detected_intent'], 'financial')
        self.assertIn("passport.sold_amt", result['enhanced_question'])
        self.assertTrue(len(result['context_hints']) > 0)
        self.assertGreater(result['confidence'], 0.5)

    def test_preprocessing_pipeline_english(self):
        """Test complete preprocessing for English question"""
        question = "What is my cash flow per activity this month?"
        result = self.preprocessor.process(question)

        self.assertEqual(result['language'], 'en')
        self.assertEqual(result['detected_intent'], 'financial')
        self.assertIn("passport.sold_amt", result['enhanced_question'])
        self.assertTrue(len(result['context_hints']) > 0)

    # === REGRESSION TESTS (Your Specific Issues) ===

    def test_cash_flow_maps_to_sold_amt_not_price(self):
        """
        CRITICAL: Ensure "cash flow" queries use sold_amt, not price_per_user
        This addresses your reported issue
        """
        questions = [
            "What is my cash flow?",
            "Quel est mon flux de trésorerie?",
            "Show me revenue",
            "Montre-moi le revenu",
        ]
        for q in questions:
            result = self.preprocessor.process(q)
            hints_text = " ".join(result['context_hints']).lower()

            # Should mention sold_amt
            self.assertTrue(
                "sold_amt" in result['enhanced_question'] or "sold_amt" in hints_text,
                f"Failed for: {q}"
            )

            # Should NOT suggest price_per_user
            self.assertNotIn("price_per_user", result['enhanced_question'])

    def test_french_queries_dont_fail(self):
        """
        Ensure French queries are properly processed
        This addresses your reported issue
        """
        french_questions = [
            "Quel est mon flux de trésorerie?",
            "Montre-moi les utilisateurs non payés",
            "Combien de passeports vendus?",
            "Quelles sont mes activités?",
        ]

        for q in french_questions:
            result = self.preprocessor.process(q)
            self.assertEqual(result['language'], 'fr')
            self.assertIsNotNone(result['enhanced_question'])
            self.assertGreater(len(result['context_hints']), 0)

if __name__ == '__main__':
    unittest.main()
```

**Run Tests**:
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
source venv/bin/activate
python -m unittest test.test_chatbot_bilingual -v
```

---

### Phase 5: Documentation & Monitoring (0.5-1 hour)

**Create**: `docs/CHATBOT_USAGE.md` (NEW FILE)

User-facing documentation:

```markdown
# Minipass AI Chatbot - User Guide

## Supported Languages

The chatbot supports questions in **English** and **French**.

## Query Examples

### Financial Queries

**English**:
- "What is my cash flow this month?"
- "Show me revenue per activity"
- "How much money did I make this year?"

**French**:
- "Quel est mon flux de trésorerie ce mois?"
- "Montre-moi le revenu par activité"
- "Combien d'argent ai-je gagné cette année?"

### User Queries

**English**:
- "Show me all customers"
- "List unpaid users"
- "Who signed up for Golf 2025?"

**French**:
- "Montre-moi tous les clients"
- "Liste des utilisateurs non payés"
- "Qui s'est inscrit au Golf 2025?"

### Activity Queries

**English**:
- "What are my most popular activities?"
- "Show me all events this summer"

**French**:
- "Quelles sont mes activités les plus populaires?"
- "Montre-moi tous les événements cet été"

## Business Terms Reference

### Revenue / Cash Flow
- **What it means**: Actual money received from sold passports
- **Database column**: `passport.sold_amt`
- **Important**: This is NOT the listed price (`passport_type.price_per_user`)

### Payment Status
- **Paid**: `passport.paid = 1` or `signup.paid = 1`
- **Unpaid**: `passport.paid = 0` or `signup.paid = 0`

### Time Periods
- "This month" / "ce mois": Current calendar month
- "This year" / "cette année": Current calendar year
- "Today" / "aujourd'hui": Current date

## Bilingual Terms

| English | French | Database Column |
|---------|--------|----------------|
| Users / Customers | Utilisateurs / Clients | `user` table |
| Activities | Activités | `activity` table |
| Passports | Passeports | `passport` table |
| Signups | Inscriptions | `signup` table |
| Revenue | Revenu | `passport.sold_amt` |
| Cash Flow | Flux de trésorerie | `passport.sold_amt` |
| Name | Nom | `name` column |
| Email | Courriel | `email` column |
| Amount | Montant | `amount` column |
| Paid | Payé | `paid` column |

## Troubleshooting

### "No results found"
- Check if data exists for the time period
- Try broadening your query (e.g., remove date filters)

### "Query error"
- Rephrase your question more simply
- Use examples from this guide as templates

### Wrong results
- Be specific about time periods
- Specify which activity if asking about specific events

## Technical Notes

- Maximum 1000 rows returned per query
- Read-only access (cannot modify data)
- Queries timeout after 30 seconds
- All financial amounts in CAD cents
```

**Modify**: `models.py`

Add language tracking to ChatMessage:

```python
# In models.py, add to ChatMessage model (around line 360)

class ChatMessage(db.Model):
    # ... existing fields ...

    # NEW: Track language for analytics
    language = db.Column(db.String(2), default='en')  # 'en' or 'fr'

    # NEW: Track preprocessing metadata
    preprocessing_metadata = db.Column(db.JSON, nullable=True)
    # Will store: {"detected_intent": "financial", "confidence": 0.85, etc.}
```

**Modify**: `models.py`

Add language tracking to QueryLog:

```python
# In models.py, add to QueryLog model (around line 395)

class QueryLog(db.Model):
    # ... existing fields ...

    # NEW: Track language
    language = db.Column(db.String(2), default='en')

    # NEW: Track semantic preprocessing
    semantic_enhancement = db.Column(db.Boolean, default=False)
    detected_intent = db.Column(db.String(50), nullable=True)
```

**Create Migration**:
```bash
cd /home/kdresdell/Documents/DEV/minipass_env/app
flask db migrate -m "Add bilingual support to chatbot tables"
flask db upgrade
```

---

## Deployment Checklist

### Pre-Deployment Testing
- [ ] Run unit tests: `python -m unittest test.test_chatbot_bilingual -v`
- [ ] Test French queries in chatbot UI
- [ ] Test English queries (ensure no regression)
- [ ] Test "cash flow" query specifically (your reported issue)
- [ ] Test wrong table/column selection scenarios
- [ ] Verify QueryLog captures language correctly

### Code Review
- [ ] Review semantic_layer.py mappings for completeness
- [ ] Verify query_preprocessor.py handles edge cases
- [ ] Check query_engine.py prompt enhancements
- [ ] Ensure routes_simple.py integration is clean

### Database Migration
- [ ] Run migration to add language columns
- [ ] Verify existing data not affected
- [ ] Check indexes on new columns

### Documentation
- [ ] User guide (CHATBOT_USAGE.md) is accurate
- [ ] Internal docs updated for future developers
- [ ] Example queries tested and verified

### Monitoring
- [ ] QueryLog tracking language distribution
- [ ] Monitor query success rate (French vs English)
- [ ] Track semantic_enhancement usage
- [ ] Watch for new error patterns

---

## Success Metrics

### Primary Goals (Your Reported Issues)
1. **French queries work**: ≥95% success rate for French questions
2. **Correct table/column selection**: "cash flow" → `passport.sold_amt` 100% of the time

### Secondary Goals
1. **User adoption**: ≥30% of queries in French (if French-speaking admins)
2. **Query accuracy**: ≥90% of queries return expected results
3. **No performance degradation**: Query processing time <2 seconds
4. **No cost increase**: Stay within Gemini/Groq free tiers

### Monitoring Queries

Check language distribution:
```sql
SELECT language, COUNT(*) as count,
       AVG(execution_time_ms) as avg_time,
       SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
FROM query_log
WHERE created_at >= DATE('now', '-7 days')
GROUP BY language;
```

Check semantic enhancement impact:
```sql
SELECT semantic_enhancement, detected_intent,
       COUNT(*) as count,
       AVG(execution_time_ms) as avg_time,
       SUM(CASE WHEN execution_status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
FROM query_log
WHERE created_at >= DATE('now', '-7 days')
GROUP BY semantic_enhancement, detected_intent;
```

---

## Future Enhancements (Post-MVP)

### Phase 6: Context-Aware Conversations (Future)
- Use conversation history for follow-up questions
- "What about last month?" after asking about current month
- Store context in ChatConversation metadata

### Phase 7: Query Templates (Future)
- Pre-built queries for common reports
- "Show me my standard financial report"
- Customizable templates per admin

### Phase 8: Advanced Analytics (Future)
- Chart generation based on query results
- Export to CSV/PDF
- Scheduled reports via email

### Phase 9: Additional Languages (Future)
- Spanish support (if needed for expansion)
- Use same semantic layer architecture

---

## Comparison: Enhanced Prompting vs MCP Server

| Aspect | Enhanced Prompting (This Plan) | MCP Server (Alternative) |
|--------|-------------------------------|--------------------------|
| **Development Time** | 4-6 hours | 2-3 days |
| **Maintenance** | Update prompts | Update server code + tools |
| **Flexibility** | High - handles unexpected queries | Medium - fixed tool set |
| **Precision** | 85-90% (AI-dependent) | 95-98% (deterministic) |
| **Cost** | $0 (free tier) | $0 + hosting if needed |
| **Complexity** | Low - builds on existing | High - new infrastructure |
| **Testing** | Unit tests + manual | Unit tests + integration + E2E |
| **Best For** | Natural language queries | Structured database operations |
| **Your Use Case** | ✅ **RECOMMENDED** | ❌ Over-engineered |

**Verdict**: For Minipass chatbot, enhanced prompting provides 90% of the benefits with 20% of the effort.

---

## Appendix A: File Changes Summary

### New Files (3)
1. `chatbot_v2/semantic_layer.py` (~200 lines)
2. `chatbot_v2/query_preprocessor.py` (~150 lines)
3. `test/test_chatbot_bilingual.py` (~250 lines)
4. `docs/CHATBOT_USAGE.md` (~150 lines)

### Modified Files (3)
1. `chatbot_v2/query_engine.py`
   - Add `language` and `context_hints` parameters to `process_question()`
   - Modify `_create_system_prompt()` to inject bilingual aliases + business context
   - Add `_get_bilingual_aliases_section()` method
   - Add `_get_business_context_section()` method
   - Add `_get_french_examples()` method

2. `chatbot_v2/routes_simple.py`
   - Import `QueryPreprocessor`
   - Add preprocessing step in `/chatbot/ask` endpoint
   - Pass language + hints to query engine

3. `models.py`
   - Add `language` column to `ChatMessage`
   - Add `preprocessing_metadata` JSON column to `ChatMessage`
   - Add `language`, `semantic_enhancement`, `detected_intent` columns to `QueryLog`

### Database Migration
- Migration file: `migrations/versions/XXXX_add_bilingual_support.py`

---

## Appendix B: Cost Analysis

### Current Costs
- **Gemini API**: $0/month (free tier: 1,500 requests/day)
- **Groq API**: $0/month (free tier: 14,400 requests/day)
- **Total**: $0/month

### After Enhancement
- **Same**: Still using free tier
- **No additional costs**: Semantic layer runs locally
- **Potential future**: If usage exceeds free tier, paid plans available

**Recommendation**: Monitor ChatUsage table for daily query counts.

---

## Appendix C: Risk Assessment

### Low Risk
- ✅ **Backward compatibility**: English queries unchanged
- ✅ **Security**: No changes to security.py validation
- ✅ **Performance**: Preprocessing adds <100ms
- ✅ **Data**: Read-only, no data modification

### Medium Risk
- ⚠️ **AI accuracy**: Depends on Gemini/Groq understanding prompts
  - *Mitigation*: Extensive testing, fallback to simpler prompt
- ⚠️ **French translation quality**: Aliases may not cover all terms
  - *Mitigation*: Iterative improvement, user feedback

### High Risk
- ❌ **None identified**

**Overall Risk**: **LOW** - Safe to proceed with implementation.

---

## Questions & Support

**For Developers**:
- See code comments in `chatbot_v2/semantic_layer.py`
- Run tests: `python -m unittest test.test_chatbot_bilingual -v`
- Check logs: `logs/chatbot.log`

**For Users**:
- See `docs/CHATBOT_USAGE.md`
- Try example queries from this guide
- Report issues to admin dashboard

---

**END OF PLAN**

---

## Next Steps

1. **Review this plan** - provide feedback, identify gaps
2. **Get approval** - confirm approach and effort estimate
3. **Implement Phase 1** - build semantic layer
4. **Test iteratively** - verify each phase before moving to next
5. **Deploy to production** - after all tests pass
6. **Monitor metrics** - track success rate and user adoption

**Estimated Timeline**: 4-6 hours over 1-2 days
