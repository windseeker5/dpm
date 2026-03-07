# Template Session Design Issues - Critical Fix Required

**Date:** March 7, 2026
**Discovered:** Production crash on KDC `/payment-bot-matches` endpoint
**Severity:** CRITICAL - Affects all pages using `current_admin` object

## 🚨 The Problem

### What Happened
- KDC container crashed with `SQLAlchemy DetachedInstanceError`
- Error occurred in `base.html:483` when template tried to access `current_admin.avatar_filename`
- Only triggered on specific pages, making it hard to debug

### Root Cause Analysis
Templates are directly accessing SQLAlchemy ORM objects, causing unpredictable session management issues.

## 🔥 Bad Design Patterns Identified

### 1. Templates Doing Database Queries
```html
<!-- BAD: This can trigger database access -->
{% if current_admin and current_admin.avatar_filename %}
    {{ url_for('static', filename='uploads/avatars/' ~ current_admin.avatar_filename) }}
{% else %}
    https://www.gravatar.com/avatar/{{ session['admin']|lower|trim|encode_md5 }}?d=identicon
{% endif %}
```

**Problems:**
- Templates shouldn't trigger database queries
- `current_admin` can become detached from SQLAlchemy session
- Crash timing depends on session state, making it unpredictable

### 2. Global State Dependency
- `current_admin` is stored in Flask session/global state
- No guarantee the object is fresh or properly attached to database session
- Different routes may have different session states

### 3. Inconsistent Data Loading
- Some routes properly load admin data
- Others rely on stale session objects
- No centralized admin data management

## 🎯 Impact Assessment

**This pattern is likely used throughout the application**, meaning:

### Potentially Affected Pages
- **All pages using `base.html`** (which is probably most pages)
- **Any template accessing `current_admin` attributes**
- **Pages with user authentication/avatar display**

### Risk Scenarios
- Random crashes when SQLAlchemy sessions expire
- Different behavior between development and production
- Crashes that only appear under specific timing conditions
- Issues that get worse with higher user load

### Current Workaround
- Container restarts temporarily fix the issue
- But underlying problem remains and will resurface

## 🛠️ Recommended Fixes

### 1. Template Data Pre-Loading Pattern
```python
# GOOD: In route handlers, pre-load all template data
@app.route('/some-page')
def some_page():
    admin_data = {
        'avatar_url': get_admin_avatar_url(),  # Pre-computed
        'name': current_user.name if current_user else None,
        'email': current_user.email if current_user else None
    }
    return render_template('page.html', admin=admin_data)
```

```html
<!-- GOOD: Template just displays pre-computed data -->
<img src="{{ admin.avatar_url }}" alt="Avatar">
```

### 2. Centralized Admin Data Management
```python
def get_admin_context():
    """Centralized function to get admin data for templates"""
    if not session.get('admin'):
        return None

    # Fresh database query every time
    admin = Admin.query.get(session['admin'])
    if not admin:
        return None

    return {
        'name': admin.name,
        'email': admin.email,
        'avatar_url': get_avatar_url(admin),
        'is_authenticated': True
    }

def get_avatar_url(admin):
    """Centralized avatar URL logic"""
    if admin.avatar_filename:
        return url_for('static', filename=f'uploads/avatars/{admin.avatar_filename}')
    else:
        import hashlib
        email_hash = hashlib.md5(admin.email.lower().encode()).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
```

### 3. Template Context Processor
```python
@app.context_processor
def inject_admin():
    """Make admin data available to all templates"""
    return {'admin': get_admin_context()}
```

### 4. Base Template Refactor
```html
<!-- GOOD: base.html uses pre-computed data -->
{% if admin and admin.is_authenticated %}
    <img src="{{ admin.avatar_url }}" alt="{{ admin.name }}">
{% endif %}
```

## 🔍 Audit Required

### Pages to Check (Priority Order)
1. **All routes using `render_template()`** - check what data they pass
2. **All templates extending `base.html`** - check for direct ORM access
3. **Any template using `current_admin`** - needs refactoring
4. **Session management code** - ensure proper SQLAlchemy session handling

### Search Patterns
```bash
# Find all templates using current_admin
grep -r "current_admin" templates/

# Find all templates using session['admin']
grep -r "session\['admin'\]" templates/

# Find all direct ORM object access in templates
grep -r "\." templates/ | grep -E "(\.id|\.name|\.email|\.filename)"
```

## ⚠️ Development Environment Setup

### Testing the Fix
1. **Reproduce the issue locally**
2. **Implement centralized admin data management**
3. **Refactor templates to use pre-computed data**
4. **Test with session expiration scenarios**
5. **Load test to ensure no performance regression**

### Deployment Strategy
1. **Fix in development first**
2. **Thorough testing with all user scenarios**
3. **Deploy during maintenance window**
4. **Monitor production logs after deployment**

## 🚨 Production Bandaid

**Current status:** KDC fixed with container restart and Stripe Price ID addition.

**Temporary monitoring:** Watch for similar `DetachedInstanceError` in logs across all containers.

**If crashes occur:** Container restart fixes symptom, but root cause remains.

## 💡 Additional Considerations

### Performance Impact
- Current pattern may cause unnecessary database queries
- Centralized admin data loading could improve performance
- Consider caching admin data for session duration

### Security Impact
- Direct ORM access in templates could expose sensitive data
- Centralized admin data function can implement proper data filtering
- Better control over what data reaches templates

### Maintainability
- Current pattern makes debugging difficult
- Centralized approach makes changes easier
- Clear separation between business logic and presentation

---

**This document should be used to guide the refactoring effort in the local development environment. DO NOT implement these changes directly in production.**