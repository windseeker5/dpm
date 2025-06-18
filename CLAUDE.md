# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard workflow 
1. Think about the problem first, read the source code for the relevant files, and write a plan in projectplan.md. 
2. This plan should contain a list of actions to be performed that you can tick as they are carried out. 
3. Before you start, contact me to check the plan. 
4. Then start working on the actions to be performed, marking them as completed as they go along. 
5. Please provide me with a detailed explanation of the changes made at each stage. 
6. Simplify each task and code modification as much as possible. We want to avoid massive or complex changes. Each change must have a minimal impact on the code. Simplicity is paramount. 
7. Finally, add a revision section to the projectplan.md file with a summary of the changes made and any other relevant information.


## Project Overview

Minipass is a mobile-first Activities and Digital Pass Management system built with Flask. It enables organizations to easily manage activities, digital passes or tickets, user signups, and payments—all in one place.

Designed for non-technical users, Minipass offers an intuitive interface optimized for mobile devices, allowing users to manage everything on the go. The platform also features an AI-powered chatbot for real-time insights and activity analytics, making it easier to track engagement and make informed decisions.

## Tech Stack

- **Flask** - Python web framework with SQLAlchemy ORM
- **SQLite** - Database (dev: `instance/database.db`, prod: `instance/database_prod.db`)
- **Tabler.io** - UI framework for admin dashboard
- **Stripe** - Payment processing
- **Ollama** - Local LLM integration for chatbot
- **Python 3.9** with comprehensive dependencies in `requirements.txt`

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

## Development Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db upgrade
```

### Running
```bash
# Development
flask run
# or
python app.py
```

## Key Patterns

- **Environment Detection**: Uses `FLASK_ENV` to switch between dev/prod databases
- **UTC Timezone**: All datetime operations use UTC with proper timezone handling
- **Background Jobs**: APScheduler for email automation and scheduled tasks
- **Security**: CSRF protection, bcrypt password hashing, secure file uploads
- **QR Code System**: Generated passes with QR codes for ticket validation
- **Email Templates**: HTML templates with inline CSS processing via premailer

## Business Logic

The system manages digital passes for activities where users can:
1. Sign up for activities with Stripe payment integration
2. Receive digital passes with QR codes
3. Have passes validated via QR scanning
4. Receive automated email confirmations and reminders

Financial tracking per activity includes income/expense management with payment reconciliation.

The AI chatbot provides natural language analytics queries against the business data.