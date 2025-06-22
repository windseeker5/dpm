# AI Analytics Chatbot Module - Implementation Plan

**Date:** 2025-06-22  
**Project:** Minipass - Analytics Chatbot Feature  
**Status:** Planning Phase

---

## Overview

Create a modern, conversational AI analytics chatbot for Minipass that allows users to query their data using natural language. The chatbot will provide intuitive access to insights about users, activities, passports, signups, expenses, and other business data.

**Key Goals:**
- Replace existing prototype with professional implementation
- Cost-efficient AI provider strategy
- Modern chat interface (WhatsApp/Discord style)
- Secure, read-only database queries
- Multi-language support (English/French)

---

## Technical Architecture

### 1. AI Provider Strategy (Cost-Efficient Multi-Tier)

**Development/Prototype Phase:**
- **Primary**: Ollama (your home server) - $0 cost
- **Models**: `dolphin-mistral:latest`, `llama3:8b`, `codellama:7b`
- **Access**: Via your public IP address

**Production Phase (Tiered Approach):**
- **Tier 1**: Anthropic Claude 3.5 Haiku - Most cost-effective for analytics
  - Input: ~$0.25 per 1M tokens
  - Output: ~$1.25 per 1M tokens
  - Best for: Simple queries, high volume
  
- **Tier 2**: OpenAI GPT-4o-mini - Backup option
  - Input: ~$0.15 per 1M tokens  
  - Output: ~$0.60 per 1M tokens
  - Best for: Complex reasoning when needed

- **Fallback**: Local Ollama for cost control
  - Automatic fallback when cloud budget limits reached

### 2. New Module Structure

```
/chatbot_v2/
├── __init__.py                 # Module initialization
├── routes.py                   # Flask routes and API endpoints
├── ai_providers.py            # Abstract AI provider interface
├── providers/
│   ├── __init__.py
│   ├── ollama.py              # Ollama integration
│   ├── anthropic.py           # Claude API integration  
│   ├── openai.py              # OpenAI API integration
├── query_engine.py            # SQL generation and execution
├── conversation.py            # Chat history and context management
├── security.py                # SQL injection prevention and validation
├── utils.py                   # Helper functions and utilities
└── config.py                  # Chatbot-specific configuration
```

### 3. Database Schema Extensions

**New Tables to Add:**

```sql
-- Chat conversation sessions
CREATE TABLE chat_conversation (
    id INTEGER PRIMARY KEY,
    admin_email VARCHAR(150) NOT NULL,
    session_token VARCHAR(32) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT (datetime('now')),
    updated_at DATETIME DEFAULT (datetime('now')),
    status VARCHAR(20) DEFAULT 'active'  -- active, archived, deleted
);

-- Individual chat messages
CREATE TABLE chat_message (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    message_type VARCHAR(20) NOT NULL,  -- user, assistant, system, error
    content TEXT NOT NULL,
    sql_query TEXT,                     -- Generated SQL (if applicable)
    query_result TEXT,                  -- JSON result (if applicable)
    ai_provider VARCHAR(50),            -- ollama, anthropic, openai
    ai_model VARCHAR(100),              -- Model used for this message
    tokens_used INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0,      -- Cost in cents
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES chat_conversation (id)
);

-- Query execution log for monitoring
CREATE TABLE query_log (
    id INTEGER PRIMARY KEY,
    admin_email VARCHAR(150) NOT NULL,
    original_question TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    execution_status VARCHAR(20) NOT NULL,  -- success, error, blocked
    execution_time_ms INTEGER,
    rows_returned INTEGER DEFAULT 0,
    error_message TEXT,
    ai_provider VARCHAR(50),
    ai_model VARCHAR(100),
    created_at DATETIME DEFAULT (datetime('now'))
);
```

### 4. UI/UX Design - Modern Chat Interface

**New Template: `analytics_chatbot.html`**

**Design Principles:**
- Modern messaging interface (WhatsApp/Discord style)
- Real-time typing indicators
- Message bubbles with timestamps
- Quick action buttons for common queries
- Data visualization integration (charts/graphs)
- Mobile-first responsive design
- Dark/light theme support
- Accessibility compliant

**Key UI Components:**
- Chat message container with scroll
- Input area with send button and file upload
- Typing indicator animation
- Quick query suggestion chips
- Data visualization area (charts, tables)
- Export controls (CSV, PDF, PNG)
- Conversation history sidebar
- Settings panel for AI provider selection

