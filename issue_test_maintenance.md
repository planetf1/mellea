# Test Suite Maintenance & Cleanup 🧹

**Priority:** Low

## Problem

Minor issues and cleanup tasks that should be addressed for code quality and test suite health.

## Items

### 1. XPASS Tests (2 instances)

**Issue:** Tests marked with `@pytest.mark.xfail` are now passing. These markers should be removed.

**Affected Tests:**
- `test/backends/test_ollama.py::test_generate_from_raw_with_format` - XPASS
- `test/backends/test_litellm_watsonx.py::test_multiple_async_funcs` - XPASS

**Action:**
```python
# Remove the @pytest.mark.xfail decorator from these tests
# They're now working correctly
```

**Impact:** Low - Tests pass, but the xfail marker is misleading

---

### 2. Test Suite Timeout

**Issue:** Full test suite times out after 600s (10 minutes).

**Current Behavior:**
```bash
uv run pytest test -v
# Times out after 600s
```

**Possible Solutions:**
1. Split tests into fast/slow groups
2. Use `pytest-xdist` for parallel execution
3. Increase timeout for CI
4. Mark slow tests with `@pytest.mark.slow`

**Recommended Approach:**
```python
# In pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "qualitative: marks tests that check LLM output quality",
]

# Then mark slow tests
@pytest.mark.slow
def test_long_running_operation():
    ...

# Run fast tests only
pytest -m "not slow and not qualitative"
```

**Impact:** Low - Tests complete eventually, but CI/local dev experience could be better

---

### 3. Deprecated ABC Warning

**Warning:**
```
DeprecationWarning: Use BaseMetaSerializer() instead.
```

**Affected Tests:**
- `test/backends/test_tool_calls.py::test_tool_called_from_context_action`

**Location:** `<frozen abc>:106`

**Action Required:**
- [ ] Run with traceback to identify source: `pytest -W error::DeprecationWarning --tb=long`
- [ ] Identify which library is using deprecated ABC API
- [ ] Update library or our usage

**Impact:** Low - Need investigation to determine source

---

### 4. Test Organization

**Observation:** Some test files have overlapping coverage:
- `test/backends/test_watsonx.py` - Uses deprecated Watsonx backend
- `test/backends/test_litellm_watsonx.py` - Uses LiteLLM with Watsonx

**Recommendation:**
- [ ] Archive or remove `test_watsonx.py` after migrating all tests
- [ ] Consolidate Watsonx testing in `test_litellm_watsonx.py`
- [ ] Update test documentation

**Impact:** Low - Organizational clarity

---

### 5. Test Fixture Consistency

**Observation:** Different patterns for session fixtures across test files.

**Examples:**
```python
# Pattern 1: Function scope
@pytest.fixture(scope="function")
def session():
    session = MelleaSession(...)
    yield session
    session.reset()

# Pattern 2: Module scope
@pytest.fixture(scope="module")
def session():
    return MelleaSession(...)

# Pattern 3: No cleanup
@pytest.fixture
def session():
    return MelleaSession(...)
```

**Recommendation:**
- [ ] Standardize on function scope with cleanup
- [ ] Document fixture patterns in test README
- [ ] Consider creating shared fixtures in `conftest.py`

**Impact:** Low - Consistency and maintainability

---

## Action Items

### Immediate (Quick Wins)
- [ ] Remove `@pytest.mark.xfail` from passing tests (2 files)
- [ ] Add `@pytest.mark.slow` to long-running tests

### Short-term
- [ ] Investigate ABC deprecation warning
- [ ] Document test organization strategy
- [ ] Standardize fixture patterns

### Long-term
- [ ] Implement parallel test execution with pytest-xdist
- [ ] Create test performance benchmarks
- [ ] Add test suite documentation

## Verification

```bash
# Check for XPASS tests
uv run pytest test -v | grep XPASS

# Run fast tests only (after marking slow tests)
uv run pytest test -m "not slow and not qualitative" -v

# Check test execution time
uv run pytest test --durations=10
```

## Related Issues

- Resource leaks (separate issue) - Should be fixed first
- Unawaited coroutines (separate issue) - Should be fixed first
- Deprecation warnings (separate issue) - Medium priority

---

**Priority:** Low  
**Impact:** Improves code quality and developer experience, but doesn't affect test validity or functionality.