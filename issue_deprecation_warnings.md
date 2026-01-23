# Deprecation Warnings in Test Suite ⚠️

**Priority:** Medium

## Problem

Multiple deprecation warnings from dependencies that will cause failures in future versions. These need to be addressed before the deprecated features are removed.

## Categories

### 1. Pillow Image Mode Deprecation (2 instances)

**Warning:**
```
DeprecationWarning: 'mode' parameter is deprecated and will be removed in Pillow 13 (2026-10-15)
```

**Affected Tests:**
- `test/backends/test_vision_ollama.py:38`
- `test/backends/test_vision_openai.py:48`

**Current Code:**
```python
@pytest.fixture(scope="module")
def pil_image():
    width = 200
    height = 150
    random_pixel_data = np.random.randint(
        0, 256, size=(height, width, 3), dtype=np.uint8
    )
    random_image = Image.fromarray(random_pixel_data, "RGB")  # ❌ Deprecated
    yield random_image
    del random_image
```

**Fix:**
```python
@pytest.fixture(scope="module")
def pil_image():
    width = 200
    height = 150
    random_pixel_data = np.random.randint(
        0, 256, size=(height, width, 3), dtype=np.uint8
    )
    random_image = Image.fromarray(random_pixel_data)  # ✅ Mode inferred from array
    yield random_image
    del random_image
```

**Urgency:** High - Breaks in October 2026 (8 months)

---

### 2. Pydantic `.dict()` Method Deprecation (1 instance)

**Warning:**
```
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump` instead.
```

**Affected Tests:**
- `test/backends/test_litellm_ollama.py::test_async_parallel_requests`

**Location:** `/litellm/litellm_core_utils/streaming_handler.py:1855`

**Issue:** This is in the LiteLLM dependency, not our code.

**Options:**
1. **Update LiteLLM dependency** - Check if newer version fixes this
2. **Report upstream** - File issue with LiteLLM project
3. **Suppress warning** - Temporary until LiteLLM fixes it

**Recommended Action:**
```bash
# Check current and latest LiteLLM version
uv pip list | grep litellm
# Update if newer version available
uv pip install --upgrade litellm
```

**Urgency:** Low - Upstream dependency issue

---

### 3. Watsonx Backend Deprecation (3 instances)

**Warning:**
```
DeprecationWarning: Watsonx Backend is deprecated, use 'LiteLLM' or 'OpenAI' Backends instead
```

**Affected Tests:**
- `test/backends/test_watsonx.py::test_client_cache`
- `test/stdlib/test_session.py::test_start_session_watsonx`

**Current Code:**
```python
@pytest.fixture(scope="function")
def session():
    return WatsonxAIBackend(  # ❌ Deprecated backend
        model_id="ibm/granite-3-3-8b-instruct",
        ...
    )
```

**Migration Path:**
```python
@pytest.fixture(scope="function")
def session():
    # Option 1: Use LiteLLM backend
    return LiteLLMBackend(
        model_id="watsonx/ibm/granite-4-h-small",
        ...
    )
    
    # Option 2: Use OpenAI-compatible backend
    return OpenAIBackend(
        model_id="ibm/granite-4-h-small",
        base_url="https://us-south.ml.cloud.ibm.com/ml/v1/...",
        ...
    )
```

**Action Items:**
- [ ] Migrate `test/backends/test_watsonx.py` to use LiteLLM backend
- [ ] Update `test/stdlib/test_session.py::test_start_session_watsonx`
- [ ] Consider renaming test file to `test_litellm_watsonx.py` (already exists!)
- [ ] Remove or archive old `test_watsonx.py` after migration
- [ ] Update documentation to remove Watsonx backend references

**Urgency:** Medium - Our own deprecation, should migrate soon

---

### 4. Docling Core Field Deprecation (4 instances)

**Warning:**
```
DeprecationWarning: Field `annotations` is deprecated; use `meta` instead.
```

**Affected Tests:**
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_basics`
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_markdown`
- `test/stdlib/components/docs/test_richdocument.py::test_richdocument_save`

**Location:** `/docling_core/transforms/serializer/markdown.py:490`

**Issue:** This is in the docling-core dependency.

**Options:**
1. **Update docling-core** - Check if newer version uses `meta`
2. **Wait for upstream fix** - May already be fixed in newer version
3. **Suppress warning** - If we can't control the dependency usage

**Recommended Action:**
```bash
# Check current version
uv pip list | grep docling-core
# Update to latest
uv pip install --upgrade docling-core
```

**Urgency:** Low - Upstream dependency issue

---

### 5. IBM Watsonx Model Lifecycle Warning (1 instance)

**Warning:**
```
LifecycleWarning: Model 'ibm/granite-3-3-8b-instruct' is in deprecated state from 2025-11-24 until 2026-02-22. 
IDs of alternative models: ibm/granite-4-h-small.
```

**Affected Tests:**
- `test/backends/test_watsonx.py::test_client_cache`

**Fix:**
```python
# Current
model_id="ibm/granite-3-3-8b-instruct"  # ❌ Deprecated model

