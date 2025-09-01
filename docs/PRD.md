# Minipass Product Requirements Document (PRD)
**Version:** 1.0  
**Date:** August 28, 2025  
**Product Owner:** Ken Dresdell  
**Target Launch:** September 2025  

---

## 14. Operations & Support Strategy

### 14.1 **Customer Onboarding Process**
**Automated Container Deployment:**
1. Customer subscribes via main Flask website landing page
2. Collects: Organization name, desired subdomain, primary email (3-4 questions total)
3. Automated validation: Check subdomain availability, email format
4. Automated container deployment triggered upon successful validation
5. Beautiful welcome email sent with: subdomain URL, initial credentials, "getting started" video link
6. Video Onboarding: 2-3 minute maximum video showing basic system operation

**Design Principle:** Onboarding should be so intuitive that customers don't need the video, but it's there as a safety net.

### 14.2 **Customer Support Strategy**
**Support Philosophy:** Prevent issues rather than fix them - focus on bug-free, high-performance system.

**Support Channels:**
- **Primary:** Chat-based support (Microsoft Teams, Discord, or similar messaging platform)
- **Secondary:** Video/voice support available for complex issues
- **Self-Service:** Comprehensive library of short, engaging tutorial videos
- **Documentation:** Simple, visual guides for all core features

**Support Materials:**
- Multiple tutorial videos showing real-world usage scenarios
- Step-by-step visual guides for common tasks
- FAQ section based on actual customer questions

### 14.3 **Performance Monitoring & Infrastructure**
**Current Monitoring:** Custom Python scripts monitoring VPS performance and container health

**Scaling Triggers:** Evaluate CPU, RAM, and disk upgrades after every 10 new customers

**Health Monitoring Needs:**
- Container startup/crash detection
- Memory usage per customer container
- Database performance metrics
- Email delivery success rates
- Payment processing success rates

### 14.4 **Error Handling & Logging**
**User-Facing Errors:** 
- Friendly error messages in the dashboard with clear next steps
- Color-coded status indicators for payment issues, email problems
- Complete audit trail of all transactions and system events

**Technical Logging:**
- All errors logged in user's dashboard for transparency
- Payment failures: Clear status with actionable information
- Email issues: Automatic bounce-back notifications to user's email
- System errors: Logged but presented in user-friendly language

**Error Recovery:**
- Automatic retry mechanisms for temporary failures
- Clear escalation path for issues requiring manual intervention
- User notification for any issue that affects their service

---

## 1. Executive Summary

**Minipass** is a SaaS PWA (Progressive Web App) that provides end-to-end activities management for organizations. It streamlines registrations, payments, digital pass distribution, and activity tracking while offering comprehensive financial reporting and customer feedback collection.

### Vision Statement
To simplify organizational operations and optimize revenue through an automated, secure, and user-friendly digital platform that manages the complete activity lifecycle.

### Success Metrics
- **Launch Goal:** 10 pilot customers within first month
- **User Adoption:** 80% digital pass redemption rate
- **Financial Impact:** 25% reduction in administrative overhead for customers
- **User Satisfaction:** 4.5+ star rating from end users

---

## 2. Product Overview

### 2.1 Problem Statement
**Primary Market - Activity Managers:** Small business owners and activity managers who organize recurring activities (sports leagues, fitness classes, workshops, tournaments) currently struggle with fragmented manual processes. They use Excel spreadsheets for registrations, handle bank transfers manually, track payments in multiple systems, and manage attendance through paper lists or basic apps.

**Secondary Market - Small Business Loyalty Programs:** Small service businesses (coffee shops, salons, local services) rely on outdated paper punch cards for customer loyalty programs. These businesses miss opportunities for upfront revenue, struggle to track loyalty redemptions, and provide poor customer experience with easily-lost paper cards.

### 2.2 Solution
Minipass provides a unified digital platform serving both markets:

**For Activity Managers:**
- Create activities (e.g., "Monday Night Hockey", "September Golf Tournament") 
- Define passport types within each activity (e.g., "Substitute Pass", "Season Pass")
- Generate automatic web-based registration forms
- Process payments and automatically issue digital passports
- Track attendance through QR code scanning or manual redemption

