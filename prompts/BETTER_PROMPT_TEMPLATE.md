# 🎯 Better Prompt Template for Claude Code

## The Problem with Your Current Prompt:
- Too many instructions at once
- Mixing orchestration with implementation
- Conflicting requirements (orchestrator vs doing the work)
- Too many "Always" and "Do not" rules that confuse the AI

## New Simplified Prompt Template:

```
Please implement the plan in: /path/to/plan.md

CONTEXT:
- Flask server is running on localhost:5000 (login: kdresdell@gmail.com / admin123)
- We use Tabler.io CSS framework
- Keep JavaScript minimal (<50 lines per file)

APPROACH:
1. Read the plan first
2. Implement one phase at a time
3. Test each change before moving to the next
4. If something doesn't work, tell me instead of over-engineering

TESTING:
- Create simple Python unit tests in /test/ folder
- Use MCP Playwright for UI testing when needed
- Save any screenshots to /test/playwright/

That's it. Start with Phase 1 of the plan.
```

## Why This Works Better:

### 1. **Clear Structure**
- CONTEXT: What exists
- APPROACH: How to work
- TESTING: How to verify
- No conflicting instructions

### 2. **Less is More**
- 10 lines instead of 20+
- Clear, not overwhelming
- Room for the AI to think

### 3. **Phase-by-Phase**
- "Start with Phase 1" - clear starting point
- Prevents trying to do everything at once
- Natural checkpoints

### 4. **Positive Instructions**
Instead of "DO NOT do X, Y, Z" (which often backfires), use:
- "Keep JavaScript minimal"
- "Test each change"
- "Tell me if something doesn't work"

## Alternative Templates for Different Situations:

### For Bug Fixes:
```
BUG: [describe the issue]
FILE: [where the bug likely is]

Fix this bug following our constraints:
- Flask on port 5000
- Minimal JavaScript (<50 lines)
- Test the fix with MCP Playwright
```

### For New Features:
```
FEATURE: [what to build]
EXAMPLE: [point to similar existing code]

Build this using:
- Our existing patterns from [file]
- Tabler.io components
- Python/Flask (not JavaScript) when possible

Test and show me it works.
```

### For Refactoring:
```
SIMPLIFY: [file or feature]
GOAL: Reduce code by 50% while keeping functionality

Rules:
- Keep existing functionality
- Use our current CSS (Tabler.io)
- Test that nothing breaks
```

## The Magic Formula:

### ✅ GOOD Prompt Structure:
1. **WHAT** - Clear, single objective
2. **HOW** - 3-5 key constraints
3. **VERIFY** - How to test success

### ❌ BAD Prompt Structure:
1. Long list of "Always do..."
2. Long list of "Never do..."
3. Conflicting instructions
4. No clear starting point

## Pro Tips:

### 1. **One Goal at a Time**
Instead of: "Implement this entire plan"
Use: "Implement Phase 1 of this plan"

### 2. **Point to Examples**
Instead of: "Use our style"
Use: "Style it like the dashboard at /dashboard"

### 3. **Explicit Over Implicit**
Instead of: "You know our Flask server"
Use: "Flask server on localhost:5000 (kdresdell@gmail.com/admin123)"

### 4. **Trust with Guardrails**
Instead of: "Don't over-engineer" (vague)
Use: "If it takes >50 lines of JS, stop and ask"

## Your Specific Case - Email Template Simplification:

```
Implement Phase 1 from: /home/kdresdell/Documents/DEV/minipass_env/app/plans/email_template_simplification.md

CONTEXT:
- Flask on localhost:5000 (kdresdell@gmail.com/admin123)
- Current page: /activity/1/email-templates
- Keep the existing modals

TASK:
Just create the thumbnail generation route first.
Test that it generates real preview images.
Show me the result before moving to Phase 2.
```

## Why Orchestrator Mode Usually Fails:

When you say "act as an orchestrator and delegate", Claude gets confused because:
1. There aren't really other agents to delegate to
2. It adds unnecessary complexity
3. It prevents direct action

**Better approach**: Let Claude work directly, one step at a time.

## The 80/20 Rule for Prompts:

**80% Success Formula:**
- Clear single task
- 3-5 constraints max
- How to verify success

**The 20% That Causes 80% of Problems:**
- Too many rules
- Conflicting instructions  
- No clear starting point
- Asking for "orchestration" when you want implementation

## Test This Approach:

Try this simple prompt for your email template task:

```
Read the plan at: /home/kdresdell/Documents/DEV/minipass_env/app/plans/email_template_simplification.md

Start with Phase 1 only - create the thumbnail generation.
Use Flask on port 5000.
Show me it works, then we'll do Phase 2.
```

That's it. Simple, clear, effective.