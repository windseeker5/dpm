# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minipass is a Flask-based SAAS PWA application for end-to-end activities management including registrations, payments, digital passes, and activity tracking. The application uses Tabler.io for UI components and supports multiple AI providers for chatbot functionality.

## Key Development Commands

### IMPORTANT: Development Server Status
**THE FLASK SERVER IS ALREADY RUNNING IN DEBUG MODE ON PORT 8890**
- DO NOT start a new Flask server with `python app.py`
- DO NOT attempt to kill or restart the existing server
- The server is ALWAYS available at http://127.0.0.1:8890
- Simply navigate to the URL to test changes - the debug server auto-reloads

### Running the Application (Only if server is not already running)
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (port 8890) - ONLY IF NOT ALREADY RUNNING
python app.py
```

### Database Management
```bash
# Initialize database
flask db init

# Create migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade
```

### Development Server Access
- URL: http://127.0.0.1:8890
- Login: kdresdell@gmail.com / admin123
- Style Guide: http://127.0.0.1:8890/style-guide

## Application Architecture

### Core Components

**Main Application (app.py)**
- Flask application initialization and route definitions
- Authentication and session management
- Activity, signup, and passport management
- Survey system integration
- Payment processing (Stripe integration)
- Email notification system

**Data Models (models.py)**
- SQLAlchemy models with timezone-aware datetime handling
- Key entities: User, Activity, Passport, PassportType, Signup, Survey, Expense, Income
- Relationship mappings between activities, users, and passes
- Admin action logging and audit trails

**Chatbot System (chatbot_v2/)**
- Modular AI provider architecture supporting Ollama, OpenAI, and Anthropic
- Conversation management with token tracking
- Security and rate limiting implementation
- Query engine for context-aware responses

### Frontend Architecture
- Jinja2 templates with base template inheritance
- Tabler.io Bootstrap 5 components (pre-installed in static/tabler/)
- Mobile-first responsive design
- PWA-ready implementation
- TinyMCE for rich text editing

### Key Integrations
- **Stripe**: Payment processing for passes and activities
- **QR Code Generation**: For digital pass validation
- **Email System**: Flask-Mail for notifications with HTML templates
- **AI Providers**: Ollama (local), OpenAI, and Anthropic APIs
- **APScheduler**: Background job processing for reminders

## UI Development Guidelines

When working on UI components:
1. Use ONLY Tabler.io components - no custom CSS frameworks
2. Follow conventions from /style-guide endpoint
3. Maintain Flask/Jinja2 template inheritance structure
4. Ensure mobile-first responsive design
5. Test all changes using Playwright MCP on development server

## Database Schema Notes

The application uses PostgreSQL with SQLAlchemy ORM. Key relationships:
- Activities have multiple PassportTypes (pricing tiers)
- Users can have multiple Signups and Passports
- Passports track redemptions and remaining sessions
- Survey system links to activities for feedback collection
- Financial tracking through Expense and Income models

## Important File Locations

- Templates: `/templates/` - Jinja2 HTML templates
- Static Assets: `/static/` - CSS, JS, images, Tabler.io components
- Database Migrations: `/migrations/versions/` - Alembic migration files
- Email Templates: `/templates/email_templates/` - HTML email layouts
- Uploads: `/uploads/` - User-uploaded files (receipts, images)