**For Small Business Loyalty Programs:**
- Create loyalty activities (e.g., "Coffee Shop Loyalty Program")
- Define passport types for bulk purchases (e.g., "10 Coffees for $50", "5 Haircuts for $200")
- Generate upfront revenue through pre-paid service packages
- Track redemptions digitally, eliminating paper punch cards
- Build customer retention through convenient mobile access

### 2.3 Value Proposition
**For Activity Managers:**
- Eliminate Excel chaos and manual payment reconciliation
- Automatic email payment matching saves hours of administrative work
- Professional automated participant communication builds trust and reduces support requests
- Clear financial visibility with real-time KPI dashboards
- Never manually send payment confirmations or activity updates

**For Small Businesses (Loyalty):**
- Generate upfront cash flow through pre-paid packages
- Eliminate paper cards and manual tracking
- Automatic payment processing for email transfers
- Professional customer communication improves brand perception
- Reduce customer service inquiries with clear transaction history

**For All Participants/Customers:** 
- Easy online purchase with immediate confirmation
- Beautiful, professional email communications with complete transaction history
- Mobile access to digital passports with QR codes
- Always know exactly what you've purchased, paid for, and used
- Never lose track of your sessions or credits

---

## 3. Critical Project Constraints

### 3.1 **Infrastructure & Budget Constraints** 💰
- **Deployment Model:** One Docker container per customer on shared VPS infrastructure
- **Starting Budget:** Minimal server specifications with pay-as-you-grow scaling
- **Resource Limits:** Each container must be lightweight and efficient
- **Cost Optimization:** Prioritize features that don't require expensive third-party services

### 3.2 **Technical Development Constraints** ⚙️
- **Python-First Policy:** All business logic, data processing, and server operations in Python
- **JavaScript Minimization:** Use JavaScript only for essential UI interactions, keep code minimal
- **Simplicity Mandate:** Choose simple solutions over complex ones every time
- **Framework Constraint:** Stick with Flask + Tabler.io, avoid adding heavy dependencies

### 3.3 **Performance Constraints** 🚀
- **Speed is Critical:** Every feature must be optimized for fast response times
- **Memory Efficiency:** Low RAM usage is mandatory for multi-tenant deployment
- **Startup Speed:** Containers must start quickly for good customer experience

---

## 4. Target Users

### Primary Users (Activity Managers)
- **Amateur Sports League Organizers** (Priority 1) - Hockey leagues, soccer clubs, tennis groups
- **Fitness & Recreation Activity Leaders** (Priority 1) - Ski lessons, kitesurf sessions, gymnastics classes  
- **Individual Coaches & Instructors** (Priority 1) - Yoga teachers, dance instructors, running coaches
- **Tournament & Event Organizers** (Priority 2) - Golf tournaments, competitions, workshops
- **Community Group Coordinators** (Priority 3) - Local clubs, hobby groups, meetups

### Primary Users (Small Business Loyalty Programs)
- **Coffee Shops & Cafes** (Priority 1) - Independent coffee roasters, local cafes
- **Personal Services** (Priority 1) - Hair salons, barber shops, massage therapists
- **Local Food Services** (Priority 2) - Bakeries, lunch spots, food trucks
- **Specialty Retail** (Priority 2) - Bike shops with services, local bookstores with events
- **Professional Services** (Priority 3) - Car washes, dry cleaners, small repair shops

### Secondary Users (Customers/Participants)
- Sports league players and substitutes
- Lesson participants and students
- Loyalty program customers
- Tournament competitors  
- Community group members

### User Personas
#### Persona 1: "Marc the Hockey League Organizer"
- Manages Monday night amateur hockey league
- Currently uses Excel + bank transfers + WhatsApp groups
- Needs to track who paid, who's playing, substitute management
- Wants professional system without complexity

#### Persona 2: "Sophie the Ski Instructor"  
- Runs weekend ski lessons and private sessions
- Manages both season passes and drop-in lessons
- Struggles with payment tracking and attendance
- Values mobile-friendly solution for mountain use

#### Persona 3: "Carlos the Coffee Shop Owner"
- Runs independent coffee shop with paper punch cards
- Wants to generate upfront revenue and improve customer retention
- Struggles with lost punch cards and manual tracking
- Needs simple system that customers can use easily

