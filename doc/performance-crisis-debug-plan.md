# 🚨 Performance Crisis Debug Plan - VPS Docker Deployment
**Date:** 2025-08-25  
**Issue:** 20-35 second page loads on VPS (https://lhgi.minipass.me) vs <1s on local  
**Root Cause:** Static assets failing to load (404 errors), Flask serving everything

---

## 📊 Critical Findings
- **35.93 seconds blocking time** on static assets
- **Multiple 404 errors** for CSS/JS files
- **0 bytes transferred** on failed requests
- **54MB of vendor assets** (Tabler: 45MB, TinyMCE: 9MB) causing bottlenecks

---

## 🎯 PHASE 1: DIAGNOSTICS & DATA COLLECTION
*Goal: Understand exactly what's failing without changing anything*

### Task 1.1: Performance Profiler Script
**Agent:** `backend-architect`
**File:** `/test/performance_profiler.py`
**Purpose:** Automated performance testing comparing local vs VPS
```
Actions:
- Use Playwright to load pages on both environments
- Capture HAR (HTTP Archive) data
- Measure load times for each asset
- Generate comparative report
- Output: performance_report.json with timings
```

### Task 1.2: Static Asset Validator
**Agent:** `code-security-reviewer`  
**File:** `/test/static_asset_checker.py`
**Purpose:** Identify all missing/inaccessible static files
```
Actions:
- Parse all HTML templates for asset references
- Check file existence locally
- Test HTTP accessibility on both URLs
- Generate 404 report with exact paths
- Output: missing_assets.txt
```

### Task 1.3: Network Monitor Script
**Agent:** `backend-architect`
**File:** `/test/network_monitor.py`
**Purpose:** Real-time network analysis using Playwright
```
Actions:
- Monitor specific pages: /edit-activity/1, /passports
- Capture network waterfall data
- Track blocking times per resource
- Identify timeout patterns
- Output: network_analysis.json
```

### Task 1.4: Request Logger Middleware
**Agent:** `backend-architect`
**File:** `/test/request_logger.py`
**Purpose:** Server-side request timing
```
Actions:
- Create Flask middleware for request logging
- Log every request with timing
- Identify requests >1s
- Check if Flask serves static files
- Output: request_timings.log
```

---

## 🛠️ PHASE 2: ANALYSIS & REPORTING
*Goal: Process collected data to identify exact bottlenecks*

### Task 2.1: Performance Analysis Report
**Agent:** `trend-researcher`
**Input:** All Phase 1 outputs
**Purpose:** Comprehensive analysis of performance data
```
Actions:
- Correlate 404 errors with slow loads
- Identify critical path resources
- Calculate impact of each missing asset
- Generate priority fix list
- Output: analysis_report.md
```

### Task 2.2: Database Query Analyzer
**Agent:** `backend-architect`
**File:** `/test/db_query_analyzer.py`
**Purpose:** Check for database bottlenecks
```
Actions:
- Add SQLAlchemy event listeners
- Log all queries with execution time
- Identify N+1 query problems
- Find slow queries (>100ms)
- Output: slow_queries.log
```

---

## 🔧 PHASE 3: QUICK FIXES (Without Docker Access)
*Goal: Implement fixes that don't require VPS access*

### Task 3.1: CDN Fallback Implementation
**Agent:** `ui-designer`
**Files:** `/templates/base.html`, `/templates/partials/cdn_assets.html`
**Purpose:** Add CDN links for large vendor libraries
```
Actions:
- Add CDN fallbacks for Tabler.io
- Add CDN for TinyMCE
- Implement local fallback logic
- Add integrity checks
```

### Task 3.2: Static Asset Optimization
**Agent:** `flask-ui-developer`
**Purpose:** Optimize and compress assets
```
Actions:
- Minify custom CSS/JS files
- Combine multiple small files
- Add proper cache headers
- Implement versioning strategy
- Remove unused vendor files
```

### Task 3.3: Production Configuration
**Agent:** `backend-architect`
**File:** `/production_config.py`
**Purpose:** Flask configuration for production
```
Config additions:
- SEND_FILE_MAX_AGE_DEFAULT = 31536000
- Static file serving optimizations
- Proxy-aware configurations
- Database connection pooling
```

### Task 3.4: Nginx Configuration Generator
**Agent:** `backend-architect`
**File:** `/doc/nginx_config_template.conf`
**Purpose:** Nginx config for VPS admin
```
Generate:
- Static file serving rules
- Gzip compression config
- Cache control headers
- Proxy pass settings for Flask
```

---

## 🧹 PHASE 4: CODE CLEANUP
*Goal: Remove technical debt and unused code*

### Task 4.1: Dead Code Removal
**Agent:** `code-security-reviewer`
**Purpose:** Clean up unused models and endpoints
```
Actions:
- Remove Pass model (replaced by Passport)
- Clean 62+ references to old Pass model
- Remove duplicate imports (18 found)
- Delete unused endpoints
- Remove orphaned templates
```

### Task 4.2: Import Optimization
**Agent:** `js-code-reviewer`
**File:** `app.py`
**Purpose:** Clean up and optimize imports
```
Actions:
- Consolidate duplicate imports
- Remove unused imports
- Organize import structure
- Add lazy loading where appropriate
```

### Task 4.3: Database Migration
**Agent:** `backend-architect`
**Purpose:** Clean up database schema
```
Actions:
- Create migration to drop Pass table
- Remove unused columns
- Add missing indexes
- Optimize foreign keys
```

---

## 🚀 PHASE 5: EMERGENCY BYPASS
*Goal: Make site usable immediately*

### Task 5.1: Emergency CDN Switch
**Agent:** `flask-ui-developer`
**File:** `/test/emergency_cdn_switch.py`
**Priority:** URGENT - RUN FIRST
```
Actions:
- Script to replace all local asset URLs with CDN
- Temporary fix for production
- Makes site usable while debugging
- Revertable with single command
```

---

## 📈 EXPECTED TIMELINE & RESULTS

### Day 1 (Immediate)
- **Tasks:** 5.1, 1.1, 1.2, 1.3
- **Result:** Site usable with CDN bypass, diagnostics running
- **Performance:** 20s → 5s

### Day 2
- **Tasks:** 2.1, 2.2, 3.1, 3.2
- **Result:** Full analysis complete, optimizations applied
- **Performance:** 5s → 2s

### Day 3
- **Tasks:** 3.3, 3.4, 4.1, 4.2
- **Result:** Clean codebase, production-ready config
- **Performance:** 2s → <1s

---

## 🔍 MONITORING & VALIDATION

### Success Metrics
- [ ] Page load time <2 seconds
- [ ] Zero 404 errors on static assets
- [ ] All assets served with proper cache headers
- [ ] Database queries <100ms
- [ ] No Flask static file serving in production

### Validation Script
**Agent:** `backend-architect`
**File:** `/test/performance_validator.py`
```
Run after each phase to measure improvement
```

---

## 📝 NOTES FOR VPS ADMIN

Once we identify the issues, provide the VPS admin with:
1. `nginx_config_template.conf` - Proper static file serving
2. `docker-compose.yml` updates - Volume mappings for static files
3. Environment variable configurations
4. Deployment checklist

---

## 🎯 AGENT ASSIGNMENTS SUMMARY

| Agent | Task Count | Primary Responsibility |
|-------|------------|------------------------|
| `backend-architect` | 8 tasks | Scripts, config, database |
| `flask-ui-developer` | 3 tasks | UI fixes, CDN, templates |
| `code-security-reviewer` | 2 tasks | Validation, cleanup |
| `ui-designer` | 1 task | CDN implementation |
| `trend-researcher` | 1 task | Analysis report |
| `js-code-reviewer` | 1 task | Import optimization |

---

## 🚦 EXECUTION ORDER

1. **URGENT:** Task 5.1 (Emergency CDN Switch)
2. **Phase 1:** All diagnostic scripts (parallel)
3. **Phase 2:** Analysis (after Phase 1)
4. **Phase 3:** Quick fixes (parallel)
5. **Phase 4:** Cleanup (after fixes verified)

---

## ✅ CHECKLIST FOR COMPLETION

- [ ] All diagnostic scripts created and run
- [ ] Performance report generated
- [ ] CDN fallbacks implemented
- [ ] Production config created
- [ ] Nginx template provided
- [ ] Dead code removed
- [ ] Database optimized
- [ ] Final performance <1s
- [ ] Documentation updated
- [ ] VPS admin briefed

---

**END OF PLAN**