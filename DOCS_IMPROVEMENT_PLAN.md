# API Documentation Improvement Plan (Timescale A)

Retain current `mdxify` CI tooling. Iteratively improve output quality, DX, and completeness.

> [!NOTE]
> Self-contained plan. All code, YAML, and schemas inline. Incorporates all feedback from Gemini, Copilot, Bob (three passes), and Claude (synthesis pass — architectural fixes, Griffe migration, PR 601 compatibility).

## Current State

- **Scripts:** `generate-ast.py` creates isolated venv, installs **PyPI** `mellea` + `mdxify`, runs `mdxify`, post-processes to `docs/docs/api/`. `decorate_api_mdx.py` adds sidebar fixes, CLASS/FUNC pills, dividers.
- **CI:** `docs-autogen-pr.yml` triggers on `v*` tags or manual dispatch. Opens a PR.
- **Pain points:** Uses `pip`/`venv` (rest of repo uses `uv`). No single build command. Source links point into `.venv-docs-autogen/`. Flat backticks (no hyperlinks). Dropped docstring sections.

## Resolved: Missing Modules (Issue #532)

`mellea/eval/`, `mellea/archetypes/`, `mellea/stdlib/requirements/catalog/` **do not exist** (all branches + full git history). Create `tooling/docs-autogen/audit_missing_modules.py` to document this as a traceable JSON artifact.

---

## How the Documentation Pipeline Works

This section describes the intended end-to-end pipeline — both as it exists today and as it will work after all phases are complete.

### What lives in this repository (tooling branch)

All scripts, CI definitions, configuration, and tests. **The generated `.mdx` files in `docs/docs/api/` are never committed here** — they are always the output of running the pipeline.

```
tooling/docs-autogen/
  generate-ast.py      # Installs mellea from PyPI (or wheel), runs mdxify, post-processes
  decorate_api_mdx.py  # Adds SidebarFix, CLASS/FUNC pills, dividers
  build.py             # NEW (Phase 0): unified wrapper that calls both scripts above
  validate.py          # NEW: built incrementally phases 1/2/4, assembled Phase 6
  requirements.txt     # mdxify==x.y.z, griffe==x.y.z

.github/workflows/
  docs-autogen-pr.yml  # CI: tag push → generate docs → open PR
```

### Local development workflow

```bash
# Standard test — runs generate-ast.py's own venv (pip, self-contained):
make docs

# Iterating on source changes — runs generate-ast.py directly with PYTHONPATH=. (no install):
make docs-dev

# Fast test with exact wheel (mirrors CI, requires uv build first):
uv build
WHEEL=$(ls dist/*.whl | head -1)
uv run --isolated --with "${WHEEL}" --with "mdxify==0.2.35" \
  python tooling/docs-autogen/build.py --no-venv

# Validate output:
make docs-validate
```

Output lands in `docs/docs/api/`. Inspect it, iterate, discard — never commit it from this branch.

### CI workflow (tag push)

```
git tag v0.4.0 → push tag
  → docs-autogen-pr.yml triggers
  → uv build (local wheel)
  → generate-ast.py --no-venv skips pip install; uses uv-managed env (wheel pre-installed)
  → decorate_api_mdx.py decorates output
  → validate.py checks quality thresholds
  → peter-evans/create-pull-request opens a PR: "docs: auto-generate (v0.4.0)"
```

The docs PR contains only generated `.mdx` files and an updated `docs.json`. It is reviewed and merged separately. It is never the same branch as this tooling branch.

### Relationship to PR 601

PR 601 (`update-docs`) restructures the narrative "Docs" tab. It does not touch `docs/docs/api/`. After PR 601 merges, run `make docs` once locally to confirm the merged `docs.json` round-trips correctly, then this pipeline continues unchanged.

---

## PR 601 Website Compatibility

PR 601 (branch: `update-docs`) is a complete rewrite of the Mintlify developer docs at `docs.mellea.ai`. The autogen pipeline must co-exist with it.

**What PR 601 changes:**

- Restructures the "Docs" tab with a Diataxis layout (Getting Started, Tutorials, Concepts, How-To, Integrations, Advanced, Examples, Evaluation & Observability, Reference, Community, Troubleshooting)
- Does **not** change the "API Reference" tab — autogen continues to own it
- Adds `markdownlint` CI check on `docs/docs/**/*.md` files only; API `.mdx` files are excluded
- Modifies `docs/docs/docs.json` significantly

**Merge impact:**
`generate-ast.py` replaces **only** the `"tab": "API Reference"` entry in `docs.json` by matching `NAV_TAB = "API Reference"`. This is safe — it will not conflict with PR 601's "Docs" tab structure. After PR 601 merges, run `make docs` once to verify the merged `docs.json` round-trips correctly.

**URL stability requirement:**
PR 601 narrative docs may link directly to API reference pages (e.g. `api/mellea/stdlib/session`). The autogen pipeline must never change the `api/<pkg>/...` URL convention across regenerations. Do not rename packages or restructure the output directory hierarchy.

**Style alignment:**
Phase 5 preambles and any injected prose must follow PR 601's style: US English, active voice, present tense, 80-char prose wrap.

---

## Phase Dependencies & Effort

```
Phase 0 (uv, 2-3d) ──┬──> Phase 1 (links, 1d)    ──┐
                      ├──> Phase 2 (coverage, 2-3d) ─┤
                      └──> Phase 3 (docstrings, 3-5d)─┤
                                                       └──> Phase 4 (cross-refs, 5-7d) ──> Phase 5 (structure, 1-2d) ──> Phase 6 (validation, 2d)
```

**Total: ~3-4 weeks.**

---

## Parallel Execution Map (for agent teams)

Agents should work in execution waves. Within each wave, all items are independent and can be assigned to separate agents simultaneously.

**Skill codes used below:**

| Code | Skill |
| --- | --- |
| `bash` | Shell scripting, CLI tools, running commands |
| `python` | Python scripting, editing existing `.py` files |
| `yaml` | GitHub Actions / CI YAML authoring |
| `regex` | Regular expression writing and testing |
| `toml` | `pyproject.toml` / config file editing |
| `griffe` | Griffe API, static Python analysis |
| `mintlify` | Mintlify MDX format, docs platform |
| `read-only` | Code reading, version checking, measurement only |

---

### Wave 0 — Immediately (no dependencies)

| Task | Skills | Blocks |
| --- | --- | --- |
| Pre-Work: measure CI baseline timing (5 CI runs) | `bash`, `read-only` | Pre-Work section filled in |
| Phase 0 Step 5: check latest `mdxify`/`griffe` versions, smoke-test, update pins | `bash`, `python`, `read-only` | CI `--with` pin in Wave 3 |

### Wave 1 — After Wave 0

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 0 Step 1: add `--no-venv` flag to `generate-ast.py` | `python` | Wave 2 (all wheel-based tasks) |
| Phase 3 Step 1: verify/add ruff `D` config in `pyproject.toml` | `toml` | Phase 3 Step 2 |
| Phase 3 Step 3: add pre-commit hook | `yaml` | — |
| Phase 3 Step 4: add VS Code snippets | `read-only` | — |