### Activity Examples
**Activity Management:**
- "Monday Night Hockey", "Saturday Yoga Class", "Weekly Tennis League"
- "Winter Ski Lessons 2025", "Summer Golf Tournament"
- "Kitesurf Workshop Sept 15", "Gymnastics Competition"

**Loyalty Programs:**
- "Coffee Shop Rewards", "Salon Package Deals", "Bakery Loyalty Program"  
- "Car Wash Packages", "Massage Therapy Bundles"

---

## 4. Core Features & Requirements

### 4.1 MVP Features (Launch Priority)

#### A. Digital Passport Management ⭐ CRITICAL
- **Create Passports:** Generate digital passports with QR codes
- **Distribute Passports:** Send via email/SMS automatically
- **Track Passports:** Real-time status monitoring (sent, opened, redeemed)
- **Redeem Passports:** QR code scanning interface
- **Passport Templates:** Customizable passport designs

#### B. Registration System ⭐ CRITICAL
- **Registration Forms:** Customizable form builder
- **Automated Confirmations:** Email/SMS notifications
- **Capacity Management:** Limit attendees per activity
- **Waitlist Management:** Automatic notification system

#### C. **AUTOMATIC PAYMENT MATCHING** ⭐ KILLER FEATURE
- **Email Payment Monitoring:** Monitor designated email address for incoming e-transfers/interact payments
- **Automatic Matching:** Match payment amount + sender email to pending registrations
- **Auto-Status Update:** Automatically mark registrations as "PAID" without manual intervention
- **Payment Logging:** Complete audit trail of all matched payments with timestamps
- **Reconciliation Dashboard:** Show matched vs unmatched payments for easy oversight

#### D. **AUTOMATED PARTICIPANT COMMUNICATION** ⭐ CRITICAL
- **Professional Email Design:** Beautiful, branded email templates for all participant communications
- **Real-time Updates:** Automatic emails sent for every status change (payment received, passport issued, redemption, etc.)
- **Transaction History:** Complete transaction table in every email showing:
  - Purchase date and details
  - Payment confirmation date  
  - Redemption history with dates
  - Remaining sessions/credits
- **QR Code Integration:** Every communication includes participant's current passport with QR code
- **Activity Details:** Clear information about the specific activity, dates, and requirements

#### D. Payment Integration ⭐ CRITICAL
- **Payment Processing:** Credit card and digital wallet support (secondary to email payments)
- **Payment Tracking:** Transaction history and status
- **Refund Management:** Automated refund processing
- **Payment Reporting:** Revenue summaries by activity

#### E. **KPI Dashboard** ⭐ CRITICAL
- **Activity Overview Cards:** Clear KPI cards for each activity showing:
  - Total Revenue per activity
  - Passports Created count
  - Active Passports count  
  - Pending Sign-ups (awaiting approval)
  - Payment Status (paid vs pending)
  - Survey Response Rate and Satisfaction Scores
- **Real-time Updates:** Dashboard updates automatically as payments are matched
- **Financial Summaries:** Revenue summaries by date range

#### F. **AUTOMATED SURVEY SYSTEM** ⭐ HIGH PRIORITY
- **Pre-Built Survey Templates:** Ready-made survey templates for different activity types (sports, fitness, lessons, loyalty programs)
- **3-Click Deployment:** Activity managers can send surveys with just 3 clicks - no complex setup required
- **Smart Timing:** Send surveys after activity completion or after specific time periods
- **Participant-Friendly:** Ultra-simple surveys designed for quick completion (few clicks, few seconds)
- **Activity-Specific Targeting:** Send surveys to specific activities or all activities at once
- **Basic Questions:** Pre-configured essential questions: pricing feedback, scheduling preferences, location satisfaction, overall experience
- **Response Collection:** All responses automatically collected and displayed in easy-to-read format
- **Actionable Insights:** Help activity managers improve pricing, scheduling, location, and service quality

### 4.2 Phase 2 Features (Professional & Enterprise Tiers)

#### H. **AI DATA CHATBOT** 🔶 HIGH PRIORITY (Professional & Enterprise Only)
- **Natural Language Queries:** Ask questions about activity data in plain English
- **Intelligent Data Analysis:** LLM processes SQLite database to provide accurate answers
- **Formatted Responses:** Beautiful tables and summaries for easy understanding
- **Business Intelligence:** Answer questions like:
  - "Give me the list of people who haven't paid for Monday RK activity"
  - "Show me the substitute users who came the most to Monday RK activity"  
  - "What's my best performing activity this month?"
  - "Which customers have the most credits remaining?"
