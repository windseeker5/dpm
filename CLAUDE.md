# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minipass is a Flask-based SAAS PWA application for end-to-end activities management including registrations, payments, digital passes, and activity tracking. The application uses Tabler.io for UI components and supports multiple AI providers for chatbot functionality.

## Critical Development Notes

### ⚠️ FLASK SERVER STATUS
**THE FLASK SERVER IS ALREADY RUNNING IN DEBUG MODE ON PORT 8890**
- **NEVER** start a new Flask server with `python app.py`
- **NEVER** attempt to kill or restart the existing server
- The server is ALWAYS available at http://127.0.0.1:8890
- Debug mode auto-reloads on file changes
- To test changes: Simply navigate to http://127.0.0.1:8890

### Development Access
- **URL**: http://127.0.0.1:8890
- **Login**: kdresdell@gmail.com / admin123
- **Style Guide**: http://127.0.0.1:8890/style-guide (Tabler.io component reference)

## Development Commands

### Virtual Environment & Dependencies
```bash
# Activate virtual environment (required before any Python commands)
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run development server (port 8890) - ONLY IF NOT ALREADY RUNNING
python app.py
```

### Database Operations
```bash
# Initialize database (first time only)
flask db init

# Create new migration after model changes
flask db migrate -m "description of changes"

# Apply pending migrations
flask db upgrade

# View migration history
flask db history

# Downgrade to previous migration
flask db downgrade
```

### Testing & Code Quality
**Note**: No testing framework or linting tools are currently configured.
If implementing tests or linting, update this section with the appropriate commands.

## High-Level Architecture

### Core Stack
- **Backend**: Flask with SQLAlchemy ORM (SQLite database in `instance/minipass.db`)
- **Frontend**: Jinja2 templates + Tabler.io components (Bootstrap 5)
- **Authentication**: Session-based with bcrypt password hashing
- **Configuration**: Environment-based config in `config.py`

### Key Application Files

**app.py** (3980 lines) - Main application entry point
- Routes for activities, signups, passports, surveys, and admin functions
- Stripe payment integration endpoints
- Email notification triggers
- QR code generation and validation
- Runs on port 8890 in debug mode

**models.py** - SQLAlchemy data models
- User authentication and profile management
- Activity lifecycle (creation, scheduling, capacity tracking)
- PassportType: Pricing tiers for activities
- Passport: Digital passes with redemption tracking
- Signup: Registration and payment status
- Survey/SurveyResponse: Feedback collection
- Expense/Income: Financial tracking per activity
- AdminLog: Audit trail for admin actions

### Chatbot System (`chatbot_v2/`)
Multi-provider AI chatbot with modular architecture:
- **ai_providers.py**: Provider factory and base classes
- **providers/**: Ollama, OpenAI, Anthropic implementations
- **conversation.py**: Chat history and token management
- **security.py**: Rate limiting and input validation
- **routes.py**: API endpoints for chat interface

### Key Integrations
- **Stripe API**: Payment processing for passes and activities
- **QR Code**: Digital pass generation and validation (`qrcode` library)
- **Email**: Flask-Mail with HTML templates in `templates/email_templates/`
- **Rich Text**: TinyMCE editor (static files in `static/tinymce/`)
- **Scheduling**: APScheduler for automated reminders
- **AI Models**: Support for Ollama (local), OpenAI, and Anthropic

## UI Development Guidelines

### Tabler.io Component Usage
- **MANDATORY**: Use ONLY Tabler.io components - already installed in `static/tabler/`
- **Reference**: http://127.0.0.1:8890/style-guide for live component examples
- **CSS Classes**: Use Tabler's utility classes (e.g., `card`, `btn`, `avatar`, `badge`)
- **Icons**: Tabler icons available in `static/tabler/icons/`
- **No Custom Frameworks**: Do not add Bootstrap, Tailwind, or other CSS libraries

### Template Structure
- **Base Template**: All pages extend `templates/base.html`
- **Partials**: Reusable components in `templates/partials/`
- **Mobile-First**: Test responsive design at all breakpoints
- **Testing**: Use Playwright MCP to test on http://127.0.0.1:8890

## Database Schema

### Core Relationships
```
User (1) ──> (N) Signup
User (1) ──> (N) Passport
Activity (1) ──> (N) PassportType (pricing tiers)
Activity (1) ──> (N) Signup
Activity (1) ──> (N) Survey
PassportType (1) ──> (N) Passport
Passport (1) ──> (N) Redemptions (tracked in passport.used_sessions)
```

### Key Model Features
- **Soft Deletes**: Activities use `active` flag instead of deletion
- **Timezone Aware**: All datetime fields use UTC with pytz
- **Audit Trail**: AdminLog tracks all admin actions
- **Financial Tracking**: Expense/Income models link to activities

## Project Structure

```
/app/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy models
├── config.py                 # Configuration settings
├── chatbot_v2/              # AI chatbot system
├── templates/               # Jinja2 templates
│   ├── base.html           # Base template
│   ├── partials/           # Reusable components
│   └── email_templates/    # Email HTML templates
├── static/                  # Static assets
│   ├── tabler/             # Tabler.io framework
│   ├── tinymce/            # Rich text editor
│   └── uploads/            # User uploads
└── migrations/              # Database migrations
```