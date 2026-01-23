<!-- mellea-pr-edited-marker: do not remove this marker -->
# Fix Unawaited Coroutines in Test Suite

Fixes #345

## Type of PR

- [x] Bug Fix
- [ ] New Feature
- [ ] Documentation
- [ ] Other

## Description
- [x] Link to Issue: #345

Fixes `RuntimeWarning: coroutine '...' was never awaited` in 2 test files by adding missing `await` keywords and converting sync tests to async where needed.

### Problem

Several tests were calling async methods without `await`, causing them to return coroutine objects that were never executed. The tests appeared to pass because creating a coroutine doesn't raise an exception, but the actual async code never ran - meaning these tests provided zero validation and could hide bugs.

**Affected tests:**
1. `test/backends/test_ollama.py::test_multiple_asyncio_runs` - Called `session.achat("hello")` without await
2. `test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_list` - Sync test calling async `Requirement.validate()` (2 occurrences)
3. `test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_table` - Sync test calling async `Requirement.validate()` (1 occurrence)

### Changes Made

#### 1. `test/backends/test_ollama.py` - Fix `test_multiple_asyncio_runs`
- Added `await` to `session.achat()` call
- Added assertion to validate the result
- Test now actually executes the async chat call and verifies event loop handling

**Context:** This test was added in commit 1e236dd (async overhaul) to verify multiple `asyncio.run()` calls work correctly. The missing `await` was an oversight.

#### 2. `test/stdlib/requirements/test_reqlib_markdown.py` - Convert to async tests
- Converted `test_markdown_list` from sync to async function
- Converted `test_markdown_table` from sync to async function  
- Added `await` to all `.validate()` calls
- Added assertions to validate `ValidationResult` objects
- Tests now actually execute markdown parsing/validation logic

**Context:** `Requirement.validate()` is an async method. Even though these Requirements use synchronous validation functions internally, the `.validate()` wrapper must be async to support both sync validators and LLM-as-a-Judge validation.

### Impact

**Before:** Tests passed but never executed validation logic  
**After:** Tests properly execute and validate async behavior

This fix ensures:
- Event loop handling is actually tested in `test_multiple_asyncio_runs`
- Markdown parsing/validation logic is actually tested in markdown tests
- Future bugs in these code paths will be caught by the test suite

### Results

**Before Fix:**
- 185 passed, 75 warnings
- 4 RuntimeWarnings about unawaited coroutines

**After Fix:**
- 185 passed, 72 warnings
- **0 RuntimeWarnings** ✅

### Testing
- [x] Tests added to the respective file if code was changed - N/A (fixing existing tests)
- [x] New code has 100% coverage if code as added - N/A (fixing existing tests)
- [x] Ensure existing tests and github automation passes

**Verification:**
```bash
# Individual tests - all passed with no warnings
uv run pytest test/backends/test_ollama.py::test_multiple_asyncio_runs -v -W error::RuntimeWarning
uv run pytest test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_list -v -W error::RuntimeWarning
uv run pytest test/stdlib/requirements/test_reqlib_markdown.py::test_markdown_table -v -W error::RuntimeWarning

# Full test suite - no RuntimeWarnings found
uv run pytest test -v -m "not qualitative"
# Result: 185 passed, 24 skipped, 69 deselected, 1 xpassed, 72 warnings (0 RuntimeWarnings)
```

### Files Changed
- `test/backends/test_ollama.py` - 3 lines modified
- `test/stdlib/requirements/test_reqlib_markdown.py` - 12 lines modified