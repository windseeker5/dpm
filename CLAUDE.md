# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

CONSTRAINTS - DO NOT:
  - Create ANY new files
  - Add ANY global event listeners
  - Touch ANY search functionality
  - Touch ANY filter functionality  
  - Use WeakMap, RequestQueue, or any complex patterns
  - Add "monitoring", "performance", or "enterprise" features
  - Write more than 50 lines


Only change what's necessary to fix this issue. Don't refactor working code around it. 

Always use the best competent agent for the task. Do not start a flask server. We already have one up and running for debug on port 8890.

Always test your task using playwrights mcp server and username = kdresdell@gmail.com and password = admin123

Reference: @Developmet_Guidelines.md [Bug Fix Protocol]


## Architecture Overview

### Core Structure
This is a Flask-based business management application (Minipass) that handles:
- **Passport Management**: Digitized passes with QR codes, payments, and tracking
- **Activity Tracking**: Member activities with expenses and income
- **Survey System**: Customer surveys with template management
- **AI Analytics Chatbot**: Multi-provider AI chatbot (OpenAI, Anthropic, Ollama)
- **Email Integration**: IMAP/SMTP for automated payment processing and notifications

### Key Components
- **Main Application**: `app.py` - Primary Flask app with all route handlers
- **Database Models**: `models.py` - SQLAlchemy models for all entities
- **Utilities**: `utils.py` - Email processing, QR generation, payment matching
- **Security**: `decorators.py` - Rate limiting, admin auth, API logging
- **AI Chatbot**: `chatbot_v2/` - Modular AI chatbot with provider abstraction
- **KPI Components**: `components/kpi_card.py` - Reusable dashboard metrics

### Database Architecture
- Uses SQLite with timezone-aware datetime handling
- Key models: Admin, Passport, Activity, Survey, Organization, ChatConversation
- Migration system in `migrations/` directory with version tracking
- Backward compatibility maintained for removed UI fields via `REMOVED_FIELD_DEFAULTS`

### Frontend Architecture
- Uses Tabler.io CSS framework for responsive UI
- Custom CSS in `static/css/` for component-specific styling
- JavaScript components in `static/js/` (dropdown fixes, chatbot, unified settings)
- Templates in `templates/` with Jinja2 templating

### AI Chatbot System (chatbot_v2/)
- Multi-provider support: OpenAI, Anthropic Claude, Ollama
- Database query integration for analytics
- Conversation tracking and usage monitoring
- Security-focused with query sanitization

### Email System
- IMAP integration for automated payment processing from Gmail
- Email template compilation system in `templates/email_templates/`
- Automated reminder system and notification workflows
- Image inlining and premailer for email compatibility

### Security Features
- CSRF protection via Flask-WTF
- Rate limiting decorators
- Admin authentication system
- API call logging and audit trails
- Secure file handling with werkzeug

### Performance Optimizations
- Response caching decorators
- Background job scheduling with APScheduler
- Optimized database queries with SQLAlchemy
- Static asset organization for efficient loading

## Development Notes

### Key Dependencies
- **Flask Stack**: Flask, SQLAlchemy, Migrate, WTF, Mail
- **AI/ML**: OpenAI, Anthropic, Ollama clients, pandas, matplotlib
- **Payments**: Stripe integration
- **Email**: premailer for template processing
- **QR Codes**: qrcode[pil] for pass generation
- **Fuzzy Matching**: rapidfuzz for payment matching

### Important Patterns
- All datetime handling uses UTC with timezone conversion via `utc_to_local()`
- Email templates are compiled from source with inline image processing
- KPI cards use standardized component system for consistency
- Security decorators are applied to sensitive routes
- Database migrations maintain backward compatibility

### Development Environment
- Uses Python virtual environment
- Environment variables loaded via python-dotenv
- Static files served directly in development
- Database auto-creates on first run

### File Upload Handling
- Activity images stored in `static/uploads/activity_images/`
- Avatar uploads in `static/uploads/avatars/`
- Receipt files in expense tracking
- Secure filename processing with werkzeug

This is a production business application with customer data, so maintain security best practices and thorough testing for all changes.