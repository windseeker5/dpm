# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard Workflow

1. Understand the Problem First. Begin by reading the relevant source code and thinking through the problem. Then, write a clear plan in projectplan.md.

 - Always append new planned features to this file — even small ones.
 - Include the date and time for each new feature entry.

2. Write an Action Plan. Your plan in projectplan.md should include a checklist of concrete steps to implement the feature. You will tick off these steps as you complete them.

3. Review the Plan Before Starting. Before writing any code, contact me to review and approve the action plan.

4. Test-Driven Development. Create Pytest unit tests for all new features — including functions, classes, routes, etc. If you modify existing logic, update the related tests accordingly.

 - All tests must live in the /tests directory, mirroring the main app structure.
 - Include at least:
   - One success case
   - One edge case
   - One failure case

5. Execute the Plan. Begin coding based on the approved action plan. Check off each completed action in projectplan.md as you go.

6. Explain Your Changes. After each stage of implementation, write a clear explanation of the changes made and why.

7. Keep it Simple. Prioritize simplicity.
 - Break down tasks into small, manageable changes.
 - Avoid large or complex commits.
 - Each modification should have minimal impact on the overall codebase.

8. Document Revisions. At the end of each feature or task, add a Revision section to projectplan.md summarizing:
 - What was implemented or changed
 - Any key decisions or notes for future work
















## Project Overview

Minipass is a mobile-first Activities and Digital Passport Management system built with Flask. It enables organizations and small businesses to easily manage activities, digital passport or tickets, user signups, and payments—all in one place.

Designed for non-technical users, Minipass offers an intuitive interface optimized for mobile devices, allowing users to manage everything on the go. The platform also features an AI-powered chatbot for real-time insights and activity analytics, making it easier to track engagement and make informed decisions.

## Tech Stack

- **Flask** - Python web framework with SQLAlchemy ORM
- **SQLite** - Database (dev: `instance/database.db`, prod: `instance/database_prod.db`)
- **Tabler.io** - UI framework for admin dashboard
- **Stripe** - Payment processing
- **Python** with comprehensive dependencies in `requirements.txt`

## Core Architecture

### Key Files
- `app.py` - Main Flask application with all routes
- `models.py` - Database models (User, Activity, Signup, Passport, etc.)
- `config.py` - Environment-based configuration
- `utils.py` - Utility functions for QR codes, emails, file handling
- `chatbot.py` - AI analytics chatbot (separate Blueprint)

### Database Models
Core business models: User, Activity, Signup, Passport, Expense/Income, Admin, AdminActionLog
Legacy models marked for cleanup: Pass, Redemption, EbankPayment

### Directory Structure
- `templates/` - Jinja2 HTML templates
- `static/` - Assets including Tabler UI, TinyMCE, uploads, email templates
- `migrations/` - Database migration files
- `instance/` - SQLite database files



## Key Patterns

- **Environment Detection**: Uses `FLASK_ENV` to switch between dev/prod databases
- **UTC Timezone**: All datetime operations use UTC with proper timezone handling
- **Background Jobs**: APScheduler for email automation and scheduled tasks
- **Security**: CSRF protection, bcrypt password hashing, secure file uploads
- **QR Code System**: Generated passes with QR codes for ticket validation
- **Email Templates**: HTML templates with inline CSS processing via premailer

## Business Logic

The system manages digital passes for activities where users can:
1. Sign up for activities with e-bank transfert or Stripe payment integration
2. Receive digital passes with QR codes
3. Have passes validated via QR scanning
4. Receive automated email confirmations and reminders

Financial tracking per activity includes income/expense management with payment reconciliation.

The AI chatbot provides natural language analytics queries against the business data.