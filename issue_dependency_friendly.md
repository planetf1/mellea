# Proposal: Improve Pip Friendliness with Descriptive Import Errors

Hi team! 👋

As a new user setting up Mellea, I noticed that the library can be a bit strict if you try to use a backend without installing its specific optional dependencies.

### The Problem
Mellea uses a lean core with optional "extras" (e.g., `mellea[hf]`, `mellea[watsonx]`). This is great for keeping install size down! However, if a user tries to use a backend they haven't installed, they get a raw, confusing traceback.

**Example:**
If I run `start_session(backend="hf")` without the `hf` extra:
```python
ModuleNotFoundError: No module named 'outlines'
```
This applies to the following backends, which all rely on optional extras:
*   `hf` or `huggingface` (requires `mellea[hf]`)
*   `watsonx` (requires `mellea[watsonx]`)
*   `litellm` (requires `mellea[litellm]`)

This is technically correct (the `hf` backend needs `outlines`), but it asks the user to debug internal dependencies rather than telling them what high-level action to take.

### Proposed Solution
We should wrap the backend imports in `session.py` (and potentially inside the backend modules themselves) with `try/except ImportError` blocks that raise a helpful `MelleaDependencyError`.

**Before:**
```python
elif name == "hf":
    from mellea.backends.huggingface import LocalHFBackend # Crashes here
```

**After:**
```python
elif name == "hf":
    try:
        from mellea.backends.huggingface import LocalHFBackend
    except ImportError as e:
        raise ImportError(
            "The 'hf' backend requires extra dependencies. "
            "Please install them with: pip install 'mellea[hf]'"
        ) from e
```

**2. Standardize**: We should also update `AGENTS.md` (and any future `CONTRIBUTING.md`) to explicitly document this pattern. This ensures that when contributors add new backends or optional integrations, they know to wrap imports in this standard way.

### Benefits
*   **Better Onboarding**: Users get a copy-pasteable fix immediately.
*   **Reduced Support Load**: Fewer issues filed asking "Why is outlines missing?".
*   **Polished Feel**: The library feels more robust and helpful.

I'd be happy to submit a PR for this! 🛠️
