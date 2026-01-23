# Migration to Granite 4.0 Models 🚀

**Why this matters:**
The `granite-3.x` model family is approaching its End of Life (EOL). To ensure Mellea remains robust, performant, and secure, default configurations, examples, and tests must be migrated to the `granite-4.0` family. This is also a great opportunity to take advantage of the performance improvements in v4!

**What needs to be done:**
Identify all usages of Granite v3 (and earlier) and update them to their v4 equivalents.

**Observations:**
Preliminary research indicates a potential confusion in `mellea/backends/model_ids.py`. The constant `IBM_GRANITE_4_MICRO_3B` is mapped to `ibm/granite-4-h-small`. However, `ibm/granite-4-h-small` is a "Hybrid Small" model (larger and more capable than "Micro"). This naming mismatch should be corrected during the migration.
Additionally, explicit Granite 4 usages were found in:
- `test/stdlib/components/intrinsic/test_rag.py`: Uses `ibm-granite/granite-4.0-micro` directly.
- `test/conftest.py`: References `granite4:micro` in docstrings for Ollama checks.
These should be harmonized with the new default constants.

**Action Items:**
- [ ] **Model IDs**: Address the observation above. Create a new constant (e.g., `IBM_GRANITE_4_HYBRID_SMALL`) for `ibm/granite-4-h-small` and ensure `IBM_GRANITE_4_MICRO_3B` points to a true micro model (if available) or is deprecated/renamed.
- [ ] **Audit Usages**: Check all usages of `IBM_GRANITE_4_MICRO_3B` to determine if they intended to use the Micro model or the Hybrid Small model (since the constant currently points to Hybrid Small on Watsonx).
- [ ] **Backend Defaults**: Update `WatsonxAIBackend` default model to `ibm/granite-4-h-small` (using the new correct constant).
    - *Note*: The `WatsonxAIBackend` itself is deprecated in favor of `LiteLLM` (as noted in the codebase). However, the default should still be fixed while it remains in use.
- [ ] **Documentation**: Update `docs/tutorial.md` and other guides to reference Granite 4.
- [ ] **Examples**: Ensure all examples in `docs/examples/` run out-of-the-box with Granite 4.
- [ ] **Tests**: Verify `uv run pytest` passes with the new defaults.

**Affected Files (Preliminary Scan):**
References to "granite" were found in the following files. Please check these for v3 usages:

### Configuration & Core
- `pyproject.toml`
- `mellea/backends/model_ids.py`
- `mellea/backends/watsonx.py`
- `mellea/backends/ollama.py`
- `mellea/backends/huggingface.py`
- `mellea/backends/litellm.py`
- `mellea/backends/openai.py`

### Documentation & Examples
- `docs/tutorial.md`
- `docs/AGENTS_TEMPLATE.md`
- `docs/alora.md`
- `docs/dev/mellea_library.md`
- `docs/examples/aLora/101_example.py`
- `docs/examples/notebooks/model_options_example.ipynb`
- `docs/examples/notebooks/simple_email.ipynb`
- `docs/examples/instruct_validate_repair/101_email_with_validate.py` (and others in `docs/examples/`)
- `docs/kv_smash/hf_example.py`

### Tests
- `test/backends/test_watsonx.py`
- `test/backends/test_ollama.py`
- `test/backends/test_huggingface.py`
- `test/conftest.py`