### Wave 2 — After Wave 1 (Phase 0 Step 1 complete)

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 0 Step 3a: create `build.py` wrapper | `python`, `bash` | Wave 3 CI rewrite |
| Phase 0 Step 3b: create `Makefile` | `bash` | Wave 3 CI rewrite |
| Phase 1: implement `fix_source_links()` + `--version` flag + unit tests | `python`, `regex` | Phase 4 (correct links required) |
| Phase 2 Step 1: Griffe-based symbol discovery (`get_public_symbols_for_package`) | `python`, `griffe` | Phase 2 Step 3 |
| Phase 2 Step 2: CLI Typer extraction (`extract_typer_commands`, filter) | `python` | Phase 2 Step 3 |
| Phase 3 Step 2: run ruff `--select D --fix` on `mellea/` and `cli/` | `bash`, `python` | Phase 4 acceptance |

### Wave 3 — After Wave 2 (`build.py` + `Makefile` done)

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 0 Step 4: rewrite `docs-autogen-pr.yml` (uv, wheel, lock check) | `yaml`, `bash` | — |
| Phase 2 Step 3: write `audit_coverage.py`, run, record baseline | `python`, `griffe`, `bash` | Phase 2 Step 4 |
| Phase 2 Step 4: set coverage target, write exclusions JSON | `read-only` | Phase 4 acceptance |

### Wave 4 — After Phases 1, 2, 3 all complete

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 4A: run anchor probe against Mintlify preview, confirm/update `generate_mintlify_anchor()` | `python`, `mintlify`, `bash` | Phase 4B |

### Wave 5 — After Phase 4A

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 4B: implement `linkify_backticks()`, `build_symbol_index()`, `validate_cross_references()` | `python`, `regex`, `griffe` | Phase 4C |

### Wave 6 — After Phase 4B

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 4C: add `check_anchor_collisions()`, run full validation, fix broken links | `python`, `mintlify` | Phase 5 |

### Wave 7 — After Phase 4C

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 5: write `preambles.json`, implement `inject_preamble()`, run orphaned module discovery | `python`, `mintlify` | Phase 6 |

### Wave 8 — After Phase 5

| Task | Skills | Blocks |
| --- | --- | --- |
| Phase 6: assemble final `validate.py`, update CONTRIBUTING/AGENTS.md, set up metrics CSV | `python`, `bash` | — |

---

**Intra-phase parallelism notes:**

- **Phase 0**: Steps 1 and 5 (requirements.txt) are independent — assign to different agents. Steps 2 (wheel build docs), 3a (build.py), and 3b (Makefile) can all run after Step 1 completes, in parallel with each other. Step 4 (CI workflow) requires build.py + Makefile first.
- **Phase 1**: Steps 1–3 are sequential (implement → integrate → add CLI flag). Step 4 (validate.py function) and Step 5 (unit tests) can be written in parallel with each other once the implementation is done.
- **Phase 2**: Steps 1 (Griffe discovery) and 2 (Typer extraction) are independent. Step 3 (coverage audit) requires Step 1. Step 4 (targets/exclusions) requires Step 3.
- **Phase 3**: Steps 1 (ruff config), 3 (pre-commit), and 4 (VS Code snippets) are fully independent. Step 2 (fix violations) requires Step 1.
- **Phase 4**: Strictly sequential within the phase (4A → 4B → 4C).

---

**User-value order** (independent of technical dependencies, highest first):

| Phase | Direct user impact |
|---|---|
| 3 — Docstrings | Every symbol description users read |
| 2 — Coverage | Missing APIs = docs users can't trust |
| 1 — Source links | Broken "View Source" links frustrate immediately |
| 4 — Cross-refs | Navigation between related types |
| 5 — Structure | Preambles and overview pages |
| 0, 6 | Internal CI/validation — invisible to users |

**Agent execution notes:**
Each phase is self-contained with runnable code, exact file paths, acceptance criteria, and a verification command. All code blocks are complete and copy-paste-ready — no pseudocode. Follow the wave map above for maximum parallelism; do not start a wave until all blocking tasks in the previous wave are complete and their acceptance criteria pass.

For multi-agent orchestration, track wave completion with a lightweight state file (e.g., `tooling/docs-autogen/.wave-state.json`) that each agent updates when its task's acceptance criteria pass. This prevents race conditions where a later-wave agent starts before an earlier-wave task has truly finished.

---

## Getting Started (Bootstrap)

```bash
# 1. Check out this branch and install dev dependencies
git checkout <this-tooling-branch>
uv sync

# 2. Generate docs with current (unmodified) pipeline to establish baseline
make docs                        # or: python tooling/docs-autogen/generate-ast.py ...
ls docs/docs/api/                # inspect output

# 3. Run existing tests (if any)
make docs-test

# 4. Begin Phase 0. Work through phases in dependency order:
#    Phase 0 → Phase 1 / Phase 2 / Phase 3 (1, 2, 3 all parallel) → Phase 4 → Phase 5 → Phase 6
```

All work is committed to this tooling branch. When a phase is complete, verify its acceptance criteria, commit the script/config changes, and move to the next phase.

---

## Pre-Work: Establish Baseline

Before starting Phase 0:

1. **Measure current CI timing** (avg of 5 runs):
   - Total CI job time: ___ min
   - Venv creation: ___ sec
   - pip install: ___ sec
   - mdxify execution: ___ sec
   - Post-processing: ___ sec

2. **Set up test infrastructure:**
   ```bash
   mkdir -p test/tooling/docs-autogen
   ```

3. **Mintlify anchor algorithm** — a provisional `generate_mintlify_anchor()` is ready (see Phase 4A). Run the probe script once against the live preview to confirm before Phase 4B; if no preview is available, proceed with the provisional implementation — Phase 4C validation will catch mismatches.

---

## Phase 0: `uv` Migration & Unified Build Command

**Risk:** ⚠️ HIGH — PyPI availability, cache strategy

### Actions

#### 1. Add `--no-venv` flag to `generate-ast.py` (required for wheel approach)

**This is a prerequisite for the wheel-based build.** `generate-ast.py` always creates its own `.venv-docs-autogen` and runs `pip install` internally. When called by `build.py` under `uv run --isolated --with wheel`, the uv environment is invisible to it — it still installs from PyPI, defeating the chicken-egg fix entirely.

Add a `--no-venv` flag to `generate-ast.py` (`tooling/docs-autogen/generate-ast.py`):

```python
# In main(), add to argument parser:
parser.add_argument(
    "--no-venv",
    action="store_true",
    help="Skip venv creation and pip install; use sys.executable directly. "
         "Use when the caller (uv run --with wheel) has already set up the environment.",
)

# Replace the venv/install section in main():
if args.no_venv:
    venv_python = Path(sys.executable)
    print(f"⚡ --no-venv: using {venv_python} directly", flush=True)
else:
    venv_python = ensure_venv()
    pip_install(venv_python, args.pypi_name, args.pypi_version)
```

**Verification:** Run `uv run --isolated --with mdxify python tooling/docs-autogen/generate-ast.py --no-venv --help` and confirm it exits cleanly without creating `.venv-docs-autogen/`.

#### 2. Build from local wheel (solves chicken-egg problem)

PyPI publish happens *after* tagging, so `--with mellea==${VERSION}` would fail. The `--no-venv` flag (added above) ensures `generate-ast.py` uses the uv-managed environment that already has the wheel installed.

```bash
uv build
WHEEL=$(ls dist/*.whl | head -1)
uv run --isolated --with "${WHEEL}" --with "mdxify==0.2.35" \
  python tooling/docs-autogen/build.py --no-venv
```

