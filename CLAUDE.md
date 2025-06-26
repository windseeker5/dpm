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

Minipass is a mobile-first Activities and Digital Passport Management system built with Flask. It enables organizations and small businesses to easily manage activities, digital passport ,signups, and payments.

Minipass offers an intuitive interface optimized for mobile devices, allowing users to manage everything on the go. 


## Tech Stack

- **Flask** - Python web framework with SQLAlchemy ORM
- **SQLite** - Database (dev: `instance/database.db`)
- **Tabler.io** - UI framework for admin dashboard based on Boostrap and ApexJS
- **Stripe** - Payment processing
- **Python** with comprehensive dependencies in `requirements.txt`

## Core Architecture

### Key Files
- `app.py` - Main Flask application with all routes
- `models.py` - Database models (User, Activity, Signup, Passport, etc.)
- `config.py` - Environment-based configuration
- `utils.py` - Utility functions for QR codes, emails, file handling


### Directory Structure
- `templates/` - Jinja2 HTML templates
- `static/` - Assets including Tabler UI, TinyMCE, uploads, email templates
- `instance/` - SQLite database files


## Key Patterns

- **UTC Timezone**: All datetime operations use UTC with proper timezone handling
- **Background Jobs**: APScheduler for email automation and scheduled tasks
- **Security**: CSRF protection, bcrypt password hashing, secure file uploads
- **QR Code System**: Generated passes with QR codes for ticket validation
- **Email Templates**: HTML templates with inline CSS processing via premailer



## UI/UX Guidelines
