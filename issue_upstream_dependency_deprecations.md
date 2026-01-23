# Upstream Dependency Deprecation Warnings 📦

**Priority:** Medium

## Problem

Multiple deprecation warnings from upstream dependencies (LiteLLM, docling-core, aiohttp) that we don't directly control. These warnings indicate the dependencies are using deprecated APIs that may break in future versions.

## Affected Dependencies

### 1. LiteLLM - Pydantic `.dict()` Method

**Warning:**
```
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
```

**Location:** `/litellm/litellm_core_utils/streaming_handler.py:1855`

**Affected Tests:**
- `test/backends/test_litellm_ollama.py::test_async_parallel_requests`

**Issue:** LiteLLM is using the deprecated Pydantic v1 `.dict()` method instead of the v2 `.model_dump()` method.

---

### 2. Docling-Core - Field Name Change

**Warning:**
```
DeprecationWarning: Field `annotations` is deprecated; use `meta` instead.
```

**Location:** `/docling_core/transforms/serializer/markdown.py:490`

**Affected Tests:**
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_basics`
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_markdown`
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_save`

**Issue:** Docling-core is using a deprecated field name internally.

---

### 3. aiohttp - Cleanup Parameter

**Warning:**
```
DeprecationWarning: enable_cleanup_closed ignored because https://github.com/python/cpython/pull/118960 
is fixed in Python version sys.version_info(major=3, minor=12, micro=8, releaselevel='final', serial=0)
```

**Location:** `/aiohttp/connector.py:963`

**Affected Tests:** Multiple tests using LiteLLM with aiohttp

**Issue:** aiohttp is passing a parameter that's no longer needed in Python 3.12.8+. This is informational rather than breaking.

---

### 4. Pydantic Serialization Warnings

**Warning:**
```
UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue(Expected 10 fields but got 5: Expected `Message` - serialized value may not be as expected)
```

**Affected Tests:**
- `test/backends/test_litellm_ollama.py` (multiple tests)
- `test/backends/test_tool_calls.py::test_tool_called`

**Issue:** LiteLLM's Pydantic models don't match the actual response structure from Ollama.

---

## Impact

- **Timeline:** Varies by dependency
- **Scope:** Multiple test files, but issues are in dependencies not our code
- **Risk:** Low to Medium - depends on when dependencies update
- **Effort:** Low - mainly dependency updates

## Solution Approach

### Option 1: Update Dependencies (Recommended)
Check if newer versions of these dependencies have fixed the issues:

```bash
# Check current versions
uv pip list | grep -E "(litellm|aiohttp|docling-core)"

# Update to latest versions
uv pip install --upgrade litellm aiohttp docling-core

# Test after updates
uv run pytest test -v -W error::DeprecationWarning
```

### Option 2: Report Upstream
If updates don't fix the issues, report to the respective projects:
- LiteLLM: https://github.com/BerriAI/litellm/issues
- docling-core: https://github.com/DS4SD/docling-core/issues
- aiohttp: https://github.com/aio-libs/aiohttp/issues

### Option 3: Suppress Warnings (Temporary)
If fixes aren't available yet, suppress specific warnings in `pytest.ini`:

```ini
[tool.pytest.ini_options]
filterwarnings = [
    "ignore::pydantic.warnings.PydanticDeprecatedSince20",
    "ignore:Field `annotations` is deprecated:DeprecationWarning",
]
```

**Note:** Only suppress after confirming the warnings don't affect functionality.

## Action Items

- [ ] Check current versions of affected dependencies
- [ ] Update dependencies to latest versions
- [ ] Run test suite to verify warnings are resolved
- [ ] If warnings persist, check dependency issue trackers
- [ ] Report issues upstream if not already reported
- [ ] Document any suppressions with justification

## Verification

```bash
# Check dependency versions
uv pip list | grep -E "(litellm|aiohttp|docling-core|pydantic)"

# Update dependencies
uv pip install --upgrade litellm aiohttp docling-core

# Run tests and check for deprecation warnings
uv run pytest test -v 2>&1 | grep -E "(DeprecationWarning|PydanticDeprecated)" | sort | uniq

# Count remaining warnings
uv run pytest test -v 2>&1 | grep -c "DeprecationWarning"
```

## Notes

- **aiohttp warning** is informational - the parameter is simply ignored in Python 3.12.8+
- **Pydantic warnings** may not affect functionality but indicate model mismatches
- **LiteLLM and docling-core** warnings are more concerning as they use deprecated APIs

## Priority

Medium - These are upstream issues that we can't directly fix, but we should:
1. Keep dependencies updated
2. Monitor for fixes
3. Report issues if not already known
4. Consider alternatives if dependencies become unmaintained