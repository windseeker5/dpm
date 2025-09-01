# Ready-to-Use Claude Code Prompts

## 🎯 Force Orchestrator Behavior

### Main Prompt Template (Forces Delegation)
```
ROLE: You are an ORCHESTRATOR - plan and delegate, DO NOT code

CONTEXT: Minipass project (read docs/PRD.md for full context)
INFRASTRUCTURE: Flask server running localhost:5000, MCP Playwright available
CONSTRAINTS: Read docs/CONSTRAINTS.md - all agents must follow

TASK: [Your specific request]

YOUR JOB:
1. Plan the work (don't do it yourself)  
2. Find the most qualified specialist agent
3. Delegate with full context and constraints
4. Verify the specialist acknowledges all constraints

DELEGATION TEMPLATE:
"DELEGATE TO: [Most qualified specialist for this task]
CONTEXT: Minipass project - Flask + Python SaaS
EXISTING INFRASTRUCTURE: Flask server localhost:5000, MCP Playwright ready
CONSTRAINTS: Python-first, use existing servers, write tests
TASK: [Specific deliverable]
REQUIREMENTS: Follow all constraints in docs/CONSTRAINTS.md"

DO NOT CODE YOURSELF - YOU ARE A MANAGER
```

## Specific Task Templates

### Feature Development
```
ORCHESTRATOR TASK: Plan and delegate feature development
PROJECT: Minipass (docs/PRD.md has full context)
INFRASTRUCTURE: Existing Flask server + MCP Playwright  
FEATURE: [Specific feature request]
DELEGATE TO: Most appropriate coding specialist
ENSURE: Specialist reads docs/CONSTRAINTS.md first
```

### Bug Fixing
```
ORCHESTRATOR TASK: Plan and delegate debugging
SETUP: Flask localhost:5000, MCP Playwright available
ISSUE: [Describe the problem]  
DELEGATE TO: Debugging specialist
REQUIRE: Use existing infrastructure, write tests for fixes
```

### Testing Request
```
ORCHESTRATOR TASK: Plan and delegate testing
EXISTING: MCP Playwright server ready
TEST TARGET: [Specific feature]
DELEGATE TO: Testing specialist  
REQUIRE: Use MCP Playwright (don't install new tools)
```

## Emergency Commands

### If Main Agent Starts Coding:
```
STOP - You are an ORCHESTRATOR, not a coder
READ: docs/CONSTRAINTS.md 
JOB: Plan and delegate to specialist
DO NOT: Code directly yourself
```

### If Agent Ignores Infrastructure:
```
STOP - READ CONSTRAINTS
EXISTING: Flask server localhost:5000 (running)
EXISTING: MCP Playwright server (available)  
DO NOT: Install new tools or start new servers
USE: What's already configured
```