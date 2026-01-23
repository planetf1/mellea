# Issue: Maintenance - Library API Updates & Dependency Maintenance 🧹

**Problem:**
Ongoing evolution of third-party libraries (Pillow, Docling, Pydantic/LiteLLM) has generated several deprecation warnings. While these do not currently break functionality, they should be addressed to avoid future regressions and follow best practices.

**Warning Groups:**
1.  **Pillow (Imaging)**: `'mode' parameter is deprecated and will be removed in Pillow 13`. Found in `test_vision_ollama.py` and `test_vision_openai.py`.
2.  **Docling (Data)**: `Field 'annotations' is deprecated; use 'meta' instead`.
3.  **Pydantic / LiteLLM**: Pydantic v2 serializer warnings triggered by LiteLLM usage.
4.  **Aiohttp**: `enable_cleanup_closed` warnings related to Python 3.12+ compatibility.

**Action Items:**
- [ ] **LiteLLM**: Bump `litellm` version to `>= 1.81.1` in `pyproject.toml` to resolve Pydantic compatibility warnings.
- [ ] **Pillow**: Identify and update `mode` parameter usage in image handling code to comply with Pillow 13 standards.
- [ ] **Docling**: Update `annotations` to `meta` in relevant transformation logic.
- [ ] **Aiohttp**: Review and remove/update legacy connector cleanup logic to align with Python 3.12+ expectations.

**Priority:** Low (Minor)
**Grouping Strategy**: These are minor maintenance items that can be bundled into a single "Clean-up" PR.