# Should be
model_id="ibm/granite-4-h-small"  # ✅ Current model
```

**Action Items:**
- [ ] Update all references to `granite-3-3-8b-instruct`
- [ ] Search codebase for hardcoded model IDs
- [ ] Update documentation/examples

**Search Command:**
```bash
grep -r "granite-3-3-8b-instruct" . --exclude-dir=.venv
```

**Urgency:** High - Model deprecated until Feb 2026 (1 month)

---

### 6. aiohttp `enable_cleanup_closed` Deprecation (multiple instances)

**Warning:**
```
DeprecationWarning: enable_cleanup_closed ignored because https://github.com/python/cpython/pull/118960 
is fixed in Python version sys.version_info(major=3, minor=12, micro=8, releaselevel='final', serial=0)
```

**Affected Tests:**
- Multiple tests using LiteLLM with aiohttp

**Location:** `/aiohttp/connector.py:963`

**Issue:** aiohttp is passing a parameter that's no longer needed in Python 3.12.8+

**Options:**
1. **Update aiohttp** - Likely fixed in newer version
2. **Ignore** - This is informational, not breaking

**Recommended Action:**
```bash
uv pip install --upgrade aiohttp
```

**Urgency:** Low - Informational warning, not breaking

---

### 7. Pydantic Serialization Warnings (multiple instances)

**Warning:**
```
UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue(Expected 10 fields but got 5: Expected `Message` - serialized value may not be as expected)
```

**Affected Tests:**
- `test/backends/test_litellm_ollama.py` (multiple tests)
- `test/backends/test_tool_calls.py::test_tool_called`

**Issue:** LiteLLM's Pydantic models don't match the actual response structure from Ollama.

**Options:**
1. **Update LiteLLM** - May be fixed in newer version
2. **Report upstream** - If not fixed
3. **Suppress** - If it doesn't affect functionality

**Urgency:** Low - Warning only, doesn't break functionality

---

### 8. ABC Serializer Deprecation (1 instance)

**Warning:**
```
DeprecationWarning: Use BaseMetaSerializer() instead.
```

**Affected Tests:**
- `test/backends/test_tool_calls.py::test_tool_called_from_context_action`

**Location:** `<frozen abc>:106`

**Issue:** Unclear which library is causing this. Need to investigate.

**Action Items:**
- [ ] Add traceback to identify source: `pytest -W error::DeprecationWarning`
- [ ] Update the offending library
- [ ] Or update our code if we're using the deprecated API

**Urgency:** Low - Need more investigation

---

## Summary of Actions

### Immediate (Can fix now)
- [ ] Fix Pillow deprecation (2 files, trivial change)
- [ ] Update model ID from granite-3 to granite-4 (search and replace)

### Short-term (This sprint)
- [ ] Migrate Watsonx backend tests to LiteLLM
- [ ] Update dependencies: `uv pip install --upgrade litellm aiohttp docling-core`

### Medium-term (Next sprint)
- [ ] Investigate ABC serializer warning
- [ ] Monitor upstream fixes for Pydantic/LiteLLM issues

### Low Priority (Monitor)
- [ ] Pydantic serialization warnings (upstream)
- [ ] aiohttp cleanup warning (informational)

## Verification

After fixes:

```bash
# Run tests and check for deprecation warnings
uv run pytest test -v -W error::DeprecationWarning 2>&1 | grep -i "deprecation"

# Check specific categories
uv run pytest test/backends/test_vision_ollama.py -v -W error::DeprecationWarning
uv run pytest test/backends/test_watsonx.py -v -W error::DeprecationWarning
```

## Dependency Update Commands

```bash
# Check current versions
uv pip list | grep -E "(litellm|aiohttp|docling-core|pillow)"

# Update all at once
uv pip install --upgrade litellm aiohttp docling-core pillow

# Or update individually
uv pip install --upgrade litellm
uv pip install --upgrade aiohttp
uv pip install --upgrade docling-core
uv pip install --upgrade pillow
```

---

**Priority:** Medium  
**Impact:** Will cause test failures in future versions. Some have specific deadlines (Pillow in Oct 2026, Granite model in Feb 2026).