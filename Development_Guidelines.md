# Claude Code Development Guidelines - Minipass Project

## CRITICAL: Read This First Every Time

This document contains **mandatory constraints** for the Minipass project. Violating these constraints will cause bugs, performance issues, and deployment failures.

---

## Core Project Constraints

### **Infrastructure Reality**
- **Docker containers:** One per customer, deployed on low-spec VPS servers
- **Memory limit:** Each container must use < 512MB RAM
- **CPU constraint:** Shared VPS resources, optimize for minimal usage
- **Database:** SQLite per container (single-tenant, portable)
- **Budget constraint:** Start small, scale as revenue grows

### **Architecture Requirements**
- **Backend:** Python Flask with minimal dependencies
- **Frontend:** Server-side HTML rendering with Jinja2
- **Styling:** Tabler.io CSS framework (no JavaScript dependencies)
- **Authentication:** Simple Flask sessions (no JWT)
- **File storage:** Local filesystem (no S3/cloud storage)

---

## MANDATORY JavaScript Constraints

### **Default Rule: Python First**
- **ALWAYS try Python/Flask solution first** before considering JavaScript
- JavaScript is permitted ONLY for: form validation, QR code scanning, basic UI interactions
- **Maximum JavaScript function size:** 10 lines preferred, 25 lines absolute maximum

### **Forbidden JavaScript Approaches**
❌ **NO** jQuery, React, Vue, Angular, or any JavaScript frameworks  
❌ **NO** JavaScript for business logic, data processing, or API calls  
❌ **NO** Client-side routing or navigation  
❌ **NO** JavaScript for form handling (use Flask-WTF instead)  
❌ **NO** JavaScript DOM manipulation for dynamic content (use Jinja2)  
❌ **NO** JavaScript for data display (generate tables server-side)  
❌ **NO** Complex JavaScript state management  

### **Preferred Solutions**
✅ **Form Handling:** Flask-WTF with server-side validation  
✅ **Dynamic Content:** Jinja2 templating with Python data  
✅ **User Feedback:** Flask flash messages  
✅ **Data Display:** Server-side HTML generation  
✅ **Payment Processing:** Server-side Stripe integration  

---

## Bug Fix Protocol

### **Minimal Change Principle**
1. **Fix ONLY the specific issue** - don't improve surrounding code
2. **One bug = One focused change** - don't refactor working features
3. **Test in isolation** - ensure fix doesn't break other functionality
4. **Document why** - explain the necessity of each change

### **JavaScript Bug Handling**
- **First option:** Can this functionality be moved to Python instead?
- **If JavaScript required:** Use vanilla JavaScript, maximum 10 lines
- **Never refactor** working JavaScript when fixing unrelated bugs

---

## Development Patterns

### **Flask Patterns to Use**
```python
# Form handling
from flask_wtf import FlaskForm
from wtforms import StringField, validators

# Database operations  
import sqlite3
# Simple query patterns, avoid ORM complexity

# Templates
return render_template('template.html', data=python_data)
# Always pass Python data to templates
```

### **Database Patterns**
- **Use SQLite3 directly** or simple SQLAlchemy if needed
- **Keep queries simple** - optimize for readability over complexity
- **One database per customer container**
- **Prepare for easy data export** (user data ownership)

### **Performance Optimization**
- **Lazy loading** where possible
- **Minimize memory usage** in all operations
- **Cache static content** appropriately
- **Optimize database queries** for fast response times

---

## UI/UX Constraints

### **Simplicity Requirements**
- **Interface must be usable by children** - extreme simplicity
- **Maximum 3 clicks** to complete any core action
- **Large, clear buttons** with obvious visual hierarchy
- **Single unified interface** - no mode switching between activity/loyalty features

### **Tabler.io Usage**
- **Use existing Tabler components** - don't create custom CSS
- **Responsive design** built-in with Tabler classes
- **No additional CSS frameworks** or custom styling

---

## Feature Implementation Priorities

### **MVP Features (Critical Path)**
1. Digital passport creation and distribution
2. **Automatic email payment matching** (killer feature)
3. QR code scanning for redemption
4. **Automated participant communication** with transaction history
5. **KPI dashboard** with activity overview cards
6. **3-click survey system** with pre-built templates

### **Professional/Enterprise Features**
- **AI chatbot** for natural language data queries (external LLM API)
- **Complete data export** (SQLite database download)
- Advanced reporting and analytics

---

## Error Handling Strategy

### **User-Facing Errors**
- **Friendly messages** with clear next steps
- **Color-coded status** indicators for issues
- **Complete audit trail** visible to users
- **No technical jargon** in user interfaces

### **Technical Logging**
- **Log everything** for debugging purposes
- **User dashboard transparency** - show relevant logs
- **Email notifications** for payment/system issues
- **Automatic retry mechanisms** for temporary failures

---

## Deployment Considerations

### **Container Optimization**
- **Minimize Docker image size** - use Python slim images
- **Fast startup times** - < 10 seconds cold start
- **Efficient resource usage** - optimize for shared VPS hosting
- **Stateless application design** where possible

### **Database Management**
- **SQLite per container** for data isolation
- **Regular backup capabilities** built into application
- **Easy data export** for user data ownership
- **Simple schema design** for AI chatbot integration

---

## Communication with External Services

### **Email Integration**
- **SendGrid or AWS SES** for transactional emails
- **Beautiful HTML templates** for professional participant communication
- **Monitor designated email addresses** for incoming payments (Interac e-Transfer)
- **Automatic payment matching** based on email content parsing

### **Payment Processing**
- **Stripe integration** for credit card payments
- **Email transfer monitoring** for Canadian Interac payments
- **Automatic reconciliation** between payments and registrations
- **Complete audit trail** of all payment activities

---

## AI Integration Guidelines

### **External LLM Integration** (Professional/Enterprise tiers)
- **API-based integration** with OpenAI, Anthropic, etc.
- **SQLite database queries** converted to natural language responses
- **No data storage** on external services (privacy)
- **Formatted responses** as tables and summaries
- **Cost optimization** through efficient API usage

---

## Testing Strategy

### **Manual Testing Priorities**
- **Payment matching accuracy** - critical feature
- **Email delivery reliability** - participant communication
- **QR code scanning functionality** - redemption process
- **Container memory usage** - performance constraints
- **Database operations** - SQLite performance

### **Error Scenarios to Test**
- **Payment failures** and recovery
- **Email delivery issues** 
- **Container memory limits** exceeded
- **Database corruption** scenarios
- **Network connectivity** problems

---

## Success Metrics to Monitor

### **Technical Performance**
- **Container startup time:** < 10 seconds
- **Memory usage:** < 400MB average per container
- **Database query time:** < 100ms average
- **Email delivery rate:** > 95% success
- **Payment matching accuracy:** > 95% automatic success

### **User Experience**
- **First-time setup completion:** > 90% without support
- **Feature adoption rates** across all tiers
- **Customer support ticket volume** (should be minimal)
- **User satisfaction scores** from surveys

---

## Remember: Simplicity Over Complexity

**Every development decision should prioritize:**
1. **Simplicity** over feature richness
2. **Performance** over fancy functionality  
3. **Reliability** over cutting-edge technology
4. **User-friendliness** over technical sophistication
5. **Python solutions** over JavaScript alternatives

**The goal is a lightweight, fast, reliable application that non-technical users love and that can be maintained by a solo developer.**