- **External LLM Integration:** Uses API connection to external LLM service
- **Data Privacy:** All queries processed securely, no data stored externally

#### I. **COMPLETE DATA OWNERSHIP** 🔶 HIGH PRIORITY (All Tiers)
- **SQLite Database Export:** Users can download their complete database at any time
- **No Vendor Lock-in:** Full data portability ensures users are never trapped
- **Backup Capability:** Easy backup and restore of all activity, payment, and participant data
- **Data Transparency:** Users own their data completely, can migrate to any solution

#### J. Advanced Survey System
- **Customer Surveys:** Post-activity feedback collection
- **Activity Evaluations:** Performance rating system
- **Survey Builder:** Custom question types and logic
- **Response Analytics:** Trend analysis and insights

#### K. Comprehensive Financial Management
- **Expense Tracking:** Manual expense entry with categories
- **Receipt Upload:** Image capture and storage
- **Profit/Loss Reporting:** Detailed financial analytics
- **Tax Preparation:** Export for accounting software

#### L. Enhanced Analytics
- **Customer Journey Analytics:** Registration to redemption flow
- **Predictive Insights:** Demand forecasting
- **Comparative Analysis:** Activity performance comparison

---

## 5. User Stories

### Activity Manager Stories
```
As an activity manager, I want to:
- Create an activity (e.g., "Monday Night Hockey") with multiple passport types so that I can serve different participant needs
- Generate automatic registration forms so that participants can sign up and pay online
- See a clear dashboard with KPI cards for each activity showing: revenue, passports created, active passports, pending sign-ups, and survey feedback
- Have email payments automatically matched to registrations so I never have to manually check Excel sheets again
- Ask questions about my data in plain English (e.g., "Who hasn't paid for Monday hockey?") and get instant answers
- Send professional surveys to participants with just 3 clicks using pre-built templates so I can improve my activities
- Get feedback on pricing, scheduling, and location without the hassle of creating surveys from scratch
- Download my complete database at any time so I own my data and am never locked into the platform
- Track who has paid and who hasn't with automatic updates so that I can follow up only when needed
- Scan QR codes or manually redeem passports so that I can track attendance efficiently
- Use an interface so simple that I can teach it to anyone in minutes
- Access all features without switching between different modes or interfaces
```

### Small Business Owner Stories (Loyalty Programs)
```
As a small business owner, I want to:
- Create a loyalty program (e.g., "Coffee Shop Rewards") with package deals so that I can generate upfront revenue
- Let customers buy loyalty packages online so that I don't handle cash or track paper cards
- Have email payments for loyalty packages automatically processed so I don't manually reconcile transactions
- Send simple surveys to my loyalty customers to understand what they like and how to improve
- Use pre-built survey templates designed for small businesses so I don't waste time creating surveys
- Redeem customer purchases quickly at point of sale so that service remains fast
- See KPI dashboard showing package sales, redemptions, revenue, and customer satisfaction without complexity
- Use the same simple interface whether managing loyalty programs or activities
- Replace paper punch cards with a professional digital solution that customers love and provides me business insights
```

### Customer/Participant Stories  
```
As a customer/participant, I want to:
- Register and pay online easily so that I don't have to deal with bank transfers, cash, or paper cards
- Send email payments (Interac e-Transfer) and have them automatically processed
- Receive beautiful, professional email confirmations immediately after every transaction
- See my complete transaction history in every email (purchase date, payment date, redemption dates)
- Access my digital passport with QR code on my phone so I don't need to print anything
- Always know exactly how many sessions/credits I have remaining
- Receive automatic updates when I attend activities so I can track my participation
- Feel confident that I'm dealing with a professional, trustworthy system
- Use the same simple system whether buying hockey league access or coffee shop loyalty packages
```

---

## 6. Technical Requirements & Constraints

