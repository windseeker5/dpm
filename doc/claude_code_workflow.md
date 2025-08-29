# Minipass - Claude Code Workflow Guide

## Overview

This workflow prevents Claude Code from over-engineering, creating bugs, or hallucinating enterprise-grade solutions for simple problems. Follow this process for every development session.

---

## 3-Layer Documentation Strategy

Your project uses **3 levels of guidance** for Claude Code:

1. **📋 PRD** (Strategic Context) - What to build and why
2. **⚙️ Development Guidelines** (Technical Constraints) - How to build it
3. **🎯 Session Prompt** (Focus Reminder) - Stay on track each session

---

## Initial Project Setup (Do This Once)

### Step 1: Organize Project Documents
Place these documents in your Minipass project root folder:
- `Minipass PRD v1.0.md` 
- `Claude Code Development Guidelines.md`
- `Claude Code Workflow Guide.md` (this document)

### Step 2: Initialize Claude Code
```bash
cd /path/to/minipass-project
claude-code init
```
Claude Code will automatically read and understand your project context from the documents.

---

## Daily Development Workflow

### Before Each Coding Session

**1. Start Claude Code:**
```bash
claude-code chat
```

**2. Paste Session Prompt Template:**
```
CRITICAL CONSTRAINTS: Python Flask app, minimize JavaScript, SQLite per container, server-side rendering, low-RAM optimization. Fix ONE thing at a time, don't refactor working code. When unsure: choose Python over JavaScript.
```

### Making Development Requests

**3. Be Specific and Focused:**
✅ **Good Example:**
```
Fix the payment validation error in routes.py line 45. Only change the validation logic, don't refactor the entire payment system. Check Development Guidelines section for JavaScript constraints.
```

❌ **Bad Example:**
```
Improve the payment system and make it better.
```

**4. Reference Documentation When Needed:**
- "Check PRD section 4.1 for the automatic payment matching requirements"
- "Follow Development Guidelines for JavaScript constraints" 
- "See PRD user stories for the expected behavior"

### During Development

**5. Enforce Constraints:**
If Claude Code suggests JavaScript solutions:
```
No, use the Python/Flask approach instead. Check the Development Guidelines - we minimize JavaScript to absolute bare minimum.
```

**6. Prevent Scope Creep:**
If Claude Code starts refactoring working code:
```
Stop. Fix only the specific bug I mentioned. Don't change working functionality.
```

**7. Validate Solutions:**
Ask Claude Code to explain:
```
Explain why this solution follows our memory constraints and Python-first approach.
```

---

## Session Templates for Common Tasks

### Bug Fix Session
```
CRITICAL CONSTRAINTS: Python Flask app, minimal JavaScript, fix ONE thing only.

I need to fix [specific bug description]. 

Only change what's necessary to fix this issue. Don't refactor working code around it. 

Always use the best competent agent for the task.

Do not start a flask server. We already have one up and running for debug on port 8890.


Always test your task using playwrights mcp server and username = kdresdell@gmail.com and password = admin123


Reference: @Developmet_Guidelines.md [Bug Fix Protocol]
```

### New Feature Session  
```
CRITICAL CONSTRAINTS: Python Flask app, minimal JavaScript, server-side rendering.

I need to implement [specific feature from PRD]. This should follow our Python-first approach and integrate with existing Flask patterns.

Reference: PRD section [relevant section] and Development Guidelines
```

### Performance Optimization Session
```
CRITICAL CONSTRAINTS: < 512MB RAM per container, SQLite database, minimize resource usage.

I need to optimize [specific component] for memory usage. Focus on efficiency, don't add new features.

Reference: Development Guidelines performance section
```

---

## Quality Control Checklist

After each development session, verify:

### ✅ **Technical Constraints Met**
- [ ] Uses Python/Flask patterns (not JavaScript)
- [ ] Server-side rendering with Jinja2
- [ ] Minimal memory usage approach
- [ ] SQLite database operations
- [ ] No unnecessary refactoring of working code

### ✅ **Feature Requirements Met**
- [ ] Matches PRD specifications
- [ ] Maintains kid-friendly UI simplicity
- [ ] Follows activity-based business logic
- [ ] Preserves existing functionality

### ✅ **Performance Standards**
- [ ] Fast response times
- [ ] Memory efficient
- [ ] Works in low-resource container

---

## Troubleshooting Common Issues

### Problem: Claude Code generates complex JavaScript
**Solution:** 
```
Stop. Check Development Guidelines - we use Python/Flask for this. Show me the server-side solution instead.
```

### Problem: Claude Code refactors working code
**Solution:**
```
Only fix the specific issue I mentioned. Don't change working functionality. Follow the "one bug = one change" rule.
```

### Problem: Claude Code suggests enterprise-grade solutions  
**Solution:**
```
This is too complex for our constraints. We need a simple Flask solution that uses minimal resources. Check our PRD - we target non-technical users.
```

### Problem: Code suggestions don't match business logic
**Solution:**
```
Check the PRD user stories and business rules. The solution should match our activity-based model with automatic payment matching.
```

---

## Success Indicators

**Your workflow is working when:**
✅ Claude Code suggests simple Python solutions first  
✅ Bug fixes don't create new bugs  
✅ New features integrate cleanly with existing code  
✅ Memory usage stays low  
✅ Development stays focused on specific tasks  
✅ Solutions match PRD business requirements  

---

## Emergency Reset Protocol

**If Claude Code starts hallucinating or over-engineering:**

1. **Stop the session immediately**
2. **Start fresh session** with prompt template
3. **Reference specific guideline sections**
4. **Be extremely specific** about requirements
5. **Ask for explanation** of how solution meets constraints

---

## Tips for Success

### 🎯 **Stay Focused**
- One feature/bug at a time
- Resist urge to "improve while we're here"
- Complete current task before starting new ones

### 📖 **Reference Documentation**
- Point Claude Code to specific PRD/Guidelines sections
- Use documentation to resolve disagreements
- Keep business context in mind

### 🐍 **Python First**
- Always ask for Python solution first
- Question any JavaScript suggestions
- Prefer server-side over client-side logic

### ⚡ **Keep It Simple**
- Simplest solution that meets requirements
- Optimize for maintainability
- Remember: non-technical users need to understand the results

---

## Remember

**Your PRD and Guidelines are your shield against AI over-engineering.** Use them to keep Claude Code focused on building the simple, efficient, bug-free application your customers need for September launch.

**Goal:** Deliver a lightweight, reliable, profitable SaaS application - not an enterprise monolith.