# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard Workflow

1. Understand the Problem First. Begin by reading the relevant source code and thinking through the problem. Then, write a clear plan in projectplan.md.

2. Write an Action Plan projectplan.md that include a checklist of concrete steps to implement the feature. You will tick off these steps as you complete them.

3. Review the Plan Before Starting. Before writing any code, contact me to review and approve the action plan.

4. Create Pytest unit tests for all new features — including functions, classes, routes, etc. If you modify existing logic, update the related tests accordingly.

 - All tests must live in the /tests directory. do not delete the test files
 - Include at least:
   - One success case
   - One edge case
   - One failure case

5. Execute the Plan. Begin coding based on the approved action plan. Check off each completed action in projectplan.md as you go.

6. Explain Your Changes. After each stage of implementation, write a clear explanation of the changes made and why.

7. Keep it Simple. Prioritize simplicity.
 - Break down tasks into small, manageable changes.
 - Each modification should have minimal impact on the overall codebase.

8. Document Revisions. At the end of each feature or task, add a Revision section to projectplan.md summarizing:
 - What was implemented or changed
 - Any key decisions or notes for future work

## Project Overview

Minipass is a mobile-first Activities and Digital Passport Management system built with Flask. It enables organizations and small businesses to easily manage activities, digital passport, signups, and payments.

Minipass offers an intuitive interface optimized for mobile devices, allowing users to manage everything on the go.

## Tech Stack

- **Flask** - Python web framework with SQLAlchemy ORM
- **SQLite** - Database (`instance/minipass.db`)
- **Tabler.io** - UI framework for admin dashboard based on Bootstrap and ApexJS
- **Stripe** - Payment processing
- **Python** with comprehensive dependencies in `requirements.txt`

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test files
python tests/test_flask_startup.py
python tests/test_survey_system.py
python tests/test_chatbot_infrastructure.py

# Run database validation
python tests/validate_fix.py
```

### Database Management
```bash
# Initialize database
python migrations/init_db_1.py

# Run migrations
python migrations/migrate_database.py

# Create survey templates
python migrations/init_survey_templates.py

# Database uses single minipass.db file
```

## Core Architecture

### Key Files
- `app.py` - Main Flask application with all routes and core functionality
- `models.py` - SQLAlchemy database models (User, Activity, Signup, Passport, etc.)
- `config.py` - Environment-based configuration with database path handling
- `utils.py` - Utility functions for QR codes, emails, file handling, and background tasks

### Directory Structure
- `templates/` - Jinja2 HTML templates for web interface
- `static/` - Frontend assets including Tabler UI, TinyMCE, uploads, email templates
- `instance/` - SQLite database file (minipass.db)
- `tests/` - Comprehensive test suite including Flask startup, survey system, and chatbot tests
- `migrations/` - Database migration scripts and version control

### Database Models
Core entities include:
- **Admin** - Admin user management with bcrypt password hashing
- **Activity** - Event/activity management with image support
- **User/Signup** - User registration and activity signups
- **Passport/PassportType** - Digital passport system with QR code generation
- **Pass** - Legacy pass system (marked for deletion)
- **Survey System** - SurveyTemplate, Survey, SurveyResponse for feedback collection
- **Chat System** - ChatConversation, ChatMessage, QueryLog for AI chatbot integration
- **Financial** - EbankPayment, Income, Expense for payment tracking

## Key Patterns

- **UTC Timezone**: All datetime operations use UTC with proper timezone handling via `datetime.now(timezone.utc)`
- **Background Jobs**: APScheduler for email automation and scheduled tasks
- **Security**: CSRF protection, bcrypt password hashing, secure file uploads
- **QR Code System**: Generated passes with QR codes for ticket validation using `utils.py` functions
- **Email Templates**: HTML templates with inline CSS processing via premailer
- **AI Integration**: Chatbot system with support for multiple LLM providers (Ollama, Anthropic, OpenAI)

## Testing Strategy

The test suite includes:
- **test_flask_startup.py** - Application initialization and configuration validation
- **test_survey_system.py** - Survey functionality and database operations
- **test_chatbot_infrastructure.py** - AI chatbot integration testing
- **validate_fix.py** - Database schema and data integrity validation
- **test_admin.py** - Admin authentication and management features

Tests can be run individually with `python tests/filename.py` or collectively with pytest.

## UI/UX Guidelines

### Mobile Dropdown Buttons in Bootstrap Carousels

When creating dropdown buttons in mobile carousels, use Bootstrap's built-in Popper.js boundary configuration instead of fighting against carousel overflow requirements:

#### HTML Solution:
```html
<!-- Add data-bs-boundary="viewport" to mobile dropdown toggles -->
<a class="dropdown-toggle" 
   data-bs-toggle="dropdown" 
   data-bs-boundary="viewport" 
   href="#">Dropdown</a>
```

#### CSS Solution:
```css
/* Simple z-index boost for mobile dropdowns in carousels */
@media (max-width: 767.98px) {
  #carousel .dropdown-menu {
    z-index: 1060 !important;
  }
}
```

**Key Points:**
- Use `data-bs-boundary="viewport"` on dropdown toggles in carousels
- Let Bootstrap's Popper.js handle positioning automatically
- Only override z-index, never override carousel overflow
- Avoid custom JavaScript positioning that conflicts with Popper.js
- Keep carousel `overflow: hidden` intact for proper sliding

**Why This Works:**
- Bootstrap carousels need `overflow: hidden` for slide transitions
- Popper.js can position dropdowns outside overflow boundaries when boundary="viewport"
- This maintains both carousel functionality and dropdown visibility

## Environment Configuration

The application uses a single database configuration with `instance/minipass.db`.

Required environment variables should include Stripe keys, email configuration, and any AI API keys for chatbot functionality.

## Important Reminders

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User