### 6.1 **CRITICAL PERFORMANCE CONSTRAINTS** ⚠️
**Infrastructure Reality:** Multi-tenant Docker deployment on low-spec VPS servers
- **RAM Constraint:** Each customer container must operate in < 512MB RAM
- **CPU Constraint:** Minimal CPU usage, optimized for shared resources  
- **Storage Constraint:** Container size < 1GB per customer
- **Scaling Model:** One Docker container per customer organization
- **Budget Reality:** Start with minimal server specs, scale up as revenue grows

### 6.2 **MANDATORY TECHNICAL PRINCIPLES** 🎯
**Python-First Architecture:**
- **Primary Rule:** Use Python for ALL business logic, data processing, and server-side operations
- **JavaScript Minimization:** Use JavaScript ONLY when absolutely required for UI interactions
- **Complexity Constraint:** Any JavaScript code must be < 10 lines when possible, maximum 50 lines per function
- **Framework Choice:** Leverage Flask's simplicity - avoid heavy frameworks or libraries
- **Database Operations:** All queries and data processing in Python, never in JavaScript

**Extreme UI/UX Simplicity:**
- **Kid-Friendly Interface:** UI must be so intuitive that children can operate it
- **Single Unified Interface:** One UI serves both activity management and loyalty programs
- **No Mode Switching:** No separate interfaces for different use cases
- **Visual Clarity:** Large, clear buttons and text, obvious visual hierarchy
- **Minimal Clicks:** Maximum 3 clicks to complete any core action

**Automatic Payment Processing:**
- **Email Monitoring:** Real-time monitoring of designated email addresses for incoming payments
- **Pattern Recognition:** Automatic matching of payment amounts and sender emails to registrations
- **Zero Manual Intervention:** Payment matching happens automatically in background
- **Audit Trail:** Complete logging of all automatic payment matches

### 6.3 Architecture
- **Backend:** Flask (Python) with minimal dependencies
- **Frontend:** Server-side rendered HTML with Tabler.io CSS + minimal JavaScript
- **Database:** SQLite per customer container (single-tenant, portable, fast)
- **Authentication:** Simple session-based auth (avoid JWT overhead)
- **File Storage:** Local filesystem storage (avoid S3 costs/complexity in MVP)
- **AI Integration:** External LLM API for natural language data queries (Professional/Enterprise tiers)
- **Data Portability:** SQLite database export functionality for complete data ownership

### 6.4 Performance Requirements
- **Container Startup:** < 10 seconds cold start
- **Memory Usage:** < 400MB RAM per customer container under normal load
- **Response Time:** < 500ms for all pages (server-side rendered)
- **Database Queries:** < 100ms average query time
- **Concurrent Users:** 20 simultaneous users per container maximum

### 6.5 Integrations
- **Payment Gateway:** Stripe (primary), PayPal (secondary)
- **Email Service:** SendGrid or AWS SES
- **SMS Service:** Twilio
- **QR Code Generation:** Python QR library
- **External LLM Service:** OpenAI API, Anthropic Claude API, or similar for AI chatbot functionality (Professional/Enterprise tiers)
- **Analytics:** Google Analytics integration

### 6.3 Performance Requirements
- **Page Load Time:** < 3 seconds
- **Mobile Responsiveness:** 100% mobile-friendly
- **Uptime:** 99.5% availability
- **Concurrent Users:** Support 100 simultaneous users per organization

### 6.4 Security Requirements
- **Data Encryption:** All data encrypted in transit and at rest
- **Payment Compliance:** PCI DSS compliance through payment processor
- **Authentication:** Multi-factor authentication for admin users
- **Data Privacy:** GDPR/CCPA compliance features

---

## 7. Success Metrics & KPIs

### Business Metrics
- **Customer Acquisition:** 10 organizations in first month
- **Monthly Recurring Revenue (MRR):** $500 by month 1, $2,000 by month 3
- **Customer Retention:** 90% month-over-month retention
- **Average Revenue Per User (ARPU):** $25/month average (mix of plans)
- **Plan Distribution Target:** 60% Starter, 30% Professional, 10% Enterprise

