# PR: Fix Unawaited Coroutines in Test Suite

## Summary

Fixes `RuntimeWarning: coroutine '...' was never awaited` in 2 test files by adding missing `await` keywords and converting sync tests to async where needed. These tests were passing but not actually executing their async validation logic.

## Problem

Several tests were calling async methods without `await`, causing them to return coroutine objects that were never executed. The tests appeared to pass because creating a coroutine doesn't raise an exception, but the actual async code never ran - meaning these tests provided zero validation and could hide bugs.

## Changes

### 1. `test/backends/test_ollama.py` - Fix `test_multiple_asyncio_runs`

**Before:**
```python
def test_multiple_asyncio_runs(session):
    async def test():
        session.achat("hello")  # ❌ Missing await - coroutine never executes
    
    asyncio.run(test())
    asyncio.run(test())
```

**After:**
```python
def test_multiple_asyncio_runs(session):
    async def test():
        result = await session.achat("hello")  # ✅ Properly awaited
        assert result is not None  # Added validation
    
    asyncio.run(test())
    asyncio.run(test())
```

**Context:** This test was added in commit 1e236dd (async overhaul) to verify multiple `asyncio.run()` calls work correctly. The missing `await` was likely an oversight during implementation.

---

### 2. `test/stdlib/requirements/test_reqlib_markdown.py` - Fix async test functions

**Before:**
```python
def test_markdown_list():  # ❌ Sync function calling async method
    assert is_markdown_list.validate(None, MARKDOWN_LIST_CTX)  # Returns coroutine
    assert len(as_markdown_list(MARKDOWN_LIST_CTX)) == 3
    assert len(as_markdown_list(MARKDOWN_OL_LIST_CTX)) == 4
    assert type(as_markdown_list(MARKDOWN_OL_LIST_CTX)[0]) is str
    assert is_markdown_list.validate(None, MARKDOWN_OL_LIST_CTX)  # Returns coroutine

def test_markdown_table():  # ❌ Sync function calling async method
    assert is_markdown_table.validate(None, MARKDOWN_TABLE_CONTEXT)  # Returns coroutine
```

**After:**
```python
async def test_markdown_list():  # ✅ Async function
    result = await is_markdown_list.validate(None, MARKDOWN_LIST_CTX)
    assert result  # Validate the ValidationResult
    assert len(as_markdown_list(MARKDOWN_LIST_CTX)) == 3
    assert len(as_markdown_list(MARKDOWN_OL_LIST_CTX)) == 4
    assert type(as_markdown_list(MARKDOWN_OL_LIST_CTX)[0]) is str
    result = await is_markdown_list.validate(None, MARKDOWN_OL_LIST_CTX)
    assert result

async def test_markdown_table():  # ✅ Async function
    result = await is_markdown_table.validate(None, MARKDOWN_TABLE_CONTEXT)
    assert result
```

**Context:** `Requirement.validate()` is an async method (see `mellea/core/requirement.py:116`). Even though these Requirements use synchronous validation functions internally (`_md_list`, `_md_table`), the `.validate()` wrapper must be async to support both sync validators and LLM-as-a-Judge validation. These tests were likely written before the API became async or were never updated.

## Testing

### Individual Test Verification
```bash
# Test 1: test_multiple_asyncio_runs
uv run pytest test/backends/test_ollama.py::test_multiple_asyncio_runs -v -W error::RuntimeWarning
# ✅ PASSED - No RuntimeWarnings

# Test 2: test_markdown_list
uv run pytest test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_list -v -W error::RuntimeWarning
# ✅ PASSED - No RuntimeWarnings

# Test 3: test_markdown_table
uv run pytest test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_table -v -W error::RuntimeWarning
# ✅ PASSED - No RuntimeWarnings
```

### Verification Commands
```bash
# Verify no RuntimeWarnings in affected tests
uv run pytest test/backends/test_ollama.py::test_multiple_asyncio_runs \
             test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_list \
             test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_table \
             -v -W error::RuntimeWarning

# Check for any remaining RuntimeWarnings in full suite
uv run pytest test -v -m "not qualitative" 2>&1 | grep "RuntimeWarning: coroutine"
```

## Impact

**Before:** Tests passed but never executed validation logic  
**After:** Tests properly execute and validate async behavior

This fix ensures:
- Event loop handling is actually tested in `test_multiple_asyncio_runs`
- Markdown parsing/validation logic is actually tested in markdown tests
- Future bugs in these code paths will be caught by the test suite

## Files Changed
- `test/backends/test_ollama.py` - 3 lines modified
- `test/stdlib/requirements/test_reqlib_markdown.py` - 12 lines modified

## Checklist
- [x] All affected tests pass
- [x] No RuntimeWarnings emitted
- [x] Tests now actually execute async code
- [x] Added assertions where missing
- [x] No regressions in other tests