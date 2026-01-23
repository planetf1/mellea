# Unawaited Coroutines in Tests 🛠️

**Priority:** High (Major)

## Problem

Several tests trigger `RuntimeWarning: coroutine '...' was never awaited`, indicating async functions are called without `await`. These tests are **false positives** — they pass because creating a coroutine object doesn't raise an exception, but the actual async code **never executes**.

## Impact

- **Test validity compromised**: Tests appear to pass but provide zero validation
- **False confidence**: Bugs in async code paths go undetected
- **Coverage illusion**: Tests show in coverage reports but don't test anything

## Affected Tests

### 1. `test/backends/test_ollama.py:187` - `test_multiple_asyncio_runs`
**Warning:** `RuntimeWarning: coroutine 'MelleaSession.achat' was never awaited`

**Issue:** Calls `session.achat("hello")` without `await` inside async function.

**Should validate:** Multiple `asyncio.run()` calls work without event loop conflicts.

### 2. `test/stdlib/requirements/test_reqlib_markdown.py` (lines 49, 53, 57)
**Warning:** `RuntimeWarning: coroutine 'Requirement.validate' was never awaited`

**Issue:** Synchronous test functions calling async `Requirement.validate()` method.

**Should validate:** Markdown list/table parsing and validation logic.

## Why This Matters

If someone breaks:
- Event loop handling → `test_multiple_asyncio_runs` won't catch it
- Markdown parsing logic → `test_markdown_list/table` won't catch it

The tests would still pass, giving false confidence.

## Action Items

- [ ] Fix `test_multiple_asyncio_runs`: Add `await` before `session.achat("hello")`
- [ ] Fix `test_markdown_list`: Convert to `async def`, add `await` before `.validate()` calls
- [ ] Fix `test_markdown_table`: Convert to `async def`, add `await` before `.validate()` call
- [ ] Scan for similar issues: `grep -rn "\.a[a-z_]*(" test/ | grep -v "await"`

---

**See PR template for implementation details and verification steps.**