### Product Metrics
- **Automatic Payment Matching:** 95% of email payments automatically matched without manual intervention
- **Participant Communication:** 100% of status changes trigger automatic professional emails
- **AI Chatbot Usage:** 60% of Professional+ users ask at least 5 questions per month about their data
- **AI Query Accuracy:** 90% of natural language queries return accurate, useful results
- **Data Export Usage:** 30% of users export their database within first 6 months (demonstrates data ownership trust)
- **Survey Response Rate:** 60% response rate on surveys (industry average is 10-15% for small businesses)
- **Survey Deployment:** 80% of Professional+ customers send at least one survey per activity
- **User Interface Usability:** 90% of new users complete first activity setup without support
- **Activity Utilization:** 80% of purchased activity slots actively used
- **Passport Redemption Rate:** 80% of issued passports are redeemed  
- **Payment Processing:** 95% successful payment rate (including email transfers)
- **User Satisfaction:** 4.5+ rating on feedback surveys
- **Support Request Reduction:** 70% fewer participant inquiries due to clear automated communication
- **Feature Adoption:** 70% of Professional+ customers use advanced reporting
- **Business Improvement:** Customers report average 15% improvement in activity satisfaction after using survey insights
- **Time Savings:** Average 5+ hours saved per week on payment reconciliation, participant communication, and feedback collection

### Technical Metrics
- **Container Memory Usage:** < 400MB RAM average, < 512MB peak
- **Container Startup Time:** < 10 seconds cold start
- **Page Load Speed:** < 500ms server response time
- **Database Query Performance:** < 100ms average
- **Container Size:** < 1GB per customer deployment
- **CPU Usage:** < 20% on shared VPS environment

---

## 8. Launch Timeline

### Week 1-2: MVP Development
- [ ] Core registration system
- [ ] Basic digital pass creation
- [ ] Payment integration (Stripe)
- [ ] Email notifications
- [ ] QR code generation

### Week 3: Testing & Refinement
- [ ] User acceptance testing with 2-3 pilot customers
- [ ] Bug fixes and performance optimization
- [ ] Mobile responsiveness testing
- [ ] Security audit

### Week 4: Launch Preparation
- [ ] Production deployment setup
- [ ] Documentation completion
- [ ] Customer onboarding materials
- [ ] Marketing website updates

### Launch Month: Market Entry
- [ ] Soft launch with pilot customers
- [ ] Gather user feedback
- [ ] Iterate based on feedback
- [ ] Begin broader customer acquisition

---

## 9. Pricing Strategy

### Activity-Based Tiered Model
**Starter:** $10/month
- 1 active activity
- Unlimited passports per activity
- Basic digital pass management
- Email notifications
- Basic reporting
- Email support

**Professional:** $35/month  
- Up to 10 active activities
- Unlimited passports per activity
- Advanced pass customization
- Automated surveys
- **AI Data Chatbot** - Ask questions about your data in natural language
- Enhanced reporting & analytics
- Priority support
- Custom branding

**Enterprise:** $50/month
- Up to 100 active activities
- Unlimited passports per activity
- Full feature access
- **AI Data Chatbot** - Ask questions about your data in natural language
- Advanced financial reporting
- Receipt uploads & expense tracking
- Dedicated support
- API access (future)
- White-label options (future)

### Pricing Philosophy
- **Activity-Focused:** Customers pay based on the number of activities they manage, not passport volume
- **Unlimited Passports:** No restrictions on passport generation per activity
- **Predictable Costs:** Organizations know exactly what they'll pay based on their activity portfolio
- **Growth-Friendly:** Easy to upgrade as business scales

### Business Rules & Limits
**Activity Definition:** An activity is a managed event or service (e.g., "Monday Night Hockey", "September Golf Tournament") that can have multiple passport types within it (e.g., "Season Pass", "Substitute Pass").

**Activity Limit Enforcement:** 
- Customers cannot create more activities than their plan allows
- Attempting to exceed limit triggers upgrade prompt
- No automatic upgrades - customer must explicitly choose new plan

**Activity Lifecycle Management:**
- Activities can be ongoing (weekly hockey) or seasonal (winter ski lessons)
- Seasonal activities count toward limit when active
- Different passport types within same activity (regular members vs substitutes) don't count as separate activities

**No Free Trial:** Customers must pay to access the system - no trial period offered

---

## 10. Competitive Advantages

### 10.1 **Automatic Payment Matching - Unique Differentiator**
**The Problem Solved:** Currently, activity managers receive email transfers, then manually check Excel sheets to match payments to registrations - a time-consuming, error-prone process.

**Minipass Solution:** Monitors designated email addresses and automatically matches incoming payments to the correct person and activity without any manual intervention.