#### 3. `build.py` wrapper specification
```python
#!/usr/bin/env python3
"""Unified docs build wrapper.

Usage:
    python tooling/docs-autogen/build.py [options]

Options:
    --pkg-version VERSION    Package version (e.g., 0.3.0)
    --link-base URL         Base URL for source links
    --docs-json PATH        Path to docs.json (default: auto-detect)
    --docs-root PATH        Mintlify docs root (default: parent of docs.json)
    --skip-generation       Only run decoration (for testing)
    --skip-decoration       Only run generation (for testing)
"""
import argparse, subprocess, sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Build API documentation")
    parser.add_argument("--pkg-version", help="Package version (e.g., 0.3.0 or 0.3.0-rc1)")
    parser.add_argument("--link-base", help="Base URL for source links")
    parser.add_argument("--docs-json", help="Path to docs.json")
    parser.add_argument("--docs-root", help="Mintlify docs root")
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--skip-decoration", action="store_true")
    parser.add_argument("--no-venv", action="store_true",
                        help="Pass --no-venv to generate-ast.py (use when running under uv --with wheel)")
    args = parser.parse_args()

    # Handle pre-release versions: v0.3.0-rc1 → 0.3.0
    # Note: pkg_version is used for PyPI pin only. For source link tags, pass --link-base with the full tag.
    if args.pkg_version:
        args.pkg_version = args.pkg_version.lstrip('v').split('-')[0]

    repo_root = Path(__file__).resolve().parents[2]

    # Step 1: Generation
    if not args.skip_generation:
        print("=" * 60, "\nSTEP 1: Generating API documentation\n", "=" * 60)
        gen_cmd = [sys.executable, str(repo_root / "tooling/docs-autogen/generate-ast.py")]
        if args.docs_json: gen_cmd.extend(["--docs-json", args.docs_json])
        if args.docs_root: gen_cmd.extend(["--docs-root", args.docs_root])
        if args.pkg_version: gen_cmd.extend(["--pypi-version", args.pkg_version])
        if args.no_venv: gen_cmd.append("--no-venv")
        result = subprocess.run(gen_cmd, check=False)
        if result.returncode != 0:
            print("❌ Generation failed", file=sys.stderr)
            return result.returncode

    # Step 2: Decoration
    if not args.skip_decoration:
        print("\n" + "=" * 60, "\nSTEP 2: Decorating MDX files\n", "=" * 60)
        dec_cmd = [sys.executable, str(repo_root / "tooling/docs-autogen/decorate_api_mdx.py")]
        if args.docs_root: dec_cmd.extend(["--docs-root", args.docs_root])
        if args.pkg_version: dec_cmd.extend(["--version", args.pkg_version])
        result = subprocess.run(dec_cmd, check=False)
        if result.returncode != 0:
            print("❌ Decoration failed", file=sys.stderr)
            return result.returncode

    print("\n" + "=" * 60, "\n✅ Documentation build complete\n", "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

#### 3. Makefile
```makefile
.PHONY: docs docs-clean docs-validate docs-test docs-dev help

help:
	@echo "Documentation targets:"
	@echo "  make docs          - Generate API documentation"
	@echo "  make docs-clean    - Clean generated documentation"
	@echo "  make docs-validate - Validate generated documentation"
	@echo "  make docs-test     - Run documentation tests"
	@echo "  make docs-dev      - Generate from local source (no wheel)"

docs:
	@echo "Generating API documentation (local)..."
	@echo "Note: For CI, build wheel first (see CI workflow). Locally, this uses generate-ast.py's own venv."
	uv run python tooling/docs-autogen/build.py \
		--docs-json docs/docs/docs.json --docs-root docs/docs

docs-clean:
	rm -rf .venv-docs-autogen .mdxify-run-cwd docs/api docs/docs/api
	@echo "✅ Clean complete"

docs-validate: docs
	uv run python tooling/docs-autogen/validate.py \
		--api-dir docs/docs/api --output docs/docs/api/.validation-report.json

docs-test:
	uv run pytest test/tooling/docs-autogen/ -v

docs-dev:
	PYTHONPATH=. uv run python tooling/docs-autogen/generate-ast.py \
		--docs-json docs/docs/docs.json --docs-root docs/docs --pypi-name mellea --no-venv
	uv run python tooling/docs-autogen/decorate_api_mdx.py --docs-root docs/docs
```

#### 4. CI workflow

```yaml
# NOTE: permissions and concurrency are already present in the current
# docs-autogen-pr.yml. Verify they read exactly as shown below; add
# `actions: read` if missing.
permissions:
  contents: write
  pull-requests: write
  actions: read          # required for cache metadata reads

concurrency:
  group: docs-autogen-${{ github.ref }}
  cancel-in-progress: true

