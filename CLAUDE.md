# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

**IMPORTANT: Flask server is always running on `localhost:5000` in debug mode.**

### Infrastructure Status
- Flask Server: `localhost:5000` ✅ Always running in debug mode
- MCP Playwright: ✅ Available for browser testing
- Database: SQLite (`instance/minipass.db`) ✅ Configured
- Virtual Environment: `venv/` ✅ Activated with all dependencies

### Required Reading for All Work
🚨 **MANDATORY:** Read `docs/CONSTRAINTS.md` before starting any task
- Main agents are ORCHESTRATORS only - delegate to specialists
- Specialist agents must acknowledge constraints before coding
- Use existing servers (Flask on 5000, MCP Playwright)
- Follow Python-first development approach

## Common Commands

### Running Tests
```bash
# Unit tests (using unittest framework)
source venv/bin/activate
python -m unittest test.test_kpi_data -v
python test/test_kpi_data.py

# MCP Playwright tests (for UI testing)
# Use MCP Playwright browser tools directly in Claude Code
```

### Development
```bash
# Virtual environment (if needed)
source venv/bin/activate

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Access Flask app (always running on port 5000)
# No need to start - already running in debug mode
curl http://localhost:5000/
```

## Architecture Overview

### Core Application Structure
- **Main App**: `app.py` - Single-file Flask application (~66k lines)
- **Models**: `models.py` - SQLAlchemy models for all entities
- **Utils**: `utils.py` - Business logic and helper functions
- **Templates**: `templates/` - Jinja2 templates using Tabler.io CSS framework

### Key Models & Entities
- **Admin**: Administrator accounts with authentication
- **Activity**: Core business entity (sports leagues, fitness classes, etc.)
- **Passport/PassportType**: Digital passes for activities
- **Signup**: Registration process for activities
- **User**: End users who purchase and redeem passes
- **Income**: Financial tracking and payment matching
- **Survey/SurveyTemplate**: Customer feedback collection
- **ChatConversation/ChatMessage**: AI chatbot for data queries

### Business Logic Architecture
- **Registration Flow**: Activity → PassportType → Signup → Payment → Passport
- **Payment Matching**: Automated email parsing to match e-transfers with signups
- **Digital Passes**: QR code generation and redemption tracking
- **KPI Dashboard**: Real-time metrics using `get_kpi_data()` function
- **Survey System**: Template-based feedback collection with 3-click deployment

### API Structure
- **Blueprints**: `api/backup.py`, `api/settings.py`
- **Chatbot**: `chatbot_v2/` - AI-powered business intelligence queries
- **Email Templates**: `templates/email_templates/` - Automated branded communications

### Frontend Architecture
- **Server-side rendering** with Jinja2 templates
- **Tabler.io CSS framework** for consistent UI components
- **Minimal JavaScript** (<10 lines per function constraint)
- **Progressive Web App** features for mobile experience

### 🚨 CRITICAL UI RULES - READ BEFORE ANY TABLE/CSS WORK

**TABLE STYLING RULES (NON-NEGOTIABLE):**
1. **NO HOVER EFFECTS** - No transform, translateY, scale, or shadow changes on hover
2. **NO ANIMATIONS** - No fancy CSS transitions or effects on cards/tables
3. **PLAIN WHITE CARDS** - Simple `background-color: #fff !important;` only
4. **REFERENCE PAGES** - When creating ANY new table page, copy CSS from:
   - `templates/passports.html`
   - `templates/signups.html`
5. **NEVER ADD:**
   - `transform: translateY(-2px)` on hover
   - `box-shadow` changes on hover
   - `transition: all 0.3s ease` effects
   - `backdrop-filter: blur()` effects
   - Gradient backgrounds (use plain white)

**If you add ANY hover effects or animations to tables, you WILL be told to remove them.**

### Database Design
- **SQLite** database with timezone-aware datetime handling
- **Migration system** using Flask-Migrate
- **Backup system** with automated daily backups in `instance/`

### Technology Constraints
- **Container Limits**: <512MB RAM, <10s startup time
- **Python-First Policy**: Business logic in Python, minimal client-side JavaScript
- **Testing Required**: Unit tests + MCP Playwright integration tests
- **Email Integration**: Custom email parsing for Canadian e-transfer automation

## Development Workflow

### For Main Orchestrator Agents
1. Read `docs/CONSTRAINTS.md` and `docs/PRD.md` for context
2. Plan tasks and delegate to appropriate specialist agents
3. Never code directly - orchestrate only

### For Specialist Agents
1. Acknowledge constraints checklist before starting
2. Use existing Flask server on port 5000
3. Write unit tests for new functionality
4. Follow Python-first development approach
5. Keep JavaScript minimal and functional

### Testing Strategy
- **Unit Tests**: Python unittest framework in `test/` directory
- **Integration Tests**: MCP Playwright for browser-based testing
- **Manual Testing**: Use running Flask server on localhost:5000

## Key Business Context

Minipass is a SaaS platform for activity management targeting two markets:
1. **Activity Managers**: Sports leagues, fitness classes, tournaments
2. **Small Business Loyalty**: Coffee shops, salons, local services

**Unique Features**:
- Automated Canadian e-transfer payment matching
- Professional branded email communications
- QR code digital pass system
- AI business intelligence chatbot
- 3-click survey deployment system

**Pricing Tiers**: $10 Starter → $35 Professional → $50 Enterprise
**Architecture**: One Docker container per customer
**Target Launch**: September 2025