**Competitive Advantage:** No other platform offers this level of automated payment reconciliation for email transfers/Interac e-Transfer, which is the dominant payment method for small Canadian activities.

### 10.2 **Extreme Simplicity**
- **Kid-Friendly Interface:** While competitors build complex enterprise solutions, Minipass focuses on intuitive design
- **Single Unified Platform:** Serves both activity management and loyalty programs without mode switching
- **Lightweight Architecture:** Fast, efficient containers vs. heavy enterprise platforms

### 10.3 **Professional Participant Experience**
- **Automated Communication:** Beautiful, professional emails sent automatically for every transaction and status change
- **Complete Transaction History:** Every email includes full transaction table showing purchase, payment, and redemption history
- **QR Code Integration:** Participants always have access to their current passport and QR code
- **Trust Building:** Professional communication reduces support requests and builds customer confidence
- **Transparency:** Participants always know exactly what they've purchased, paid for, and used

### 10.5 **Effortless Customer Feedback**
- **Pre-Built Survey Templates:** Small activity managers get professional survey tools they would never build themselves
- **3-Click Survey Deployment:** While competitors require complex survey setup, Minipass makes it effortless
- **Participant-Friendly Design:** Ultra-simple surveys ensure high response rates
- **Business Intelligence:** Provides actionable insights for pricing, scheduling, and service improvements that small businesses desperately need but rarely get
- **No Additional Tools:** Built into the platform rather than requiring separate survey services

### 10.7 **AI-Powered Business Intelligence for Non-Technical Users**
- **Natural Language Analytics:** Users can ask questions about their business in plain English instead of learning complex reporting tools
- **Instant Insights:** Get immediate answers to business questions without technical expertise
- **SQLite Integration:** Simple database structure makes AI queries fast and accurate
- **Business Optimization:** Non-technical users can discover insights they would never find in traditional dashboards
- **No Additional Learning Curve:** Chat interface requires zero training vs. complex analytics platforms

### 10.8 **Complete Data Ownership & Trust**
- **No Vendor Lock-in:** Users can export their complete SQLite database at any time
- **Data Transparency:** Complete ownership and control of all business data
- **Migration Freedom:** Users never feel trapped or worried about losing their data
- **Trust Building:** Data portability demonstrates confidence in product value
- **Competitive Differentiation:** While most SaaS platforms trap user data, Minipass liberates it

### 10.9 **Market Position**
- **Underserved Market:** Focuses on small activity managers ignored by enterprise solutions
- **Perfect Price Point:** $10 starter removes barriers vs. $99+ enterprise solutions
- **Canadian Payment Methods:** Built specifically for Interac e-Transfer workflows
- **Complete Automation:** While competitors require manual work, Minipass automates payment matching, participant communication, and feedback collection

---

## 11. Risks & Mitigation

### High Risk
**Competition from established players**
- *Mitigation:* Focus on SMB market, emphasize ease of use and quick setup

**Technical complexity of payment integration**
- *Mitigation:* Use proven payment processors, implement comprehensive testing

### Medium Risk  
**Customer adoption challenges**
- *Mitigation:* Provide excellent onboarding, offer setup assistance

**Mobile compatibility issues**
- *Mitigation:* Extensive mobile testing, progressive web app approach

### Low Risk
**Scalability concerns**
- *Mitigation:* Cloud-native architecture, monitoring and auto-scaling

---

## 11. Next Steps

1. **Validate Assumptions:** Conduct 5 customer interviews to validate problem/solution fit
2. **Technical Planning:** Create detailed technical architecture and database schema
3. **Design System:** Create UI mockups and user flow diagrams  
4. **Development Sprint Planning:** Break down features into 1-week development sprints
5. **Pilot Customer Recruitment:** Identify and reach out to 3-5 potential pilot customers

## 12. Development Principles & Guidelines

### 12.1 **Code Architecture Rules** 📋
**Python-First Development:**
- All business logic, data validation, and processing in Python
- Use Flask's templating system for dynamic HTML generation
- Database operations exclusively in Python (SQLAlchemy/raw SQL)
- Form handling and validation in Python using Flask-WTF