on:
  push:
    tags: ["v*"]
  pull_request:
    paths:
      - 'mellea/**/*.py'
      - 'cli/**/*.py'
      - 'tooling/docs-autogen/**'
  workflow_dispatch: {}

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
          # Use exact SHAs — avoids fragile origin/<base_ref> resolution on shallow clones
          BASE_SHA="${{ github.event.pull_request.base.sha }}"
          HEAD_SHA="${{ github.sha }}"
          changed_py=$(git diff --name-only "${BASE_SHA}" "${HEAD_SHA}" -- \
            'mellea/**/*.py' 'cli/**/*.py' || true)
          if [[ -z "${changed_py}" ]]; then
            echo "run=false" >> "$GITHUB_OUTPUT"; exit 0
          fi
          mapfile -t files < <(printf '%s\n' ${changed_py})
          for f in "${files[@]}"; do
            if grep -qE '^\s*"""' "$f" 2>/dev/null; then
              echo "run=true" >> "$GITHUB_OUTPUT"; exit 0
            fi
          done
          echo "run=false" >> "$GITHUB_OUTPUT"

  docs_autogen:
    needs: check_docs_needed
    if: needs.check_docs_needed.outputs.should_run == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      # Native uv caching — replaces the manual actions/cache@v4 block.
      # Gemini: setup-uv has built-in cache support; no separate cache step needed.
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
          cache-dependency-glob: "pyproject.toml"

      - name: Verify lock determinism
        shell: bash
        run: |
          set -euo pipefail
          uv lock
          git diff --exit-code uv.lock

      - run: echo "PKG_VERSION=${GITHUB_REF_NAME#v}" >> $GITHUB_ENV

      - name: Build wheel
        run: uv build

      - uses: actions/upload-artifact@v4
        with:
          name: mellea-wheel-${{ env.PKG_VERSION }}
          path: dist/*.whl
          retention-days: 7

      - name: Generate docs from wheel
        run: |
          # head -1 guards against multiple wheels in dist/ (e.g. sdist + wheel)
          WHEEL=$(ls dist/*.whl | head -1)
          uv run --isolated --with "${WHEEL}" --with "mdxify==0.2.35" \
            python tooling/docs-autogen/build.py \
            --no-venv \
            --pkg-version "${PKG_VERSION}" \
            --link-base "https://github.com/generative-computing/mellea/blob/v${PKG_VERSION}"

      - name: Validate generated docs
        run: |
          uv run python tooling/docs-autogen/validate.py \
            --api-dir docs/docs/api \
            --output docs/docs/api/.validation-report.json

      - name: Check validation passed
        run: |
          PASSED=$(jq -r '.summary.passed' docs/docs/api/.validation-report.json)
          if [ "${PASSED}" != "true" ]; then
            jq '.warnings' docs/docs/api/.validation-report.json
            exit 1
          fi

      - uses: actions/upload-artifact@v4
        with:
          name: validation-report-${{ env.PKG_VERSION }}
          path: docs/docs/api/.validation-report.json
          retention-days: 30

      - name: Job summary
        run: |
          echo "## 📊 Docs Generation Summary" >> $GITHUB_STEP_SUMMARY
          echo "- Version: ${{ env.PKG_VERSION }}" >> $GITHUB_STEP_SUMMARY
          if [ -f docs/docs/api/.validation-report.json ]; then
            echo "- Validation: $(jq -r '.summary.passed' docs/docs/api/.validation-report.json)" >> $GITHUB_STEP_SUMMARY
            echo "- Coverage (mellea): $(jq -r '.checks.api_coverage.mellea.coverage // "N/A"' docs/docs/api/.validation-report.json)" >> $GITHUB_STEP_SUMMARY
            echo "- Source links broken: $(jq -r '.checks.source_links.venv_links | length' docs/docs/api/.validation-report.json)" >> $GITHUB_STEP_SUMMARY
          fi

      - uses: peter-evans/create-pull-request@v6
        if: github.ref_type == 'tag'
        with:
          branch: "docs/autogen/v${{ env.PKG_VERSION }}"
          title: "Docs: API autogen for v${{ env.PKG_VERSION }}"
```

#### 5. Update `tooling/docs-autogen/requirements.txt` with latest compatible pins

**Before implementing Phase 0, check for newer versions of both dependencies** and pin to the latest that produces correct output:

```bash
# Check latest available versions
uv pip index versions mdxify
uv pip index versions griffe

# Test with latest mdxify: generate docs and diff against current output
uv run --isolated --with "mdxify==<latest>" python tooling/docs-autogen/generate-ast.py ...
diff -r docs/docs/api/ /tmp/mdxify-test-output/
```

Update `requirements.txt` to the verified latest versions (current pins as of plan authorship — likely outdated by the time this is implemented):

```text
mdxify==0.2.35   # update to latest that passes smoke test
griffe==0.49.0   # update to latest compatible with mdxify
```

The `--with "mdxify==<version>"` pin in `docs-autogen-pr.yml` and the `requirements.txt` pin **must always match**. When upgrading either dependency, update both in the same commit and run `make docs` to confirm output is acceptable. Record the rationale if pinning to a non-latest version (e.g. breaking change in newer release).

### Rollback
Keep `generate-ast.py` pip path working for 1 release cycle:
```yaml
- name: Generate docs (uv)
  id: uv_gen
  continue-on-error: true
  run: uv run python tooling/docs-autogen/build.py
- name: Generate docs (pip fallback)
  if: steps.uv_gen.outcome == 'failure'
  run: python tooling/docs-autogen/generate-ast.py
```

### Acceptance Criteria
- `make docs` works locally with no prior setup besides `uv`
- CI uses `--frozen`, fails on lock mismatches
- CI runtime ≤70% of baseline; cache hit rate ≥80%

---

## Phase 1: Fix GitHub Source Links

**Risk:** ✅ LOW

### Actions

#### 1. Add `fix_source_links()` to `decorate_api_mdx.py`

The original regex was too narrow: it assumed `.venv-docs-autogen` as the only venv name and `main` as the only source branch. The generalized version handles any `site-packages/` path regardless of venv name, and re-points to the correct branch or tag.

```python
import re

# Matches any GitHub blob URL that routes through a venv/site-packages path
# before reaching a mellea/ or cli/ source file.
# Groups: (1) file path relative to repo root, (2) optional #Lnnn line anchor
_VENV_SOURCE_RE = re.compile(
    r'https://github\.com/[^/]+/[^/]+/blob/[^/]+'  # any repo, any ref
    r'/(?:[^/]+/)?'                                  # optional venv folder (e.g. .venv-docs-autogen/)
    r'(?:lib/python\d+\.\d+/site-packages/)?'        # optional site-packages
    r'((?:mellea|cli)/[^)#"]+?\.py)'                 # capture: mellea/ or cli/ file path
    r'(#L\d+)?'                                      # capture: optional line anchor
)

def fix_source_links(mdx_text: str, repo_base: str, version: str | None = None) -> str:
    """Re-point any venv-routed source links to the canonical repository URL.

    Args:
        mdx_text: MDX file content.
        repo_base: Repository base URL, e.g.
            "https://github.com/generative-computing/mellea".
        version: Package version string (e.g. "0.3.0"). Links point to
            the tag "v{version}" if given, otherwise "main".

    Returns:
        MDX text with corrected source links.
    """
    branch = f"v{version}" if version else "main"

    def _replace(m: re.Match) -> str:
        file_path = m.group(1)
        line_anchor = m.group(2) or ""
        return f"{repo_base}/blob/{branch}/{file_path}{line_anchor}"

    result = _VENV_SOURCE_RE.sub(_replace, mdx_text)
    if result != mdx_text:
        count = len(_VENV_SOURCE_RE.findall(mdx_text))
        print(f"   🔗 Fixed {count} source links → {repo_base}/blob/{branch}/")
    return result
```

#### 2. Integrate into `process_mdx_file()`

```python
REPO_BASE = "https://github.com/generative-computing/mellea"

def process_mdx_file(path: Path, version: str | None = None) -> bool:
    original = path.read_text(encoding="utf-8")
    text = inject_sidebar_fix(original)                         # Step 1
    text = decorate_mdx_body(text)                              # Step 2
    text = fix_source_links(text, REPO_BASE, version=version)   # Step 3 (NEW)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False
```

#### 3. Add `--version` to `decorate_api_mdx.py` main()
```python
parser.add_argument("--version", type=str, default=None,
                    help="Package version for source links (e.g., 0.3.0)")
# ...
for f in mdx_files:
    if process_mdx_file(f, version=args.version):
        changed += 1
```

#### 4. Validation in `validate.py`
```python
def validate_source_links(api_dir: Path) -> dict:
    venv_links, invalid_links = [], []
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text()
        venv_matches = re.findall(
            r'\[View Source\]\((https://[^)]*\.venv-docs-autogen[^)]*)\)', content)
        venv_links.extend([{'file': str(mdx_file), 'url': u} for u in venv_matches])
        for url in re.findall(r'\[View Source\]\((https://github\.com/[^)]+)\)', content):
            if not re.match(
                r'https://github\.com/generative-computing/mellea/blob/[^/]+/'
                r'(mellea|cli)/.+\.py(#L\d+)?$', url):
                invalid_links.append({'file': str(mdx_file), 'url': url})
    return {'venv_links': venv_links, 'invalid_links': invalid_links,
            'passed': len(venv_links) == 0 and len(invalid_links) == 0}
```

#### 5. Unit tests
```python
# test/tooling/docs-autogen/test_source_links.py
def test_fix_source_links_python311():
    """Python 3.11 venv path."""
def test_fix_source_links_python314():
    """Python 3.14 venv path."""
def test_fix_source_links_cli_package():
    """cli/ package path."""
def test_fix_source_links_preserves_line_numbers():
    """#L123 anchors preserved."""
def test_fix_source_links_with_version():
    """Version-specific links (v0.3.0)."""
```

### Acceptance Criteria
- 100% source links point to `https://github.com/.../blob/...`
- 0 links contain `.venv-docs-autogen/`

---

## Phase 2: Ensure Existing APIs are Documented

**Risk:** ⚠️ MEDIUM — `__all__` logic, CLI extraction

### Actions

#### 1. Griffe-based public symbol discovery (replaces raw `ast`)

Raw `ast` walking fails on `__all__ += [...]`, tuple-form `__all__`, and re-exports. Griffe (already a dep in `requirements.txt`) handles all of these correctly and is already used in Phase 4 — use it here too to avoid maintaining two separate symbol-resolution strategies.

```python
# tooling/docs-autogen/audit_coverage.py
from griffe import GriffeLoader

def get_public_symbols_for_package(package: str) -> dict[str, set[str]]:
    """Get public symbols per source file using Griffe.

    Handles __all__ += [...], tuple __all__, re-exports, and dynamic
    __all__ construction that raw ast walking misses.

    Args:
        package: Package name to analyze, e.g. "mellea" or "cli".

    Returns:
        Dict mapping module filepath string to set of public symbol names.
    """
    loader = GriffeLoader()
    pkg_obj = loader.load(package)
    result: dict[str, set[str]] = {}

    def _collect(obj) -> None:
        # Skip aliases (re-exported names) and virtual objects without a file
        if obj.is_alias or not obj.filepath:
            return
        if obj.exports is not None:
            # __all__ was explicitly defined
            symbols = set(obj.exports)
        else:
            # No __all__: include non-underscore members defined here (not imported)
            symbols = {
                name for name, member in obj.members.items()
                if not name.startswith('_') and not member.is_alias
            }
        if symbols:
            result[str(obj.filepath)] = symbols
        # Recurse into subpackages
        for member in obj.members.values():
            if hasattr(member, 'members'):
                _collect(member)

    _collect(pkg_obj)
    return result
```

#### 2. CLI (Typer) command extraction

**Resolved (confirmed against Typer 0.19.2):** mdxify processes modules via `griffe` static analysis — it does not invoke the Typer app at runtime. Typer CLI commands are not surfaced by mdxify; use the AST fallback below. Additionally, Typer 0.19.2 automatically injects two hidden params on every command (`install_completion`, `show_completion`); these must be filtered out when generating parameter tables.

**Filter for auto-injected Typer params:**

```python
_TYPER_INTERNAL_PARAMS = {"install_completion", "show_completion"}

def filter_typer_params(params: list) -> list:
    """Remove Typer-injected internal params from a Click command's param list."""
    return [p for p in params if p.name not in _TYPER_INTERNAL_PARAMS]
```

**AST fallback** (required — mdxify does not document Typer commands). Handles `@app.command()`, `@app.command(name="...")`, and nested sub-app groups. **Note:** Run unit tests for `extract_typer_commands()` against every Python version in the project's test matrix — AST decorator representation changed in Python 3.8→3.9 and can differ again in 3.12+. The tests are cheap to parametrize and prevent silent misparsing under a future Python upgrade.

```python
def extract_typer_commands(cli_path: Path) -> list[dict]:
    """Extract Typer command metadata from a CLI file via AST.

    Args:
        cli_path: Path to the Python file containing Typer app definitions.

    Returns:
        List of dicts with keys: name, function, docstring.
    """
    import ast
    tree = ast.parse(cli_path.read_text())
    commands = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not (isinstance(dec, ast.Call) and hasattr(dec.func, 'attr')
                    and dec.func.attr == 'command'):
                continue
            # Resolve explicit name= keyword argument; fall back to function name
            cmd_name = node.name.replace('_', '-')
            for kw in dec.keywords:
                if kw.arg == 'name' and isinstance(kw.value, ast.Constant):
                    cmd_name = kw.value.value
                    break
            commands.append({
                'name': cmd_name,
                'function': node.name,
                'docstring': ast.get_docstring(node),
            })
    return commands
```

#### 3. Coverage audit script

```python
# tooling/docs-autogen/audit_coverage.py
def audit_api_coverage(repo_root: Path) -> dict:
    """Audit API documentation coverage across mellea and cli packages."""
    results: dict = {'warnings': []}
    for package in ['mellea', 'cli']:
        try:
            public_symbols = get_public_symbols_for_package(package)
        except Exception as e:
            results['warnings'].append(f"Failed to load {package} with Griffe: {e}")
            public_symbols = {}

        docs_path = repo_root / "docs" / "docs" / "api" / package
        documented: set[str] = set()
        if docs_path.exists():
            for mdx_file in docs_path.rglob("*.mdx"):
                documented.update(re.findall(r'##\s+`([^`]+)`', mdx_file.read_text()))

        total_public = sum(len(s) for s in public_symbols.values())
        results[package] = {
            'total_modules': len(public_symbols),
            'total_public_symbols': total_public,
            'documented_symbols': len(documented),
            'coverage': len(documented) / total_public if total_public > 0 else 0.0,
            'missing': [
                {'module': m, 'symbols': list(s - documented)}
                for m, s in public_symbols.items() if s - documented
            ],
        }
    return results
```

**Verification:** After implementing, run `uv run python tooling/docs-autogen/audit_coverage.py` and confirm it prints coverage percentages for both `mellea` and `cli` without errors. Record the baseline in `docs/metrics/coverage-baseline.json` before setting the +10% target.

#### 4. Coverage target
Establish baseline first, then target = baseline + 10% (likely ~95%).

Document exclusions:
```json
{
  "intentionally_private": ["mellea.helpers._internal"],
  "deprecated": [],
  "experimental": []
}
```

### Acceptance Criteria
- API coverage ≥ target (baseline + 10%)
- Coverage metrics reported in CI job summary
- CLI commands documented

---

## Phase 3: Docstring Compliance (Google Style)

**Risk:** ✅ LOW

### Actions

#### 1. Ruff configuration
```toml
# Already present in pyproject.toml — verify these exist:
[tool.ruff.lint.pydocstyle]
convention = "google"  # ✅ Already set

# ADD this if not present:
[tool.ruff.lint.per-file-ignores]
"test/**" = ["D"]  # Don't require docstrings in tests
```

#### 2. Fix violations
```bash
uv run ruff check --select D mellea/ cli/       # find
uv run ruff check --select D --fix mellea/ cli/  # auto-fix
```

Common violations:

| Code | Issue | Fix |
|------|-------|-----|
| D205 | Missing blank line | Add blank line before `Args:` |
| D212 | Summary on wrong line | Move summary to first line |
| D400 | Missing period | Add period to summary |
| D401 | Not imperative mood | Use "Return" not "Returns" |

#### 3. Pre-commit hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--select, D, --fix]
        files: ^(mellea|cli)/.*\.py$
```

Then activate: `pre-commit install`

#### 4. VS Code snippets
```json
// .vscode/python.code-snippets
{
  "Google Style Function Docstring": {
    "prefix": "docf",
    "body": [
      "\"\"\"${1:Brief description}.\"\"\"",
      "",
      "Args:",
      "    ${2:param}: ${3:Description}",
      "",
      "Returns:",
      "    ${4:Description}",
      "\"\"\""
    ]
  }
}
```

### Acceptance Criteria
- Ruff `D` rules pass on `mellea/` and `cli/`
- Dropped sections count = 0

---

## Phase 4: Cross-References

**Risk:** ⚠️ MEDIUM — Mintlify anchor algorithm is provisional; confirm with probe before Phase 4B.

### Phase 4A: Confirm Mintlify Anchor Algorithm

The provisional `generate_mintlify_anchor()` below is derived from the known Mintlify heading-slug rules and is ready to use. **Run the probe once against the PR 601 preview** (`https://ibm-llm-runtime-aaf3a78b.mintlify.app/`) to confirm before Phase 4B. If the probe reveals differences, update the function in place. If the preview URL is behind authentication or unavailable, run `mintlify dev` locally (`cd docs && mintlify dev`) and probe `http://localhost:3000/` instead. If neither environment is available, proceed with Phase 4B using the provisional implementation — the anchor collision checker in Phase 4C will catch any mismatches at validation time.

**Provisional implementation (use immediately):**

```python
def generate_mintlify_anchor(heading_text: str) -> str:
    """Generate the Mintlify anchor fragment for a heading.

    Rules (provisional — verify with probe_mintlify_anchors.py):
      - Strip surrounding backticks
      - Remove dots (Class.method → classmethod)
      - Remove square brackets (Type[T] → TypeT)
      - Lowercase everything
      - Underscores and dunders are preserved (__init__ → __init__)

    Args:
        heading_text: The heading text, e.g. "`Session`" or "`Session.run`".

    Returns:
        Anchor fragment without leading #, e.g. "session" or "sessionrun".
    """
    text = heading_text.strip('`')
    text = text.replace('.', '')
    text = re.sub(r'[\[\]]', '', text)
    return text.lower()
```

**Probe script** (run once, confirm rules, update function if needed):

```python
# tooling/docs-autogen/probe_mintlify_anchors.py
# Run against: https://ibm-llm-runtime-aaf3a78b.mintlify.app/  (PR 601 preview)
# or: cd docs && mintlify dev  then http://localhost:3000/
import requests
from bs4 import BeautifulSoup

TEST_CASES = [
    "`ClassName`",       # expect: classname
    "`function_name`",   # expect: function_name
    "`Class.method`",    # expect: classmethod
    "`__init__`",        # expect: __init__
    "`Type[T]`",         # expect: typet
    "`CONSTANT`",        # expect: constant
]

def probe_anchors(url: str) -> dict[str, str]:
    """Scrape Mintlify page and extract heading text → anchor id mappings."""
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    return {h.get_text(strip=True): h.get('id')
            for h in soup.find_all(['h2', 'h3', 'h4']) if h.get('id')}

if __name__ == '__main__':
    # 1. Add test headings from TEST_CASES to a test MDX page in the docs
    # 2. Deploy (mintlify dev or PR 601 preview)
    # 3. Run this script and compare actual vs expected
    # 4. Update generate_mintlify_anchor() if rules differ
    anchors = probe_anchors("http://localhost:3000/test-anchors")
    for text, anchor in anchors.items():
        expected = generate_mintlify_anchor(text)
        match = "✅" if expected == anchor else "❌"
        print(f"{match} {text:30} → #{anchor}  (expected: #{expected})")
```

Expected probe output (provisional):

| Heading | Expected anchor | Rule |
|---------|----------------|------|
| `` `ClassName` `` | `classname` | Lowercase, strip backticks |
| `` `function_name` `` | `function_name` | Underscores preserved |
| `` `Class.method` `` | `classmethod` | Dots removed |
| `` `__init__` `` | `__init__` | Dunders preserved |
| `` `Type[T]` `` | `typet` | Brackets removed |

#### Griffe-based symbol resolution (preferred over markdown-it-py)
```python
from griffe import GriffeLoader

def build_symbol_index(api_dir: Path) -> dict[str, str]:
    """Build symbol → base URL mapping (without anchor fragment)."""
    loader = GriffeLoader()
    for pkg in ['mellea', 'cli']:
        loader.load(pkg)
    index = {}
    for obj in loader.modules.values():
        for member in obj.members.values():
            fqn = f"{obj.path}.{member.name}"
            base_url = f"/api/{obj.path.replace('.', '/')}"
            index[fqn] = base_url
            if member.name not in index:  # avoid collisions
                index[member.name] = base_url
    return index
```

> [!NOTE]
> `build_symbol_index()` stores the **page URL only** (no `#anchor`). The anchor is generated by `generate_mintlify_anchor()` and appended in `linkify_backticks()`.

#### `hero_symbols.json` — priority cross-reference targets

A curated list of symbols that *must* be linked wherever they appear in backticks (CI fails if any are unlinked). Prevents regressions on the most user-facing APIs.

```json
// tooling/docs-autogen/hero_symbols.json
{
  "must_link": [
    "Session", "Backend", "Formatter", "SamplingConfig",
    "ChatFormatter", "TemplateFormatter", "Instruction", "GenSlot"
  ]
}
```

`validate.py` checks that every occurrence of a hero symbol in backticks is linkified. Add to `validate.py`:

```python
def validate_hero_symbols(api_dir: Path, hero_file: Path) -> dict:
    """Fail if any hero symbol appears as bare backtick in generated docs."""
    heroes = json.loads(hero_file.read_text())["must_link"]
    unlinked = []
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text()
        for sym in heroes:
            # bare backtick: `Sym` not preceded by [ (which would be a link)
            if re.search(rf'(?<!\[)`{re.escape(sym)}`(?!\])', content):
                unlinked.append({"file": str(mdx_file), "symbol": sym})
    return {"passed": len(unlinked) == 0, "unlinked": unlinked}
```

### Phase 4B: Implementation

`linkify_backticks()` is fenced-block-aware: it segments the document on ```` ``` ````…```` ``` ```` blocks before substituting, so symbols inside code samples are never rewritten.

```python
import re
from pathlib import Path
from urllib.parse import urlparse

# Pre-compiled patterns
_FENCED_BLOCK = re.compile(r'```.*?```', re.DOTALL)
_BACKTICK_SYMBOL = re.compile(r'(?<!`)`([A-Za-z_][A-Za-z0-9_.]*)`(?!`)')


def _link_or_warn(mm: re.Match, symbol_index: dict, warnings: list) -> str:
    symbol = mm.group(1)
    base = symbol_index.get(symbol)
    if not base:
        warnings.append(f"Unknown symbol: {symbol}")
        return mm.group(0)
    anchor = generate_mintlify_anchor(symbol)
    return f"[`{symbol}`]({base}#{anchor})"


def linkify_backticks(md_text: str, symbol_index: dict) -> tuple[str, list[str]]:
    """Transform backtick-wrapped symbols into cross-reference links.

    Skips fenced code blocks entirely so symbols in code samples are
    never rewritten. Uses generate_mintlify_anchor() for fragment generation.

    Args:
        md_text: MDX document text.
        symbol_index: Mapping of symbol name → page base URL
            (from build_symbol_index()).

    Returns:
        Tuple of (rewritten text, list of warning strings for unknown symbols).
    """
    warnings: list[str] = []
    segments, last = [], 0
    for m in _FENCED_BLOCK.finditer(md_text):
        pre = md_text[last:m.start()]
        pre = _BACKTICK_SYMBOL.sub(
            lambda mm: _link_or_warn(mm, symbol_index, warnings), pre)
        segments.append(pre)
        segments.append(md_text[m.start():m.end()])  # fenced block unchanged
        last = m.end()
    tail = md_text[last:]
    tail = _BACKTICK_SYMBOL.sub(
        lambda mm: _link_or_warn(mm, symbol_index, warnings), tail)
    segments.append(tail)
    return "".join(segments), warnings
```

Cross-ref validation with correct path mapping (strips `/api/` prefix, adds `.mdx`, ignores `#fragment`):

```python
def _mdx_path_for_api_url(api_dir: Path, url: str) -> Path:
    """Map a site URL like /api/mellea/stdlib/session#classname
    to a filesystem path like <api_dir>/mellea/stdlib/session.mdx.

    Returns a sentinel path starting with /__  for external or non-api URLs
    so callers can skip them cleanly.
    """
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        return Path("/__external__")
    path = parsed.path  # strip fragment
    if not path.startswith("/api/"):
        return Path("/__non_api__")
    rel = path[len("/api/"):]  # "mellea/stdlib/session"
    return (api_dir / rel).with_suffix(".mdx")


def validate_cross_references(api_dir: Path) -> dict:
    """Validate that all cross-reference links in generated MDX resolve to
    real files.

    Args:
        api_dir: Root of the generated API docs, e.g. docs/docs/api/.

    Returns:
        Dict with keys: passed, total_links, broken_links, success_rate.
    """
    broken_links: list[dict] = []
    total_links = 0
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text(encoding="utf-8")
        for symbol, url in re.findall(r'\[`([^`]+)`\]\(([^)]+)\)', content):
            total_links += 1
            target = _mdx_path_for_api_url(api_dir, url)
            if str(target).startswith("/__"):
                continue  # external or non-api link — skip
            if not target.exists():
                broken_links.append(
                    {'file': str(mdx_file), 'symbol': symbol, 'url': url})
    return {
        'passed': len(broken_links) == 0,
        'total_links': total_links,
        'broken_links': broken_links,
        'success_rate': 1 - (len(broken_links) / total_links) if total_links > 0 else 1.0,
    }
```

### Phase 4C: Validation

Run `validate_cross_references()` on the full generated output — it confirms every linked MDX file exists on disk. This covers structural correctness for all links automatically. For rendering QA, spot-check 5 pages in `mintlify dev` (not 20 — structural issues are already caught by the validator). Focus manual spot-checks on pages with the highest symbol density: `session.mdx`, `backend.mdx`, `chat_formatter.mdx`, `sampling/base.mdx`, `components/instruction.mdx`.

**Anchor collision detection** — add to `validate.py` and include in the validation report. Mintlify's anchor algorithm (`generate_mintlify_anchor()`) strips dots and lowercases, meaning `get_user()` and `GetUser` both map to `#getuser`. Flag these before deployment:

```python
def check_anchor_collisions(api_dir: Path) -> dict:
    """Detect headings on the same page that map to duplicate Mintlify anchors.

    Args:
        api_dir: Root of the generated API docs.

    Returns:
        Dict with keys: passed, collisions (list of dicts).
    """
    collisions: list[dict] = []
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text(encoding="utf-8")
        headings = re.findall(r'^#{2,6}\s+`([^`]+)`', content, re.MULTILINE)
        seen: dict[str, str] = {}
        for heading in headings:
            anchor = generate_mintlify_anchor(heading)
            if anchor in seen:
                collisions.append({
                    'file': str(mdx_file),
                    'anchor': anchor,
                    'heading1': seen[anchor],
                    'heading2': heading,
                })
            else:
                seen[anchor] = heading
    return {'passed': len(collisions) == 0, 'collisions': collisions}
```

Add `check_anchor_collisions()` to `validate.py` main() alongside the other checks.

**Verification:** After Phase 4B, run:

```bash
uv run python tooling/docs-autogen/validate.py \
  --api-dir docs/docs/api \
  --output /tmp/validation-phase4.json
jq '.checks.cross_references.success_rate, .checks.anchor_collisions.passed' \
  /tmp/validation-phase4.json
```

Expected: success_rate ≥ 0.80, anchor_collisions.passed = true.

### Acceptance Criteria

- Cross-ref linkification rate ≥ 80%
- 0 broken cross-ref links
- 0 anchor collisions

---

## Phase 5: Structural Enhancements

**Risk:** ✅ LOW

### Preamble format
```json
// tooling/docs-autogen/preambles.json
{
  "mellea": {
    "title": "Mellea Core Library",
    "description": "Core abstractions and standard library",
    "sections": [
      {"title": "Core", "modules": ["core.backend", "core.base", "core.sampling"]},
      {"title": "Standard Library", "modules": ["stdlib.session", "stdlib.components"]}
    ]
  }
}
```

### Preamble injection
```python
def inject_preamble(mdx_file: Path, preamble: dict) -> None:
    """Inject module overview preamble after frontmatter."""
    content = mdx_file.read_text(encoding="utf-8")
    # Find end of frontmatter (second ---)
    parts = content.split('---', 2)
    if len(parts) < 3:
        return  # No frontmatter found

    toc_lines = [f"\n## {preamble['title']}\n", f"{preamble['description']}\n"]
    for section in preamble.get('sections', []):
        toc_lines.append(f"\n### {section['title']}")
        for mod in section['modules']:
            slug = mod.replace('.', '/')
            toc_lines.append(f"- [`{mod}`](/api/mellea/{slug})")

    new_content = f"---{parts[1]}---" + '\n'.join(toc_lines) + '\n' + parts[2]
    mdx_file.write_text(new_content, encoding="utf-8")
```

### Orphaned module discovery
```python
def find_referenced_modules(pkg_path: Path) -> set[Path]:
    """Walk __init__.py files and parse __all__ to find referenced modules."""
    import ast
    referenced = set()
    for init_file in pkg_path.rglob("__init__.py"):
        try:
            tree = ast.parse(init_file.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            # Collect from __all__
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    mod_path = init_file.parent / f"{elt.value}.py"
                                    if mod_path.exists():
                                        referenced.add(mod_path)
                                    # Also check for subpackage
                                    pkg = init_file.parent / elt.value / "__init__.py"
                                    if pkg.exists():
                                        referenced.add(pkg)
            # Collect from relative imports
            if isinstance(node, ast.ImportFrom) and node.level > 0 and node.module:
                mod_path = init_file.parent / f"{node.module.replace('.', '/')}.py"
                if mod_path.exists():
                    referenced.add(mod_path)
    return referenced

def find_orphaned_modules(repo_root: Path) -> list[str]:
    orphaned = []
    for package in ['mellea', 'cli']:
        pkg_path = repo_root / package
        referenced = find_referenced_modules(pkg_path)
        for module in pkg_path.rglob("*.py"):
            if not module.name.startswith('_') and module not in referenced:
                orphaned.append(str(module))
    return orphaned
```

### Deferred to Timescale B *(Gemini)*
Type signature cleanup (`Union[X, None]` → `X | None`) — too risky with regex on nested generics.

---

## Phase 6: Validation & Monitoring

### `validate.py` main() skeleton
```python
#!/usr/bin/env python3
import argparse, json
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Validate generated API docs")
    parser.add_argument("--api-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {"passed": True, "total_checks": 0, "passed_checks": 0, "failed_checks": 0},
        "checks": {
            "source_links": validate_source_links(args.api_dir),
            "api_coverage": {},  # filled by audit_coverage
            "cross_references": validate_cross_references(args.api_dir),
            "docstring_compliance": {"passed": True, "ruff_violations": 0, "dropped_sections": 0},
        },
        "warnings": [],
    }
    # Compute summary
    checks = report["checks"]
    for name, check in checks.items():
        if isinstance(check, dict) and "passed" in check:
            report["summary"]["total_checks"] += 1
            if check["passed"]:
                report["summary"]["passed_checks"] += 1
            else:
                report["summary"]["failed_checks"] += 1
                report["summary"]["passed"] = False
                report["warnings"].append(f"{name} check failed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))
    print(f"{'✅' if report['summary']['passed'] else '❌'} Validation report: {args.output}")
    return 0 if report["summary"]["passed"] else 1

if __name__ == "__main__":
    import sys; sys.exit(main())
```

### Report schema
```json
{
  "timestamp": "2026-03-10T10:00:00Z",
  "version": "0.3.0",
  "summary": {"passed": false, "total_checks": 4, "passed_checks": 3, "failed_checks": 1},
  "checks": {
    "source_links": {"passed": true, "total_links": 1234, "venv_links": 0, "invalid_links": 0},
    "api_coverage": {
      "passed": true,
      "mellea": {"coverage": 0.96, "target": 0.95, "total_public_symbols": 234, "documented_symbols": 225},
      "cli": {"coverage": 0.94, "target": 0.95}
    },
    "cross_references": {"passed": false, "total_links": 567, "broken_links": 3, "success_rate": 0.995},
    "docstring_compliance": {"passed": true, "ruff_violations": 0, "dropped_sections": 0}
  },
  "warnings": ["3 cross-reference links are broken"]
}
```

### CI PR comment
```yaml
- name: Check validation
  run: |
    PASSED=$(jq -r '.summary.passed' docs/docs/api/.validation-report.json)
    if [ "$PASSED" != "true" ]; then
      jq '.warnings' docs/docs/api/.validation-report.json
      exit 1
    fi
- name: Comment PR with metrics
  uses: actions/github-script@v7
  with:
    script: |
      const report = JSON.parse(require('fs').readFileSync(
        'docs/docs/api/.validation-report.json'));
      const body = `## 📊 Docs Validation
      **Status**: ${report.summary.passed ? '✅ PASSED' : '❌ FAILED'}
      - **Coverage**: mellea ${(report.checks.api_coverage.mellea.coverage*100).toFixed(1)}%
      - **Source Links**: ${report.checks.source_links.venv_links} broken
      - **Cross-Refs**: ${report.checks.cross_references.broken_links} broken`;
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner, repo: context.repo.name, body});
```

### Contributor documentation
- Update CONTRIBUTING.md with `make docs` workflow
- Add docstring standards to AGENTS.md
- Create `docs/DOCS_DEVELOPMENT.md` guide
- Add troubleshooting section to README

### Metrics tracking
Store in `docs/metrics/coverage-history.csv`. Track: API coverage %, cross-ref success rate, doc generation time, CI duration.

---

## Testing Strategy

| Type | Location | Covers |
|------|----------|--------|
| Unit | `test/tooling/docs-autogen/test_source_links.py` | Source link regex |
| Unit | `test/tooling/docs-autogen/test_coverage.py` | API coverage audit |
| Unit | `test/tooling/docs-autogen/test_cross_refs.py` | Cross-ref linkification |
| Integration | `test/tooling/docs-autogen/test_full_pipeline.py` | End-to-end generation |

Manual QA: source links, API completeness, cross-refs, Mintlify rendering, navigation.

### Rollback (all phases)
```bash
git revert <hash>                          # revert commits
git checkout v0.3.1 -- docs/docs/api       # restore previous docs
mintlify deploy                            # redeploy
```

---

## Risk Mitigation Matrix

| Phase | Risk | Impact | Mitigation |
|-------|------|--------|------------|
| 0 | CI breaks | High | Parallel pip fallback for 1 release |
| 1 | Wrong links | Medium | `validate.py` catches 100% |
| 2 | Missing APIs | Low | Coverage report in PR |
| 3 | Broken docstrings | Medium | Ruff pre-commit prevents regressions |
| 4 | Broken cross-refs | High | Phase 4A probe first; extensive testing |
| 5 | Structural issues | Low | Manual review of preambles |

---

## Quick-Win Checklist

Ordered by impact. Items marked ⚠️ are blockers for later phases.

- [ ] ⚠️ Add `--no-venv` flag to `generate-ast.py` (Phase 0 prerequisite — without this, the wheel build silently falls back to PyPI)
- [ ] Check latest `mdxify` and `griffe` versions; update `requirements.txt` pins and matching `--with` flag in `docs-autogen-pr.yml`
- [ ] Remove `|| true` from `pip install` line in `docs-autogen-pr.yml` (silent failure suppression)
- [ ] Add `actions: read` permission to `docs-autogen-pr.yml` (for cache metadata)
- [ ] Create `tooling/docs-autogen/build.py` wrapper (with `--no-venv` passthrough)
- [ ] Add `Makefile` with all targets
- [ ] Implement `fix_source_links()` in `decorate_api_mdx.py` (generalized regex — direct user impact)
- [ ] Run `uv run ruff check --select D mellea/ cli/` and record violation count as baseline
- [ ] Add VS Code docstring snippets (`.vscode/python.code-snippets`)
- [ ] Create `tooling/docs-autogen/validate.py` skeleton
- [ ] Update `docs-autogen-pr.yml` (native `setup-uv` cache + lock determinism + safe PR diff)
- [ ] Run `audit_coverage.py` and save baseline to `docs/metrics/coverage-baseline.json`

---

## Prioritized Enhancements

### P1 — During Timescale A

| Enhancement | Phase | Source |
|-------------|-------|--------|
| `--no-venv` flag on `generate-ast.py` | 0 | Claude synthesis |
| CI native `setup-uv` cache (`enable-cache: true`) | 0 | Gemini |
| Lock determinism guard (`uv lock && git diff`) | 0 | Copilot |
| Safe PR diff baseline (BASE_SHA / HEAD_SHA) | 0 | Copilot |
| CI wheel upload as artifact | 0 | Bob |
| Validation report upload as artifact | 0 | Copilot |
| Pre-release version handling (`v0.3.0-rc1`) | 0 | Bob |
| Generalized `fix_source_links()` regex | 1 | Copilot/Claude |
| Griffe-based coverage (replaces raw `ast`) | 2 | Gemini |
| Typer `name=` keyword support | 2 | Copilot |
| Common violations table in CONTRIBUTING | 3 | Bob |
| Fenced-block-aware `linkify_backticks()` | 4 | Copilot |
| Cross-ref validator path fix | 4 | Copilot |
| Anchor collision detection | 4 | Gemini |
| `hero_symbols.json` — must-link APIs | 4 | Copilot |
| Decision gates after Phase 0 and Phase 3 | All | Bob |

### P2 — Stretch

| Enhancement | Phase | Source |
|-------------|-------|--------|
| `make docs-ci` target mirroring CI invocation | 0 | Copilot |
| Docstring regressions: fail CI on count increase | 3 | Copilot |
| Doc quality dashboard (GitHub Pages) | 6 | Bob |
| Coverage regression alerts | 6 | Bob |
| ISO 8601 strict timestamps in coverage CSV | 6 | Gemini |

### P3 — Timescale B
| Enhancement | Source |
|-------------|--------|
| Canonical URL builder via `inspect` | Copilot |
| `markdown-it-py` token transforms | Copilot |
| Versioned docs with `mike` | Copilot |
| Redirect policy for existing links | Copilot |
| Full `mkdocs` + `mkdocstrings` migration | All |

### Decision Points
- **After Phase 0:** Measure CI improvement. Continue or rollback.
- **After Phase 3:** Assess fix effort. Proceed to Phase 4 or defer.
- **After Phase 4A:** If anchors can't be determined → defer. If griffe fails → alternative.

---

## Timescale B (Future)

Migrate to **`mkdocs` + `mkdocstrings` + `mkdocs-material`**. When scoping:
- Decide on versioned docs early (`mike`)
- Evaluate keeping Mintlify content alongside or fully unifying
- Plan redirect policy for existing links
