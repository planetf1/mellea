# Summary of Test Warnings & Grouped Issues

The following warnings were identified during the test run (`uv run pytest test -v`). They have been categorized into logical groups to be addressed via separate issues.

## 🔴 Group 1: Strategic & High Priority (Separate Issues)

### 1. Granite 4.0 Migration
*   **Warning**: `LifecycleWarning: Model 'ibm/granite-3-3-8b-instruct' is in deprecated state... alternative models: ibm/granite-4-h-small.`
*   **Impact**: Essential for long-term stability as v3 reaches EOL.
*   **Action**: Create/Update issue for migrating defaults, IDs, docs, and tests. (Drafted: `issue_granite_migration.md`)

### 2. Test Reliability & Correctness (Async/Resources/PEFT)
*   **Warning**: `RuntimeWarning: coroutine '...' was never awaited`, `RuntimeError: ... attached to a different loop`, `UserWarning: Already found a peft_config attribute`.
*   **Impact**: Major. Compromises test validity and stability.
*   **Action**: Consolidate into a major "Test Health" issue. (Drafted: `issue_test_async_fixes.md`)

## 🟡 Group 2: Modernization & Maintenance (Medium Priority)

### 3. Backend Transition: Watsonx to LiteLLM/OpenAI
*   **Warning**: `DeprecationWarning: Watsonx Backend is deprecated, use 'LiteLLM' or 'OpenAI' Backends instead`
*   **Impact**: Architectural alignment.
*   **Action**: Update examples and core defaults to prefer standard backends. Cross-reference with Granite migration.

### 4. Dependency Bumps (Pydantic/LiteLLM)
*   **Warning**: `UserWarning: Pydantic serializer warnings`
*   **Action**: Bump `litellm >= 1.81.1` in `pyproject.toml`.

## 🟢 Group 3: Minor Cleanup (Low Priority - Can be grouped)

### 5. Library API Updates
*   **Pillow**: `'mode' parameter is deprecated and will be removed in Pillow 13`.
*   **Docling**: `Field 'annotations' is deprecated; use 'meta' instead`.
*   **Aiohttp**: `enable_cleanup_closed ignored because [sys.version fix]`.
*   **Action**: Minor code updates to follow newer third-party APIs. Should be handled in a single "Maintenance & Cleanup" issue.