**Minimal JavaScript Policy:**
- JavaScript ONLY for: form enhancements, basic UI interactions, QR code scanning
- Maximum 10 lines per JavaScript function when possible
- Use vanilla JavaScript, avoid jQuery or heavy libraries
- Server-side rendering preferred over client-side dynamic content

**Performance-First Decisions:**
- Choose simple over complex solutions every time
- Optimize for memory usage and startup speed
- Use SQLite for single-tenant containers
- Avoid unnecessary HTTP requests and API calls

### 12.2 **Technology Stack Justification**
- **Flask:** Lightweight, minimal overhead, fast startup
- **Tabler.io:** CSS-only framework, no JavaScript dependencies
- **SQLite:** No separate database server, embedded, fast for single-tenant
- **Jinja2:** Server-side templating reduces client-side complexity
- **Python stdlib:** Use built-in libraries when possible

### 12.3 **CRITICAL: AI Coding Assistant Guidelines** ⚠️

**FOR ANY AI CODING ASSISTANT (INCLUDING CLAUDE CODE):**

**Mandatory JavaScript Constraints:**
- **DEFAULT RULE:** Always try Python/Flask solution first before considering JavaScript
- **JavaScript ONLY for:** Basic form validation, QR code scanning, simple UI interactions
- **Maximum JavaScript Function Size:** 10 lines preferred, 25 lines absolute maximum
- **No JavaScript Frameworks:** No jQuery, React, Vue, Angular - vanilla JavaScript only when required
- **No Complex JavaScript Logic:** No business logic, data processing, or API calls in JavaScript
- **One Bug Fix = One Change:** Never refactor surrounding code when fixing a bug

**Preferred Solutions Examples:**
- **Form Handling:** Use Flask-WTF and server-side validation, NOT client-side JavaScript validation
- **Dynamic Content:** Use Jinja2 templating with server-side data, NOT JavaScript DOM manipulation  
- **Data Display:** Server-side HTML generation, NOT JavaScript table libraries
- **User Feedback:** Flash messages with Flask, NOT JavaScript modals or notifications
- **Payment Processing:** Server-side with Stripe, NOT JavaScript payment widgets

**Forbidden Approaches:**
- ❌ Enterprise-grade JavaScript solutions for simple problems
- ❌ JavaScript libraries for tasks Python can handle
- ❌ Client-side data processing when server-side is possible
- ❌ Complex JavaScript state management
- ❌ JavaScript-based routing or navigation
- ❌ Refactoring working code when fixing unrelated bugs

**Bug Fix Protocol:**
1. **Minimal Change Principle:** Fix only the specific issue, don't improve surrounding code
2. **Python-First:** If bug is in JavaScript, consider if it can be moved to Python instead
3. **Test Isolation:** Ensure fix doesn't affect other working features
4. **Documentation:** Explain why each change is necessary

### 12.4 **Resource Optimization Strategy**
- **Memory:** Lazy loading, efficient data structures, connection pooling
- **CPU:** Minimize complex computations, cache frequently accessed data  
- **Disk:** Compress static files, optimize database schemas
- **Network:** Minimize external API calls, batch operations

---

## 13. Questions for Discussion

1. Should we prioritize mobile-first development or responsive web design for the scanning interface?
2. What's our approach for handling different time zones for activities that might span regions?
3. How do we handle seasonal activities that go dormant - do they still count against activity limits during off-season?
4. Should the UI differentiate between "activity management" and "loyalty program" modes, or keep one unified interface?
5. What level of passport customization should we offer in MVP (logos, colors, fields)?
6. How should we handle partial redemptions (e.g., someone has a 10-session pass, uses 3 sessions)?
7. Should the activity manager be able to issue refunds directly, or should that require admin approval?
8. For loyalty programs, should we support percentage discounts or only pre-paid packages?
9. How do we market to both activity managers AND small business owners - one website or separate positioning?
10. Should small businesses be able to set expiration dates on loyalty packages?

### Market Expansion Considerations
- **Dual Market Strategy:** The same platform serves activity managers and loyalty programs with identical technical requirements
- **Cross-Selling Opportunity:** A yoga instructor could use it for both class management AND loyalty packages
- **Marketing Challenge:** Need to communicate value to two different buyer personas with different pain points
- **UI Design:** Interface should be intuitive for both use cases without feeling cluttered

---

*This PRD will be updated based on customer feedback and market validation results.*