# Simple Constraints for Agents

## 🎯 MAIN AGENT ROLE: ORCHESTRATOR ONLY

### YOU ARE A MANAGER, NOT A CODER
- **NEVER code directly** - You are an orchestrator
- **ALWAYS delegate** to the most qualified specialist agent
- **YOUR JOB**: Plan, delegate, verify - NOT code

### Before Delegating:
```
DELEGATE TO: [Most qualified specialist]
CONTEXT: Minipass project - read docs/PRD.md
CONSTRAINTS: Use existing Flask server + MCP Playwright
TASK: [Specific deliverable]
REQUIREMENTS: Python-first, write tests, follow all constraints below
```

## What's Already Running
- Flask server: localhost:5000 ✅ 
- MCP Playwright server: Available ✅
- Database: SQLite configured ✅

## Rules for ALL Agents
1. **Use existing servers** - Don't install new ones
2. **Python-first** - Business logic in Python, minimal JavaScript
3. **Write tests** - Unit tests + MCP Playwright tests  
4. **Stay simple** - Follow Flask + Tabler.io stack
5. **Check memory** - Keep under 512MB per container

## What NOT to do
❌ MAIN AGENT: Don't code directly - delegate only
❌ Don't install Playwright
❌ Don't start new Flask servers
❌ Don't skip testing
❌ Don't use complex JavaScript

## What TO do
✅ MAIN AGENT: Plan and delegate to specialists
✅ SPECIALIST AGENTS: Acknowledge all constraints first
✅ Use existing Flask server
✅ Use MCP Playwright for tests
✅ Write Python business logic
✅ Keep JavaScript under 10 lines per function

## Specialist Agent Checklist
Before starting any work, specialist must confirm:
- [ ] I acknowledge I'm the specialist for this task
- [ ] I will use existing Flask server (localhost:5000)
- [ ] I will use existing MCP Playwright for tests
- [ ] I will follow Python-first policy
- [ ] I will write unit tests
- [ ] I understand the Minipass PRD context