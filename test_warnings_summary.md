# Test Suite Warnings Analysis - Summary

**Date:** 2026-01-23  
**Test Command:** `uv run pytest test -v -m "not qualitative"`  
**Results:** 185 passed, 24 skipped, 69 deselected, 1 xpassed, **75 warnings**

## Executive Summary

Analyzed test suite warnings and categorized into 4 priority groups. Critical issues (unawaited coroutines) compromise test validity and should be addressed immediately. Resource leaks and deprecations should be addressed soon to prevent future issues.

## Issue Categories

### 🔴 High Priority - Critical

#### 1. Unawaited Coroutines (3 test files)
**File:** `issue_unawaited_coroutines.md`  
**PR Template:** `pr_template_unawaited_coroutines.md`

**Impact:** Tests pass but don't execute async code - false positives that hide bugs

**Affected:**
- `test/backends/test_ollama.py:187` - `session.achat()` never awaited
- `test/stdlib/requirements/test_reqlib_markdown.py:49,53,57` - `.validate()` never awaited

**Effort:** Low (3 files, ~10 lines changed)  
**Timeline:** Immediate

---

### 🟠 High Priority - Resource Management

#### 2. Resource Leaks (20+ test files)
**File:** `issue_resource_leaks.md`

**Impact:** 75+ warnings about unclosed sockets, transports, event loops. Indicates cleanup issues that could affect production.

**Most Affected:**
- `test/backends/test_ollama.py::test_client_cache` (10+ warnings)
- `test/stdlib/components/docs/test_richdocument.py` (15+ warnings)
- `test/backends/test_watsonx.py::test_client_cache` (5+ warnings)

**Root Causes:**
- Backend clients not properly closed
- `session.reset()` incomplete
- Event loops not cleaned up
- aiohttp sessions left open

**Effort:** Medium (requires fixture refactoring)  
**Timeline:** This sprint

---

### 🟡 Medium Priority - Future Breaking

#### 3. Deprecation Warnings (Multiple categories)
**File:** `issue_deprecation_warnings.md`

**Impact:** Will break in future versions. Some have specific deadlines.

**Categories:**
1. **Pillow** (2 files) - Breaks Oct 2026 - EASY FIX
2. **Granite Model** (multiple files) - Deprecated until Feb 2026 - EASY FIX
3. **Watsonx Backend** (3 files) - Our own deprecation - MIGRATION NEEDED
4. **Docling/Pydantic/aiohttp** - Upstream issues - UPDATE DEPS

**Effort:** Low to Medium (depends on category)  
**Timeline:** Next sprint

---

### 🟢 Low Priority - Maintenance

#### 4. Test Suite Cleanup
**File:** `issue_test_maintenance.md`

**Impact:** Code quality and developer experience improvements.

**Items:**
- Remove `@pytest.mark.xfail` from 2 passing tests
- Investigate ABC deprecation warning
- Address test suite timeout (10 min)
- Standardize fixture patterns
- Consolidate Watsonx test files

**Effort:** Low  
**Timeline:** Ongoing

---

## Recommended Action Plan

### Week 1 (Immediate)
1. **Fix unawaited coroutines** - 3 files, critical for test validity
   - Use PR template: `pr_template_unawaited_coroutines.md`
   - Estimated: 1-2 hours

2. **Quick deprecation fixes** - Pillow and Granite model
   - Remove `"RGB"` parameter from `Image.fromarray()` (2 files)
   - Update model ID from granite-3 to granite-4 (search/replace)
   - Estimated: 30 minutes

### Week 2-3 (Short-term)
3. **Fix resource leaks** - Requires fixture refactoring
   - Add proper cleanup to backend classes
   - Update `session.reset()` to close all resources
   - Fix test fixtures with try/finally
   - Estimated: 1-2 days

4. **Migrate Watsonx tests** - From deprecated backend to LiteLLM
   - Update `test/backends/test_watsonx.py`
   - Consolidate with `test_litellm_watsonx.py`
   - Estimated: 4-6 hours

### Week 4+ (Medium-term)
5. **Update dependencies** - Address upstream deprecations
   - `uv pip install --upgrade litellm aiohttp docling-core`
   - Test and verify
   - Estimated: 2-3 hours

6. **Test maintenance** - Ongoing improvements
   - Remove xfail markers
   - Add slow test markers
   - Standardize fixtures
   - Estimated: Ongoing

---

## Files Created

All issue documents are ready for GitHub:

1. **`issue_unawaited_coroutines.md`** - Critical async test issues
2. **`pr_template_unawaited_coroutines.md`** - PR template with implementation details
3. **`issue_resource_leaks.md`** - Socket/transport cleanup issues
4. **`issue_deprecation_warnings.md`** - Dependency deprecations
5. **`issue_test_maintenance.md`** - Low-priority cleanup tasks
6. **`test_warnings_summary.md`** - This file

## Verification Commands

```bash
# Run tests with warnings as errors (after fixes)
uv run pytest test -v -W error::RuntimeWarning -W error::ResourceWarning

# Check for specific warning types
uv run pytest test -v 2>&1 | grep -E "(RuntimeWarning|ResourceWarning|DeprecationWarning)" | wc -l

# Run fast tests only
uv run pytest test -v -m "not qualitative"

# Check test durations
uv run pytest test --durations=10
```

## Metrics

**Current State:**
- Total warnings: 75
- Critical issues: 3 test files
- Resource warnings: 50+
- Deprecation warnings: 20+
- Test execution time: ~2 min (fast), 10+ min (full)

**Target State:**
- Total warnings: 0
- All tests execute actual validation logic
- All resources properly cleaned up
- No deprecated APIs in use
- Test execution time: <5 min (full suite)

---

## Next Steps

1. Create GitHub issues from markdown files
2. Prioritize and assign to sprint
3. Start with unawaited coroutines (highest impact, lowest effort)
4. Track progress and update this document

**Questions?** See individual issue files for detailed analysis and solutions.