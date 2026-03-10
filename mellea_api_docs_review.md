
# Mellea API Docs Improvement Plan — Technical Review

**Reviewer:** M365 Copilot  
**Date:** 2026-03-10 10:37:41Z  
**Scope:** Review of `DOCS_IMPROVEMENT_PLAN.md` with concrete fixes, patches, and CI hardening.

---

## Executive Summary

**What’s great**
- Clear phases with dependencies, decision gates, and rollbacks.
- CI alignment on `uv` and a unified `build.py` wrapper.
- Validation-first mindset (`validate.py`, unit/integration tests, CI summary).
- Coverage audit + docstring compliance + contributor ergonomics (snippets).

**What to tighten**
- A few correctness issues in regex/path handling (source links, x‑refs).
- CI workflow quoting/conditionals and required permissions.
- Anchor strategy: don’t couple to assumptions until you’ve *proven* Mintlify slug rules; keep probe dev-only.
- Deterministic builds with `uv` (lock enforcement) and extras availability.
- Cross-ref validator path resolution (currently resolves to a non-existent `api/api/...` path).

> If you implement the **Top 10** below, you’ll de‑risk most of the plan before Phase 4.

---

## Top 10 Concrete Changes

1. **Fix cross‑ref validator path resolution + fragments.**  
   Map links like `/api/mellea/x/y#anchor` → `docs/docs/api/mellea/x/y.mdx`; strip the `#fragment`, drop `/api/`, and add `.mdx`.

2. **Harden the “docs needed” PR check.**  
   Use a safe diff baseline for PRs and proper YAML `run: |` blocks. Avoid fragile grep pipelines; fail gracefully when there are no matches.

3. **Add required workflow permissions** for `create-pull-request@v6` and artifacts:
   ```yaml
   permissions:
     contents: write
     pull-requests: write
     actions: read
   ```

4. **Enforce lock determinism with `uv`.**  
   Add a guard that runs `uv lock` then `git diff --exit-code uv.lock` to detect drift.

5. **Make `make docs` work without prior sync.**  
   Either instruct contributors to run `uv sync --all-extras`, or have `make docs` run with `--with mdxify --with griffe` so it just works.

6. **Include probe deps in `docs-autogen` extras** (`beautifulsoup4`, `requests`) and keep the probe script **dev-only**.

7. **Generalize source-link rewriting.**  
   Don’t assume `.venv-docs-autogen` or `main`. Handle commit SHAs and any venv/site-packages subpath. Add tests for both `mellea/` and `cli/`, and for pre‑rewritten URLs (should remain intact).

8. **Make the linkifier code‑block aware.**  
   Avoid rewriting inside fenced code blocks; pre-split or walk a Markdown AST.

9. **Tighten Typer CLI fallbacks.**  
   Support `@app.command(name="…")` and nested groups; add tests.

10. **Add a concurrency group** to auto‑cancel stale runs on PR updates:
    ```yaml
    concurrency:
      group: docs-autogen-${{ github.ref }}
      cancel-in-progress: true
    ```

---

## Phase-by-Phase Feedback