### 5. Core Features

#### A. Natural Language Processing
- Convert user questions to valid SQL queries
- Context-aware query understanding
- Multi-language support (English/French)
- Intent recognition for different query types

#### B. Conversation Management
- Persistent chat sessions
- Context awareness across messages
- Conversation history storage
- Session management and cleanup

#### C. Data Visualization
- Auto-detect when to show charts vs tables
- Support for: bar charts, line charts, pie charts, tables
- Interactive visualizations using Chart.js
- Export capabilities (PNG, SVG, CSV)

#### D. Query Templates
Pre-built queries for common questions:
- "Show me unpaid users for [activity]"
- "What's our revenue for the last [period]?"
- "List users who signed up [timeframe]"
- "Generate chart of signups by activity"
- "Which activities have highest expenses?"

#### E. Export & Sharing
- Export query results as CSV
- Generate PDF reports
- Share query URLs
- Download charts as images

### 6. Implementation Phases

#### Phase 1: Core Infrastructure (Week 1) ✅ COMPLETED
- [x] Create new `chatbot_v2` module structure
- [x] Implement abstract AI provider interface
- [x] Set up Ollama integration for development
- [x] Create basic database models and migrations
- [x] Implement query engine with security features

**Phase 1 Results:**
- ✅ All core infrastructure components implemented
- ✅ Ollama provider working correctly (4.4s response time)
- ✅ SQL security validation passing all tests (6/6)
- ✅ Provider manager successfully managing AI providers
- ✅ Database models added for chat functionality
- ✅ Dependencies updated in requirements.txt

#### Phase 2: Chat Interface (Week 2) ✅ COMPLETED
- [x] Design and implement modern chat UI
- [x] Add conversation management  
- [x] Implement real-time messaging features
- [x] Create responsive mobile design
- [x] Add typing indicators and message states

**Phase 2 Results:**
- ✅ Modern WhatsApp/Discord-style chat interface implemented
- ✅ Real-time messaging with typing indicators and message states  
- ✅ Responsive mobile-first design with accessibility features
- ✅ Complete conversation management system
- ✅ Flask blueprint registered and navigation updated
- ✅ JavaScript chat client with Chart.js integration
- ✅ CSS styling with dark mode and reduced motion support
- ✅ SQL result display with export capabilities
- ✅ Session statistics tracking and provider status monitoring

#### Phase 3: Cloud AI Integration (Week 3)
- [ ] Implement Anthropic Claude integration
- [ ] Add OpenAI GPT integration
- [ ] Create provider fallback system
- [ ] Implement cost tracking and limits
- [ ] Add usage monitoring dashboard

#### Phase 4: Advanced Features (Week 4)
- [ ] Data visualization integration
- [ ] Export functionality
- [ ] Query templates and suggestions
- [ ] Multi-language support
- [ ] Performance optimization

#### Phase 5: Testing & Deployment (Week 5)
- [ ] Comprehensive testing
- [ ] Security audit
- [ ] Performance testing
- [ ] Documentation
- [ ] Production deployment

### 7. Cost Management Features

#### Usage Monitoring
- Real-time token usage tracking
- Cost calculation per query
- Daily/monthly budget limits
- Usage alerts and notifications

#### Provider Optimization
- Automatic provider selection based on query complexity
- Cost-based routing (simple queries → cheaper models)
- Usage-based fallback to local Ollama
- Bulk query optimization

#### Budget Controls
- Per-admin usage limits
- Organization-wide budget caps
- Emergency fallback to free Ollama
- Cost reporting and analytics

### 8. Security & Safety

#### SQL Security
- Whitelist-only SQL operations (SELECT statements only)
- SQL injection prevention through parameterized queries
- Query complexity limits (joins, subqueries)
- Table and column access restrictions

#### Access Control
- Admin-only access initially
- Role-based permissions for future expansion
- Session-based authentication
- API rate limiting

#### Data Protection
- PII detection and redaction
- Sensitive data masking
- Query result filtering
- Audit logging for compliance

### 9. Sample Queries to Support

#### User Management
- "Show me all unpaid users for Hockey 2025"
- "List users who haven't completed their signups"
- "Find duplicate user registrations"
- "Show users by registration date"

