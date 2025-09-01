# Minipass - Activities Management SaaS

**A powerful SaaS PWA for end-to-end activities management system.**  
✔️ Simple — ✔️ Automated — ✔️ Secure

**Developer:** Ken Dresdell  
**Email:** kdresdell@gmail.com  
**Version:** 1.0  
**Target Launch:** September 2025

---

## What is Minipass?

Minipass streamlines **registrations**, **payments**, **digital passes**, and **activity tracking** for:

### 🏒 Activity Managers
- **Sports leagues** (hockey, soccer, tennis)
- **Fitness classes** (yoga, ski lessons, dance)
- **Tournaments & events** (golf competitions, workshops)

### ☕ Small Business Loyalty Programs  
- **Coffee shops & cafes** (replace paper punch cards)
- **Personal services** (salons, massage therapy)
- **Local businesses** (generate upfront revenue)

---

## 🚀 Key Features

### 🎫 **Digital Pass Management**
- Create, send, and track digital passes with QR codes
- Mobile-friendly redemption system

### 💳 **Automatic Payment Matching** (Killer Feature)
- Monitors email for incoming e-transfers/Interac payments
- Automatically matches payments to registrations
- Eliminates manual Excel reconciliation

### 📧 **Automated Professional Communication**
- Beautiful, branded email templates  
- Complete transaction history in every email
- Automatic updates for all status changes

### 📊 **KPI Dashboard**
- Real-time revenue and participation tracking
- Activity performance metrics
- Payment status monitoring

### 📝 **Effortless Survey System**
- Pre-built templates for different activity types
- 3-click deployment to gather customer feedback
- Actionable insights for pricing and scheduling

---

## 🔧 Technology Stack

- **Backend:** Flask (Python) + SQLite
- **Frontend:** Server-side HTML + Tabler.io CSS  
- **Authentication:** Simple session-based
- **QR Codes:** Python QR library
- **Payments:** Stripe integration
- **Email:** Custom and homemade tools
- **Architecture:** One Docker container per customer

---

## 🎯 Development Environment

### Infrastructure Status
- **Flask Server:** `localhost:5000` ✅ Running
- **MCP Playwright:** ✅ Available for testing
- **Database:** SQLite ✅ Configured
- **Testing:** Unit tests + MCP Playwright integration

### For Claude Code Agents
🚨 **MANDATORY:** Read `docs/CONSTRAINTS.md` before any work

### Tech Constraints
- **Python-First:** All business logic in Python
- **Minimal JavaScript:** <10 lines per function max
- **Container Limits:** <512MB RAM, <10s startup
- **Testing Required:** Unit + integration tests mandatory

---

## 💰 Pricing (Activity-Based Model)

### **Starter** - $10/month
- 1 active activity
- Unlimited passports per activity
- Basic digital pass management  
- Email notifications

### **Professional** - $35/month
- Up to 10 active activities
- Advanced surveys + **AI Data Chatbot**
- Enhanced reporting & analytics
- Custom branding

### **Enterprise** - $50/month  
- Up to 100 active activities
- Full feature access + **AI Data Chatbot**
- Advanced financial reporting
- API access

---

## 🎯 Competitive Advantages

### **Unique Differentiators:**
- **Automatic Payment Matching** - No other platform offers this for Canadian e-transfers
- **Extreme Simplicity** - Kid-friendly interface vs complex enterprise solutions
- **Professional Participant Experience** - Automated, branded communications
- **Complete Data Ownership** - Users can export their SQLite database anytime
- **AI Business Intelligence** - Natural language queries about business data

### **Target Market Position:**
- **Underserved SMB Market** - Small activity managers ignored by enterprise solutions
- **Perfect Price Point** - $10 starter vs $99+ enterprise alternatives
- **Canadian Payment Focus** - Built specifically for Interac e-Transfer workflows

---

## 📁 Project Structure

```
minipass/
├── docs/
│   ├── PRD.md                  # Complete product requirements
│   └── CONSTRAINTS.md          # Development constraints for agents
├── plans/                      # Brandstorming and panning 
├── prompts/
│   └── CLAUDE-CODE-PROMPTS.md  # Ready-to-use prompts
├── app/                        # Flask application
├── tests/                      # Unit and integration tests
└── README.md                   # This file
```

---

## 🚀 Getting Started

### For Development:
1. Ensure Flask server is running on `localhost:5000`
2. Verify MCP Playwright server is available  
3. Read `docs/CONSTRAINTS.md` for development rules
4. Use `prompts/CLAUDE-CODE-PROMPTS.md` for consistent agent behavior

### For Claude Code:
Always start with:
```
ROLE: You are an ORCHESTRATOR - plan and delegate, DO NOT code
CONTEXT: Minipass project (read docs/PRD.md)  
CONSTRAINTS: Follow docs/CONSTRAINTS.md
TASK: [Your specific request]
```

---

## 📈 Success Metrics (Launch Goals)

- **Customer Acquisition:** 10 organizations in first month
- **Payment Automation:** 95% of email payments auto-matched
- **User Experience:** 90% of new users complete setup without support
- **Business Impact:** 25% reduction in administrative overhead
- **Customer Satisfaction:** 4.5+ star rating

---

## 🎯 Vision Statement

*To simplify organizational operations and optimize revenue through an automated, secure, and user-friendly digital platform that manages the complete activity lifecycle.*

**Minipass** - Simplify your operations. Optimize your revenue.

---

*For questions or support, contact Ken Dresdell at kdresdell@gmail.com*