### Phase 0 — `uv` migration & unified build
- **Build determinism:** enforce lock checks (see Top #4).
- **Artifacts:** keep the wheel artifact and also upload `.validation-report.json` for forensics.
- **Makefile messaging vs behavior:** align the comment with actual `uv` usage or make `docs` depend on `uv sync --all-extras`.
- **Wheel selection:** if multiple wheels exist, filter or fail fast with a clear error.
- **Cache keys:** current key is fine; consider hashing `tooling/docs-autogen/**` if those scripts influence deps.

### Phase 1 — Source links
- **Regex robustness:** convert any venv/site‑packages path into a canonical repo URL using the passed tag/branch; don’t depend on the source link’s original branch.
- **Validation:** count total “View Source” links and include a ratio in CI summary.

### Phase 2 — API coverage
- **`__all__` parsing:** support lists, tuples, and `__all__ += [...]` patterns; add tests.
- **CLI coverage:** if mdxify lacks Typer support, store extracted commands in a machine‑readable file and include in the validation report.

### Phase 3 — Docstrings
- **Ruff rules:** great. To avoid regressions, compare the new `D` count to a recorded baseline and fail on increases.
- **Dropped sections:** define detection explicitly (e.g., look for `Args:`, `Returns:`, `Raises:` in source vs rendered MDX).

### Phase 4 — Cross‑references
- **BLOCKER:** keep `probe_mintlify_anchors.py` dev-only and record empirical rules (dots, underscores, generics, unicode, dunders).
- **Indexing:** consider deriving the symbol→page map from **generated MDX** (frontmatter + headings) and fall back to Griffe to avoid layout drift.

### Phase 5 — Structure
- **Preambles:** verify all `sections[].modules[]` exist; warn on orphans.
- **Orphans:** ignore `__main__.py`, migration stubs, platform-specific modules.

### Phase 6 — Validation & Monitoring
- **Must‑pass checks:** treat as required: zero venv links, zero broken cross‑refs, docstring compliance.
- **PR comment:** include version and all summary metrics; attach report artifact.

---

## Targeted Patches

### 1) Cross‑ref validator (fix path mapping & fragments)
```python
# tooling/docs-autogen/validate.py (snippet)
from urllib.parse import urlparse

def _mdx_path_for_api_url(api_dir: Path, url: str) -> Path:
    """
    Map a site URL like /api/mellea/stdlib/session#classname
    to a filesystem path like <api_dir>/mellea/stdlib/session.mdx
    """
    parsed = urlparse(url)
    # Skip absolute external URLs
    if parsed.scheme or parsed.netloc:
        return Path("/__external__")
    path = parsed.path  # e.g., "/api/mellea/stdlib/session"
    if not path.startswith("/api/"):
        return Path("/__non_api__")
    rel = path[len("/api/"):]  # "mellea/stdlib/session"
    return (api_dir / rel).with_suffix(".mdx")


def validate_cross_references(api_dir: Path) -> dict:
    broken_links, total_links = [], 0
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text(encoding="utf-8")
        for symbol, url in re.findall(r'\[\`([^\`]+)\`\]\(([^)]+)\)', content):
            total_links += 1
            target = _mdx_path_for_api_url(api_dir, url)
            if str(target).startswith("/__"):  # external or non-api -> skip
                continue
            if not target.exists():
                broken_links.append({'file': str(mdx_file), 'symbol': symbol, 'url': url})
    return {
        'passed': len(broken_links) == 0,
        'total_links': total_links,
        'broken_links': broken_links,
        'success_rate': 1 - (len(broken_links) / total_links) if total_links > 0 else 1,
    }
```

### 2) Source‑link rewriting (generalize & avoid false matches)
```python
# tooling/docs-autogen/decorate_api_mdx.py (snippet)
import re

_VENV_PATH = re.compile(
    r'https://github\.com/[^/]+/[^/]+/blob/[^/]+'
    r'/(?:\.venv[^/]+/)?'                       # any venv folder, optional
    r'(?:lib/python\d+\.\d+/site-packages/)?'  # site-packages, optional
    r'((?:mellea|cli)/[^)#"]+?\.py)(#L\d+)?'   # capture file + optional line
)

def fix_source_links(mdx_text: str, repo_base: str, version: str | None = None) -> str:
    """
    Re-point any venv-based source links to the repository.
    repo_base: e.g., "https://github.com/generative-computing/mellea"
    version:   e.g., "0.3.0" -> link to tag "v0.3.0", else "main"
    """
    branch = f"v{version}" if version else "main"

    def _replace(m: re.Match) -> str:
        file_path, line = m.group(1), m.group(2) or ""
        return f"{repo_base}/blob/{branch}/{file_path}{line}"

    return _VENV_PATH.sub(_replace, mdx_text)
```

### 3) Linkifier: avoid fenced code blocks
```python
# tooling/docs-autogen/decorate_api_mdx.py (snippet)
_FENCED_BLOCK = re.compile(r'```.*?```', re.DOTALL)
_BACKTICK_SYMBOL = re.compile(r'(?<!`)`([A-Za-z_][A-Za-z0-9_.]*)`(?!`)')

def linkify_backticks(md_text: str, symbol_index: dict) -> tuple[str, list[str]]:
    """
    Transform `symbol` to /api/...#anchor outside fenced code blocks.
    """
    warnings = []
    segments, last = [], 0
    for m in _FENCED_BLOCK.finditer(md_text):
        pre = md_text[last:m.start()]
        pre = _BACKTICK_SYMBOL.sub(lambda mm: _link_or_warn(mm, symbol_index, warnings), pre)
        segments.append(pre)
        segments.append(md_text[m.start():m.end()])  # keep fenced block untouched
        last = m.end()
    tail = md_text[last:]
    tail = _BACKTICK_SYMBOL.sub(lambda mm: _link_or_warn(mm, symbol_index, warnings), tail)
    segments.append(tail)
    return "".join(segments), warnings


def _link_or_warn(mm, symbol_index, warnings):
    symbol = mm.group(1)
    base = symbol_index.get(symbol)
    if not base:
        warnings.append(f"Unknown symbol: {symbol}")
        return mm.group(0)
    anchor = generate_mintlify_anchor(symbol)
    return f"[`{symbol}`]({base}#{anchor})"
```

### 4) Safer “docs-needed” gate + YAML quoting
```yaml
# .github/workflows/docs-autogen-pr.yml (snippet)
jobs:
  check_docs_needed:
    runs-on: ubuntu-latest
    outputs:
      should_run: ${{ steps.check.outputs.run }}
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - id: check
        name: Check if docs generation needed
        shell: bash
        run: |
          set -euo pipefail
          if [[ "${{ github.event_name }}" == "push" && "${{ github.ref }}" =~ ^refs/tags/v ]]; then
            echo "run=true" >> "$GITHUB_OUTPUT"; exit 0
          fi
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "run=true" >> "$GITHUB_OUTPUT"; exit 0
          fi
          BASE_SHA="${{ github.event.pull_request.base.sha }}"
          HEAD_SHA="${{ github.sha }}"
          changed_py=$(git diff --name-only "${BASE_SHA}" "${HEAD_SHA}" --             'mellea/**/*.py' 'cli/**/*.py' || true)
          if [[ -z "${changed_py}" ]]; then
            echo "run=false" >> "$GITHUB_OUTPUT"; exit 0
          fi
          # Only run if a changed file actually contains a docstring (heuristic)
          mapfile -t files < <(printf '%s
' ${changed_py})
          for f in "${files[@]}"; do
            if grep -qE '^\s*"""' "$f"; then
              echo "run=true" >> "$GITHUB_OUTPUT"; exit 0
            fi
          done
          echo "run=false" >> "$GITHUB_OUTPUT"
```

### 5) Lock determinism guard (portable)
```yaml
# in docs_autogen job steps
- name: Verify lock determinism
  shell: bash
  run: |
    set -euo pipefail
    uv lock
    git diff --exit-code uv.lock
```

### 6) Extras: include probe deps
```toml
[project.optional-dependencies]
docs-autogen = [
  "mdxify>=0.2.0",
  "griffe>=1.0.0",
  "beautifulsoup4>=4.12",
  "requests>=2.32",
]
```

---

## Smaller Nits & Polish
- **Pre-release tags:** `build.py` normalizes `v0.3.0-rc1` → `0.3.0` (good for PyPI), but GitHub links should use the *exact* tag (e.g., `v0.3.0-rc1`). Consider passing both `--pkg-version` and `--tag` (raw), or derive the tag from `GITHUB_REF_NAME` in CI.
- **Unit tests:** add Windows-path tests; `__all__` as tuple and with `+=`; property tests for the anchor generator with headings like ``Type[T]`` and dunders.
- **Metrics:** capture docs generation timings and CI duration; plot regressions.
- **Makefile:** add `make docs-ci` to mirror CI invocation for easier local debugging.

---

## Open Questions
1. **Pre-release docs:** Should source links point to the pre-release tag (`vX.Y.Z-rcN`) or a stable tag later? Recommendation: use the exact tag used to build the docs.
2. **CI strictness for Phase 4:** Do you want to fail on *any* broken cross-ref from day one, or warn until Phase 4 completes?
3. **Index source of truth:** Prefer MDX-derived symbol routing (matches actual output) with Griffe as a fallback—want me to sketch that hybrid?

---

## Next Steps
- Apply the Top 10 changes.
- Decide on must-pass checks and pre-release link policy.
- I can turn these patches into a PR (one commit per patch) or a single squashed change—your call.