#### Financial Analytics
- "What's our total revenue for the last 3 months?"
- "Show me expenses by category this year"
- "Generate a revenue chart by activity"
- "Which activities are most profitable?"

#### Activity Management
- "List all active activities"
- "Show signup counts by activity"
- "Find activities with low participation"
- "Generate activity performance report"

#### Operational Insights
- "Show me passport usage statistics"
- "List overdue payments"
- "Find popular activity types"
- "Generate monthly business summary"

### 10. File Structure Changes

#### New Files to Create:
```
chatbot_v2/
├── __init__.py
├── routes.py
├── ai_providers.py
├── providers/
│   ├── __init__.py
│   ├── ollama.py
│   ├── anthropic.py
│   └── openai.py
├── query_engine.py
├── conversation.py
├── security.py
├── utils.py
└── config.py

templates/
└── analytics_chatbot.html

static/
├── css/
│   └── chatbot.css
└── js/
    └── chatbot.js
```

#### Files to Modify:
- `app.py` - Register new chatbot_v2 blueprint
- `models.py` - Add new chat-related database models
- `requirements.txt` - Add new AI provider packages
- `templates/base.html` - Update navigation menu
- `config.py` - Add chatbot configuration settings

#### Files to Remove/Archive:
- `chatbot.py` - Legacy prototype
- `templates/chat.html` - Old chat interface

### 11. Dependencies & Requirements

#### New Python Packages:
```
# AI Providers
anthropic>=0.25.0
openai>=1.30.0
ollama>=0.2.0

# Additional utilities
tiktoken>=0.6.0          # Token counting
tenacity>=8.2.0          # Retry logic
pydantic>=2.0.0          # Data validation
```

#### Configuration Variables:
```python
# AI Provider Settings
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

# Cost Management
CHATBOT_DAILY_BUDGET_CENTS = int(os.environ.get('CHATBOT_DAILY_BUDGET_CENTS', 1000))  # $10
CHATBOT_MONTHLY_BUDGET_CENTS = int(os.environ.get('CHATBOT_MONTHLY_BUDGET_CENTS', 10000))  # $100

# Feature Flags
CHATBOT_ENABLE_ANTHROPIC = os.environ.get('CHATBOT_ENABLE_ANTHROPIC', 'false').lower() == 'true'
CHATBOT_ENABLE_OPENAI = os.environ.get('CHATBOT_ENABLE_OPENAI', 'false').lower() == 'true'
```

### 12. Cost Estimates (Monthly)

#### Development Phase:
- **Cost**: $0 (Ollama only)
- **Usage**: Unlimited local queries

#### Light Production (1,000 queries/month):
- **Anthropic**: ~$2-5/month
- **OpenAI**: ~$1-3/month
- **Recommended**: Start with Anthropic Claude Haiku

#### Medium Production (10,000 queries/month):
- **Anthropic**: ~$20-50/month
- **OpenAI**: ~$15-30/month
- **Features**: Add usage monitoring

#### Heavy Production (100,000 queries/month):
- **Anthropic**: ~$200-500/month
- **OpenAI**: ~$150-300/month
- **Recommendations**: Implement smart routing, caching

### 13. Success Metrics

#### User Experience:
- Query response time < 3 seconds
- Query accuracy > 90%
- User satisfaction score > 4.5/5
- Mobile usability score > 95%

#### Technical Performance:
- System uptime > 99.9%
- Error rate < 1%
- Cost per query < $0.05
- SQL injection attempts blocked: 100%

#### Business Impact:
- Reduced time for data analysis by 70%
- Increased data-driven decision making
- Improved operational efficiency
- Enhanced user self-service capabilities

---

## Next Steps

1. **Review and Approve Plan** - Stakeholder sign-off
2. **Environment Setup** - Configure development environment
3. **Phase 1 Implementation** - Begin core infrastructure development
4. **Iterative Development** - Build and test in phases
5. **Production Deployment** - Roll out to users

---

## Notes

- This plan replaces the existing chatbot prototype entirely
- All cost estimates are based on 2025 pricing and may vary
- Security is prioritized throughout the implementation
- The modular architecture allows for easy AI provider swapping
- Mobile-first design ensures accessibility across all devices

---

**Plan Created:** 2025-06-22  
**Next Review:** After Phase 1 completion  
**Estimated Timeline:** 5 weeks for full implementation