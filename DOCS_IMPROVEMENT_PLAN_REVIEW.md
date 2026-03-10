# Documentation Improvement Plan - Comprehensive Review

**Review Date**: 2026-03-10  
**Reviewer**: Bob (AI Code Assistant)  
**Plan Version**: DOCS_IMPROVEMENT_PLAN.md (Timescale A)  
**Review Type**: Technical Feasibility, Strategic Alignment, and Completeness

---

## Executive Summary

**Overall Assessment**: Well-structured plan with clear phases and actionable items. Strong technical foundation with pragmatic phasing approach. Requires modifications to address implementation risks before execution.

**Verdict**: ✅ **APPROVE WITH MODIFICATIONS**

**Key Strengths**:
- Pragmatic iterative approach vs. complete rewrite
- Incorporates feedback from multiple AI reviewers (Gemini, Copilot, Bob)
- Clear acceptance criteria for each phase
- Addresses root causes (e.g., using ruff for docstring validation)
- Defers risky changes (type signature cleanup) to Timescale B

**Critical Issues**:
- Phase 0 migration strategy has execution risks
- Phase 4 cross-reference implementation underspecified
- Missing validation and rollback strategies
- Incomplete dependency analysis

**Recommended Timeline**:
- Week 1: Address critical issues, set up test infrastructure
- Week 2-3: Execute Phase 0-3 (foundation)
- Week 4-5: Execute Phase 4-5 (enhancements)
- Week 6: Phase 6 (validation) + documentation updates

---

## Quick Reference: Risk Levels

| Phase | Risk Level | Key Issues |
|-------|-----------|------------|
| Phase 0: uv Migration | ⚠️ HIGH | PyPI availability, cache strategy, CI triggers |
| Phase 1: Source Links | ✅ LOW | Well-specified, clear implementation |
| Phase 2: API Coverage | ⚠️ MEDIUM | `__all__` logic, CLI extraction, coverage target |
| Phase 3: Docstrings | ✅ LOW | Leverages existing tools, clear path |
| Phase 4: Cross-References | 🔴 HIGH | Complex implementation, validation gaps |
| Phase 5: Structure | ✅ LOW | Straightforward enhancements |

---

## 1. Technical Feasibility Review

### Phase 0: `uv` Migration & Unified Build Command

**Risk Level**: ⚠️ **HIGH RISK**

#### Critical Issue #1: Ephemeral deps approach may fail

**Current Plan**:
```bash
uv run --isolated --with mellea==${VERSION} --with mdxify
```

**Problems**:
- If `${VERSION}` isn't published to PyPI yet, this fails
- Current CI publishes to PyPI *after* tagging (chicken-egg problem)
- No handling for pre-release versions (`v0.3.0-rc1`)

**Recommended Fix**:
```bash
# Build wheel first, install from local artifact
uv build
uv run --isolated --with ./dist/mellea-${VERSION}-py3-none-any.whl --with mdxify
```

**CI Implementation**:
```yaml
- name: Build wheel
  run: uv build

- name: Upload wheel artifact
  uses: actions/upload-artifact@v4
  with:
    name: mellea-wheel
    path: dist/*.whl
    retention-days: 1

- name: Generate docs from wheel
  run: |
    WHEEL=$(ls dist/*.whl)
    uv run --isolated --with "${WHEEL}" --with mdxify \
      python tooling/docs-autogen/build.py \
      --pkg-version "${VERSION}" \
      --link-base "https://github.com/generative-computing/mellea/blob/v${VERSION}"
```

#### Critical Issue #2: CI trigger expansion risk

**Problem**: Triggering on every `mellea/**`, `cli/**` change will run on *every* PR, significantly increasing CI costs.

**Recommended Fix**:
```yaml
on:
  push:
    tags:
      - "v*"
  pull_request:
    paths:
      - 'mellea/**/*.py'
      - 'cli/**/*.py'
      - 'tooling/docs-autogen/**'
  workflow_dispatch: {}

jobs:
  docs_autogen:
    runs-on: ubuntu-latest
    steps:
      - name: Check if docs generation needed
        id: check
        run: |
          if [[ "${{ github.event_name }}" == "push" ]] && [[ "${{ github.ref }}" =~ ^refs/tags/v ]]; then
            echo "run=true" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "run=true" >> $GITHUB_OUTPUT
          else
            # For PRs, check if docstrings changed
            CHANGED=$(git diff --name-only origin/${{ github.base_ref }}...HEAD | \
              grep -E '^(mellea|cli)/.*\.py$' | \
              xargs grep -l '^\s*"""' 2>/dev/null || true)
            if [ -n "$CHANGED" ]; then
              echo "run=true" >> $GITHUB_OUTPUT
            else
              echo "run=false" >> $GITHUB_OUTPUT
            fi
          fi

      - name: Generate docs
        if: steps.check.outputs.run == 'true'
        run: |
          # ... generation steps
```

#### Critical Issue #3: Missing rollback strategy

**Recommended Addition**:
```markdown
### Phase 0 Rollback Procedure

**Option 1: Immediate Revert**
```bash
git revert <commit-hash>
git push origin main
```

**Option 2: Parallel Workflow (Recommended)**
- Keep `generate-ast.py` using pip for 1 release cycle
- Add `generate-ast-uv.py` as experimental
- Switch default after validation

**Option 3: Emergency CI Fallback**
```yaml
- name: Generate docs (uv)
  id: uv_gen
  continue-on-error: true
  run: uv run python tooling/docs-autogen/build.py

- name: Generate docs (pip fallback)
  if: steps.uv_gen.outcome == 'failure'
  run: python tooling/docs-autogen/generate-ast.py
```
```

#### Issue #4: Cache strategy incomplete

**Recommended Enhancement**:
```yaml
- uses: actions/cache@v4
  id: cache
  with:
    path: ~/.cache/uv
    key: uv-${{ runner.os }}-${{ hashFiles('pyproject.toml', 'uv.lock') }}-v2
    restore-keys: |
      uv-${{ runner.os }}-${{ hashFiles('pyproject.toml', 'uv.lock') }}-
      uv-${{ runner.os }}-

- name: Report cache status
  run: |
    if [ "${{ steps.cache.outputs.cache-hit }}" == "true" ]; then
      echo "✅ Cache hit - using cached dependencies"
    else
      echo "⚠️ Cache miss - downloading dependencies"
    fi
```

#### Acceptance Criteria Enhancement

**Add Baseline Measurements**:
```markdown
### Phase 0: Establish Baseline

Before migration, measure:
- Total CI job time: ___ minutes (avg of 5 runs)
- Venv creation time: ___ seconds
- pip install time: ___ seconds
- mdxify execution time: ___ seconds
- Post-processing time: ___ seconds

Target after Phase 0:
- Total CI job time: ≤ 70% of baseline
- Cache hit rate: ≥ 80% on subsequent runs
- First-run time: ≤ 110% of baseline
```

---

### Phase 1: Fix GitHub Source Links

**Risk Level**: ✅ **LOW RISK**

#### Strengths
- Robust version-agnostic regex pattern
- Handles both `mellea` and `cli` packages
- Preserves line numbers
- Clear edge case documentation

#### Minor Enhancements

**1. Add version-specific links**:
```python
def fix_source_links(mdx_text: str, version: str | None = None) -> str:
    """Fix source links to point to repo instead of venv.
    
    Args:
        mdx_text: MDX file content
        version: Optional version tag (e.g., "v0.3.0"). If provided,
                links point to tag instead of main branch.
    """
    branch = f"v{version}" if version else "main"
    pattern = (
        r'(https://github\.com/generative-computing/mellea/blob/)main/'
        r'\.venv-docs-autogen/lib/python\d+\.\d+/site-packages/'
        r'((?:mellea|cli)/[^"#]+)'
    )
    result = re.sub(pattern, rf'\1{branch}/\2', mdx_text)
    
    if result != mdx_text:
        count = len(re.findall(pattern, mdx_text))
        print(f"   🔗 Fixed {count} source links")
    return result
```

**2. Add comprehensive validation**:
```python
# Add to validate.py
def validate_source_links(api_dir: Path) -> dict:
    """Validate all source links point to repo, not venv."""
    venv_links = []
    invalid_links = []
    
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text()
        
        # Find venv links (should be 0)
        venv_matches = re.findall(
            r'\[View Source\]\((https://[^)]*\.venv-docs-autogen[^)]*)\)',
            content
        )
        if venv_matches:
            venv_links.extend([
                {'file': str(mdx_file), 'url': url}
                for url in venv_matches
            ])
        
        # Validate repo links are well-formed
        repo_matches = re.findall(
            r'\[View Source\]\((https://github\.com/[^)]+)\)',
            content
        )
        for url in repo_matches:
            if not re.match(
                r'https://github\.com/generative-computing/mellea/blob/[^/]+/'
                r'(mellea|cli)/.+\.py(#L\d+)?$',
                url
            ):
                invalid_links.append({'file': str(mdx_file), 'url': url})
    
    return {
        'venv_links': venv_links,
        'invalid_links': invalid_links,
        'passed': len(venv_links) == 0 and len(invalid_links) == 0
    }
```

**3. Required test cases**:
```python
# test/tooling/docs-autogen/test_source_links.py

def test_fix_source_links_python311():
    """Test with Python 3.11 path."""
    assert fix_source_links(input_text) == expected

def test_fix_source_links_python314():
    """Test with Python 3.14 path."""
    assert fix_source_links(input_text) == expected

def test_fix_source_links_cli_package():
    """Test with cli package."""
    assert fix_source_links(input_text) == expected

def test_fix_source_links_preserves_line_numbers():
    """Ensure #L123 anchors are preserved."""
    assert fix_source_links(input_text) == expected

def test_fix_source_links_with_version():
    """Test version-specific links."""
    assert fix_source_links(input_text, version="0.3.0") == expected
```

---

### Phase 2: Ensure Existing APIs are Documented

**Risk Level**: ⚠️ **MEDIUM RISK**

#### Critical Issue #1: `__all__` fallback logic underspecified

**Problem**: Plan states "treat non-underscore symbols as public" but doesn't handle:
- Imported symbols (e.g., `from typing import List`)
- Re-exports (e.g., `from .internal import PublicClass`)
- Explicitly empty `__all__ = []`
- Dynamically computed `__all__`

**Recommended Specification**:
```python
def get_public_symbols(module_path: Path) -> set[str]:
    """Get public symbols from a module.
    
    Rules:
    1. If __all__ exists and is non-empty: use it
    2. If __all__ = []: module explicitly has no public API
    3. If no __all__: include non-underscore symbols defined in module
       - Exclude imports unless they're re-exports
       - Check if symbol is defined in this module
    """
    import ast
    
    tree = ast.parse(module_path.read_text())
    
    # Find __all__ assignment
    all_value = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        all_value = {
                            elt.s for elt in node.value.elts 
                            if isinstance(elt, ast.Str)
                        }
                    break
    
    if all_value is not None:
        return all_value  # Use explicit __all__
    
    # No __all__ - find defined symbols
    defined = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):
                defined.add(node.name)
    
    return defined
```

#### Critical Issue #2: CLI (Typer) documentation unclear

**Problem**: Typer commands use decorators, not traditional docstrings. `mdxify` may not support Typer introspection.

**Investigation Required**:
```python
# test/tooling/docs-autogen/test_typer_support.py

def test_mdxify_supports_typer():
    """Verify mdxify can document Typer commands."""
    # Create minimal Typer app
    # Run mdxify on it
    # Check if command is documented
    # If not, need custom extraction
```

**Fallback Approach** (if mdxify doesn't support Typer):
```python
def extract_typer_commands(cli_path: Path) -> list[dict]:
    """Extract Typer command documentation."""
    import ast
    
    tree = ast.parse(cli_path.read_text())
    commands = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr') and decorator.func.attr == 'command':
                        commands.append({
                            'name': node.name.replace('_', '-'),
                            'function': node.name,
                            'docstring': ast.get_docstring(node),
                            'params': extract_params(node)
                        })
    
    return commands
```

#### Critical Issue #3: Coverage target "≥99%" is arbitrary

**Recommended Approach**:
```markdown
### Establish Coverage Baseline

1. **Run current tooling**:
   ```bash
   python tooling/docs-autogen/generate-ast.py
   python tooling/docs-autogen/audit_coverage.py > baseline_coverage.json
   ```

2. **Analyze baseline** (example):
   ```json
   {
     "mellea": {
       "total_modules": 45,
       "documented_modules": 42,
       "total_public_symbols": 234,
       "documented_symbols": 198,
       "coverage": 0.846
     }
   }
   ```

3. **Set realistic target**: Baseline + 10%
   - mellea: 84.6% → **95% target**
   - cli: 84.4% → **95% target**

4. **Document exclusions**:
   ```json
   {
     "intentionally_private": ["mellea.helpers._internal"],
     "deprecated": ["mellea.old_api"],
     "experimental": ["mellea.experimental"]
   }
   ```
```

#### Recommended Implementation

**Create coverage audit script**:
```python
# tooling/docs-autogen/audit_coverage.py

def audit_api_coverage(repo_root: Path) -> dict:
    """Audit API documentation coverage."""
    results = {}
    
    for package in ['mellea', 'cli']:
        pkg_path = repo_root / package
        modules = list(pkg_path.rglob("*.py"))
        
        # Find public symbols
        public_symbols = {}
        for module in modules:
            symbols = get_public_symbols(module)
            if symbols:
                public_symbols[str(module)] = symbols
        
        # Find documented symbols
        docs_path = repo_root / "docs" / "docs" / "api" / package
        documented = set()
        if docs_path.exists():
            for mdx_file in docs_path.rglob("*.mdx"):
                content = mdx_file.read_text()
                documented.update(re.findall(r'##\s+`([^`]+)`', content))
        
        # Calculate coverage
        total_public = sum(len(syms) for syms in public_symbols.values())
        documented_count = len(documented)
        
        results[package] = {
            'total_modules': len(modules),
            'total_public_symbols': total_public,
            'documented_symbols': documented_count,
            'coverage': documented_count / total_public if total_public > 0 else 0,
            'missing': [
                {'module': mod, 'symbols': list(syms - documented)}
                for mod, syms in public_symbols.items()
                if syms - documented
            ]
        }
    
    return results
```

---

### Phase 3: Docstring Compliance (Google Style)

**Risk Level**: ✅ **LOW RISK**

#### Strengths
- Leverages existing ruff configuration
- Addresses root cause (malformed docstrings)
- Pre-commit integration prevents regression

#### Recommended Enhancements

**1. Specify exact ruff rules**:
```toml
# Add to pyproject.toml
[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"test/**" = ["D"]  # Don't require docstrings in tests
```

**2. Create auto-fix script**:
```python
# tooling/docs-autogen/fix_docstrings.py

def fix_docstrings(paths: list[Path]) -> None:
    """Fix docstring violations using ruff."""
    for path in paths:
        print(f"Fixing docstrings in {path}...")
        subprocess.run(
            ["uv", "run", "ruff", "check", "--select", "D", "--fix", str(path)],
            check=True
        )
```

**3. Add VS Code snippets**:
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

**4. Document common violations**:
```markdown
### Common Docstring Violations

| Code | Issue | Fix |
|------|-------|-----|
| D205 | Missing blank line | Add blank line before Args: |
| D212 | Summary on wrong line | Move summary to first line |
| D400 | Missing period | Add period to summary |
| D401 | Not imperative mood | Use "Return" not "Returns" |
```

---

### Phase 4: Cross-References

**Risk Level**: 🔴 **HIGH RISK**

#### Critical Issues

**1. `markdown-it-py` approach is complex**

**Problems**:
- Requires AST walking and token manipulation
- Risk of breaking existing MDX components
- No error handling for malformed markdown
- Token reconstruction is fragile

**Recommended Alternative**: Use `griffe` for symbol resolution

```python
from griffe import GriffeLoader

def build_symbol_index(api_dir: Path) -> dict[str, str]:
    """Build symbol → URL mapping using griffe."""
    loader = GriffeLoader()
    
    for pkg in ['mellea', 'cli']:
        loader.load(pkg)
    
    index = {}
    for obj in loader.modules.values():
        for member in obj.members.values():
            # Fully qualified name
            fqn = f"{obj.path}.{member.name}"
            url = f"/api/{obj.path.replace('.', '/')}/#{member.name}"
            index[fqn] = url
            
            # Short name (avoid collisions)
            if member.name not in index:
                index[member.name] = url
    
    return index

def linkify_backticks(md_text: str, symbol_index: dict) -> tuple[str, list[str]]:
    """Transform backticks to links safely."""
    warnings = []
    
    def replace_backtick(match):
        symbol = match.group(1)
        if symbol in symbol_index:
            return f"[`{symbol}`]({symbol_index[symbol]})"
        warnings.append(f"Unknown symbol: {symbol}")
        return match.group(0)
    
    # Only match backticks NOT in code blocks
    result = re.sub(
        r'(?<!`)`([a-zA-Z_][a-zA-Z0-9_.]*)`(?!`)',
        replace_backtick,
        md_text
    )
    
    return result, warnings
```

**2. Missing validation strategy**

**Required**: Add comprehensive link validation

```python
def validate_cross_references(api_dir: Path) -> dict:
    """Validate all cross-reference links."""
    broken_links = []
    total_links = 0
    
    for mdx_file in api_dir.rglob("*.mdx"):
        content = mdx_file.read_text()
        links = re.findall(r'\[`([^`]+)`\]\(([^)]+)\)', content)
        total_links += len(links)
        
        for symbol, url in links:
            # Check if target exists
            target = api_dir / url.lstrip('/')
            if not target.exists():
                broken_links.append({
                    'file': str(mdx_file),
                    'symbol': symbol,
                    'url': url
                })
    
    return {
        'total_links': total_links,
        'broken_links': broken_links,
        'success_rate': 1 - (len(broken_links) / total_links) if total_links > 0 else 1
    }
```

**3. Mintlify anchor algorithm unknown (BLOCKER)**

**Action Required**: Create probe script before Phase 4

```python
# tooling/docs-autogen/probe_mintlify_anchors.py

def probe_anchor_generation():
    """Test Mintlify's anchor generation rules."""
    test_cases = [
        ("ClassName", "?"),
        ("function_name", "?"),
        ("Class.method", "?"),
        ("__init__", "?"),
    ]
    
    # Generate test MDX with known headings
    # Deploy to Mintlify staging
    # Scrape generated anchors
    # Document the pattern
```

**Phase 4 cannot proceed without this information.**

#### Recommended Phasing

```markdown
### Phase 4A: Investigation (Week 4)
1. Probe Mintlify anchor algorithm
2. Test griffe-based symbol resolution
3. Create prototype linkification

### Phase 4B: Implementation (Week 5)
1. Build symbol index
2. Implement safe linkification
3. Add comprehensive validation

### Phase 4C: Validation (Week 5)
1. Test on full codebase
2. Manual QA of cross-references
3. Fix broken links
```

---

### Phase 5: Structural Enhancements

**Risk Level**: ✅ **LOW RISK**

#### Recommendations

**1. Specify preamble format**:
```json
// tooling/docs-autogen/preambles.json
{
  "mellea": {
    "title": "Mellea Core Library",
    "description": "Core abstractions and standard library",
    "sections": [
      {
        "title": "Core",
        "modules": ["core.backend", "core.base", "core.sampling"]
      },
      {
        "title": "Standard Library",
        "modules": ["stdlib.session", "stdlib.components"]
      }
    ]
  }
}
```

**2. Orphaned module discovery**:
```python
def find_orphaned_modules(repo_root: Path) -> list[str]:
    """Find public modules not surfaced via __all__."""
    orphaned = []
    
    for package in ['mellea', 'cli']:
        pkg_path = repo_root / package
        all_modules = set(pkg_path.rglob("*.py"))
        
        # Find modules referenced in __all__ chains
        referenced = find_referenced_modules(pkg_path)
        
        # Find public modules not referenced
        for module in all_modules:
            if module.name.startswith('_'):
                continue
            if module not in referenced:
                orphaned.append(str(module))
    
    return orphaned
```

---

## 2. Strategic Review

### Phase Dependencies

```
Phase 0 (uv) ──┬──> Phase 1 (links)
               │
               ├──> Phase 2 (coverage) ──┐
               │                          ├──> Phase 4 (cross-refs) ──> Phase 5
               └──> Phase 3 (docstrings) ─┘
```

**Parallelization Opportunities**:
- Phases 2-3 can run concurrently after Phase 0-1
- Phase 1 can start immediately after Phase 0

### Effort Estimates

| Phase | Estimated Time | Dependencies |
|-------|---------------|--------------|
| Phase 0 | 2-3 days | None |
| Phase 1 | 1 day | Phase 0 |
| Phase 2 | 2-3 days | Phase 0 |
| Phase 3 | 3-5 days | Phase 0 |
| Phase 4 | 5-7 days | Phases 2, 3 |
| Phase 5 | 1-2 days | Phase 4 |
| **Total** | **14-21 days** | **(2-4 weeks)** |

### Risk Mitigation Matrix

| Phase | Risk | Impact | Mitigation |
|-------|------|--------|------------|
| 0 | CI breaks | High | Parallel pip workflow for 1 release |
| 1 | Wrong links | Medium | validate.py catches 100% |
| 2 | Missing APIs | Low | Coverage report in PR, manual review |
| 3 | Broken docstrings | Medium | Ruff pre-commit prevents new violations |
| 4 | Broken cross-refs | High | Extensive testing, feature flag |
| 5 | Structural issues | Low | Manual review of preambles |

---

## 3. Completeness Review

### Missing Components

#### 1. Testing Strategy

**Required**:
```markdown
## Testing Strategy

### Unit Tests
- `test/tooling/docs-autogen/test_source_links.py`
- `test/tooling/docs-autogen/test_coverage.py`
- `test/tooling/docs-autogen/test_cross_refs.py`

### Integration Tests
- `test/tooling/docs-autogen/test_full_pipeline.py`
  - Runs complete generation locally
  - Validates all outputs
  - Checks for regressions

### Manual QA Checklist
- [ ] Source links point to correct files
- [ ] All public APIs documented
- [ ] Cross-references work
- [ ] Mintlify renders correctly
- [ ] Navigation structure logical
```

#### 2. Rollback Procedures

**Add to each phase**:
```markdown
### Rollback Procedure

If Phase X fails:
1. Revert commits: `git revert <hash>`
2. Restore previous docs: `git checkout v0.3.1 -- docs/docs/api`
3. Redeploy: `mintlify deploy`
4. Document failure in issue tracker
```

#### 3. Monitoring & Metrics

**Required**:
```markdown
## Metrics Dashboard

Track over time:
- API coverage % (per package)
- Cross-ref link success rate
- Doc generation time (per phase)
- User-reported doc issues (GitHub label: `docs-quality`)
- CI job duration

Store in: `docs/metrics/coverage-history.csv`
```

#### 4. Contributor Documentation

**Update Required**:
```markdown
## Documentation Updates (Phase 6)

- [ ] Update CONTRIBUTING.md with `make docs` workflow
- [ ] Add AGENTS.md rules for docstring standards
- [ ] Create docs/DOCS_DEVELOPMENT.md guide
- [ ] Add troubleshooting section to README
```

### Open Questions - Answers

**Q1: Tag → version mapping**
- ✅ Current CI extracts version correctly
- ⚠️ Add handling for pre-release tags (`v0.3.0-rc1`)

**Q2: Mintlify anchor algorithm** 🔴 **CRITICAL BLOCKER**
- ❌ Unknown - must probe before Phase 4
- **Action**: Create `probe_mintlify_anchors.py`

**Q3: Hero symbols**
- ✅ Low priority
- **Recommendation**: Create `hero_symbols.json` with must-link APIs

---

## 4. Recommended Additions

### Phase 6: Validation & Monitoring

```markdown
## Phase 6: Validation & Monitoring

### Actions
1. Generate `.validation-report.json` artifact
2. Add GitHub Action comment with metrics summary
3. Set up doc quality dashboard (GitHub Pages)
4. Create user feedback mechanism

### Acceptance Criteria
- Validation report on every docs PR
- Metrics tracked over time (CSV in repo)
- Broken link count = 0
- Coverage regression alerts configured

### Implementation
```python
# tooling/docs-autogen/validate.py

def generate_validation_report(api_dir: Path) -> dict:
    """Generate comprehensive validation report."""
    return {
        'source_links': validate_source_links(api_dir),
        'api_coverage': validate_api_coverage(api_dir),
        'cross_references': validate_cross_references(api_dir),
        'docstring_compliance': validate_docstrings(api_dir),
        'timestamp': datetime.now().isoformat()
    }
```
```

---

## 5. Success Criteria (Revised)

### Phase-Specific Criteria

**Phase 0**:
- ✅ `make docs` works locally
- ✅ CI uses `--frozen`
- ✅ CI runtime reduced ≥30%
- ✅ Cache hit rate ≥80%

**Phase 1**:
- ✅ 100% source links point to repo
- ✅ 0 links contain `.venv-docs-autogen`
- ✅ Line numbers preserved

**Phase 2**:
- ✅ API coverage ≥95% (adjusted from 99%)
- ✅ Coverage report in CI
- ✅ CLI commands documented

**Phase 3**:
- ✅ Ruff docstring lint passes
- ✅ Dropped sections count = 0
- ✅ Pre-commit hook active

**Phase 4**:
- ✅ Cross-ref linkification rate ≥80%
- ✅ 0 broken cross-ref links
- ✅ Validation passes

**Phase 5**:
- ✅ Module overviews present
- ✅ Orphaned modules documented

**Phase 6**:
- ✅ Validation report generated
- ✅ Metrics dashboard live
- ✅ Contributor docs updated

### Overall Success Criteria

- ✅ All phases have passing tests
- ✅ CI runtime reduced ≥30%
- ✅ API coverage ≥95%
- ✅ Zero broken links
- ✅ Doc generation time <5 minutes
- ✅ Rollback procedure tested and documented

---

## 6. Immediate Action Items

### Before Starting Phase 0

1. **Create baseline metrics**:
   ```bash
   uv run python tooling/docs-autogen/audit_current_state.py
   # Output: baseline_metrics.json
   ```

2. **Set up test infrastructure**:
   ```bash
   mkdir -p test/tooling/docs-autogen
   # Create test fixtures
   ```

3. **Document rollback procedure**:
   - Add to each phase in plan
   - Test rollback locally

4. **Resolve Open Question #2**:
   - Create `probe_mintlify_anchors.py`
   - Document anchor generation rules
   - **BLOCKER for Phase 4**

### Quick Wins (Can Start Immediately)

- [ ] Delete `tooling/docs-autogen/requirements.txt`
- [ ] Add VS Code docstring snippets
- [ ] Run `uv run ruff check --select D` to find violations
- [ ] Create `tooling/docs-autogen/validate.py` skeleton

---

## 7. Final Recommendations

### Critical Path

1. **Week 1**: Address Phase 0 issues, set up testing
2. **Week 2**: Execute Phase 0-1 (foundation)
3. **Week 3**: Execute Phase 2-3 (parallel)
4. **Week 4**: Probe Mintlify, start Phase 4
5. **Week 5**: Complete Phase 4-5
6. **Week 6**: Phase 6 + documentation

### Decision Points

**After Phase 0**:
- Measure actual CI improvement
- Decide: continue or rollback

**After Phase 3**:
- Assess docstring fix effort
- Decide: proceed to Phase 4 or defer

**After Phase 4A (investigation)**:
- If Mintlify anchors can't be determined: defer Phase 4
- If griffe approach fails: consider alternative

### Success Metrics

Track weekly:
- Phases completed
- Tests passing
- Coverage improvement
- CI runtime reduction

---

## Conclusion

The plan is **fundamentally sound** with a pragmatic approach to iterative improvement. The main risks are in Phase 0 (migration) and Phase 4 (cross-references), both of which have clear mitigation strategies.

**Recommendation**: Proceed with execution after addressing:
1. Phase 0 migration strategy (use wheel, not PyPI)
2. Phase 4 validation approach (use griffe, add validation)
3. Missing components (testing, rollback, monitoring)
4. Open Question #2 (Mintlify anchors - BLOCKER)

With these modifications, the plan has a high probability of success and will significantly improve the documentation quality and developer experience.

---

## 8. Updated Plan Review (2026-03-10 Second Pass)

### Summary of Incorporation

The updated `DOCS_IMPROVEMENT_PLAN.md` has successfully incorporated **most** recommendations from the initial review. However, a deeper analysis reveals several areas requiring additional detail or clarification.

### ✅ Successfully Incorporated

1. **Phase structure and dependencies** - Clear diagram with effort estimates
2. **Pre-work baseline measurements** - Specified in dedicated section
3. **Phase 0 wheel-based approach** - Solves chicken-egg problem
4. **Phase 0 rollback procedure** - Emergency fallback included
5. **Phase 1 version-specific links** - Code provided
6. **Phase 2 `__all__` logic** - Three-tier fallback specified
7. **Phase 3 common violations** - D-codes documented
8. **Phase 4 split into 4A/4B/4C** - Investigation phase added
9. **Phase 6 added** - Validation & monitoring
10. **Testing strategy table** - Unit and integration tests
11. **Risk mitigation matrix** - All phases covered
12. **Enhancement prioritization** - P1/P2/P3 tiers

### ⚠️ Areas Needing Additional Detail

#### 1. **Phase 0: Smart CI Triggers - Implementation Missing**

**Issue**: Plan mentions "gate with a check step — only run full generation if docstrings actually changed" but doesn't provide the implementation.

**Current CI** (`.github/workflows/docs-autogen-pr.yml:4-7`):
```yaml
on:
  push:
    tags:
      - "v*"
  workflow_dispatch: {}
```

**Recommended Addition to Plan**:
```yaml
### Phase 0: Smart CI Triggers - Detailed Implementation

Add to `.github/workflows/docs-autogen-pr.yml`:

```yaml
on:
  push:
    tags:
      - "v*"
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
        with:
          fetch-depth: 0
      
      - name: Check if docs generation needed
        id: check
        run: |
          if [[ "${{ github.event_name }}" == "push" ]] && [[ "${{ github.ref }}" =~ ^refs/tags/v ]]; then
            echo "run=true" >> $GITHUB_OUTPUT
            echo "reason=Release tag" >> $GITHUB_OUTPUT
          elif [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "run=true" >> $GITHUB_OUTPUT
            echo "reason=Manual trigger" >> $GITHUB_OUTPUT
          else
            # For PRs: check if docstrings changed
            BASE_SHA="${{ github.event.pull_request.base.sha }}"
            HEAD_SHA="${{ github.sha }}"
            
            # Find Python files with docstring changes
            CHANGED_FILES=$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" | grep -E '^(mellea|cli)/.*\.py$' || true)
            
            if [ -z "$CHANGED_FILES" ]; then
              echo "run=false" >> $GITHUB_OUTPUT
              echo "reason=No Python files changed" >> $GITHUB_OUTPUT
              exit 0
            fi
            
            # Check if any changed files have docstring modifications
            DOCSTRING_CHANGES=0
            for file in $CHANGED_FILES; do
              if git diff "$BASE_SHA" "$HEAD_SHA" -- "$file" | grep -E '^\+.*"""' > /dev/null; then
                DOCSTRING_CHANGES=1
                break
              fi
            done
            
            if [ "$DOCSTRING_CHANGES" -eq 1 ]; then
              echo "run=true" >> $GITHUB_OUTPUT
              echo "reason=Docstring changes detected" >> $GITHUB_OUTPUT
            else
              echo "run=false" >> $GITHUB_OUTPUT
              echo "reason=No docstring changes" >> $GITHUB_OUTPUT
            fi
          fi
      
      - name: Report decision
        run: |
          echo "Should run docs generation: ${{ steps.check.outputs.run }}"
          echo "Reason: ${{ steps.check.outputs.reason }}"

  docs_autogen:
    needs: check_docs_needed
    if: needs.check_docs_needed.outputs.should_run == 'true'
    runs-on: ubuntu-latest
    # ... rest of job
```
```

#### 2. **Phase 0: `build.py` Wrapper - Specification Missing**

**Issue**: Plan mentions creating `tooling/docs-autogen/build.py` but doesn't specify its interface or behavior.

**Current Implementation**: Two separate scripts (`generate-ast.py` + `decorate_api_mdx.py`) run sequentially.

**Recommended Addition to Plan**:
```markdown
### Phase 0: build.py Specification

Create `tooling/docs-autogen/build.py` that chains generation + decoration:

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

import argparse
import subprocess
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Build API documentation")
    parser.add_argument("--pkg-version", help="Package version")
    parser.add_argument("--link-base", help="Base URL for source links")
    parser.add_argument("--docs-json", help="Path to docs.json")
    parser.add_argument("--docs-root", help="Mintlify docs root")
    parser.add_argument("--skip-generation", action="store_true")
    parser.add_argument("--skip-decoration", action="store_true")
    args = parser.parse_args()
    
    repo_root = Path(__file__).resolve().parents[2]
    
    # Step 1: Generation
    if not args.skip_generation:
        print("=" * 60)
        print("STEP 1: Generating API documentation")
        print("=" * 60)
        
        gen_cmd = [
            sys.executable,
            str(repo_root / "tooling/docs-autogen/generate-ast.py")
        ]
        if args.docs_json:
            gen_cmd.extend(["--docs-json", args.docs_json])
        if args.docs_root:
            gen_cmd.extend(["--docs-root", args.docs_root])
        if args.pkg_version:
            gen_cmd.extend(["--pypi-version", args.pkg_version])
        
        result = subprocess.run(gen_cmd, check=False)
        if result.returncode != 0:
            print("❌ Generation failed", file=sys.stderr)
            return result.returncode
    
    # Step 2: Decoration
    if not args.skip_decoration:
        print("\n" + "=" * 60)
        print("STEP 2: Decorating MDX files")
        print("=" * 60)
        
        dec_cmd = [
            sys.executable,
            str(repo_root / "tooling/docs-autogen/decorate_api_mdx.py")
        ]
        if args.docs_root:
            dec_cmd.extend(["--docs-root", args.docs_root])
        
        # Pass version for source link fixing
        if args.pkg_version:
            dec_cmd.extend(["--version", args.pkg_version])
        
        result = subprocess.run(dec_cmd, check=False)
        if result.returncode != 0:
            print("❌ Decoration failed", file=sys.stderr)
            return result.returncode
    
    print("\n" + "=" * 60)
    print("✅ Documentation build complete")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Integration with decorate_api_mdx.py**:
Add `--version` parameter to `decorate_api_mdx.py` to pass through to `fix_source_links()`.
```

#### 3. **Phase 1: Source Link Regex - Edge Case Missing**

**Issue**: Current `decorate_api_mdx.py` doesn't have `fix_source_links()` function yet. Plan provides regex but doesn't address integration.

**Current State** (`decorate_api_mdx.py:269-282`):
```python
def process_mdx_file(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    
    # Step 1: inject SidebarFix
    text = inject_sidebar_fix(original)
    
    # Step 2: decorate headings/dividers
    text = decorate_mdx_body(text)
    
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False
```

**Recommended Addition to Plan**:
```markdown
### Phase 1: Integration Steps

1. **Add `fix_source_links()` to `decorate_api_mdx.py`**:
   ```python
   def fix_source_links(mdx_text: str, version: str | None = None) -> str:
       """Fix source links to point to repo instead of venv.
       
       Args:
           mdx_text: MDX file content
           version: Optional version tag (e.g., "0.3.0"). If provided,
                   links point to tag instead of main branch.
       
       Returns:
           MDX text with fixed source links
       """
       branch = f"v{version}" if version else "main"
       pattern = (
           r'(https://github\.com/generative-computing/mellea/blob/)main/'
           r'\.venv-docs-autogen/lib/python\d+\.\d+/site-packages/'
           r'((?:mellea|cli)/[^"#]+)'
       )
       result = re.sub(pattern, rf'\1{branch}/\2', mdx_text)
       
       if result != mdx_text:
           count = len(re.findall(pattern, mdx_text))
           print(f"   🔗 Fixed {count} source links")
       
       return result
   ```

2. **Update `process_mdx_file()` to include Step 3**:
   ```python
   def process_mdx_file(path: Path, version: str | None = None) -> bool:
       original = path.read_text(encoding="utf-8")
       
       # Step 1: inject SidebarFix
       text = inject_sidebar_fix(original)
       
       # Step 2: decorate headings/dividers
       text = decorate_mdx_body(text)
       
       # Step 3: fix source links
       text = fix_source_links(text, version)
       
       if text != original:
           path.write_text(text, encoding="utf-8")
           return True
       return False
   ```

3. **Update `main()` to accept `--version` parameter**:
   ```python
   def main() -> None:
       parser = argparse.ArgumentParser()
       parser.add_argument("--docs-root", type=Path, default=None)
       parser.add_argument("--api-dir", type=Path, default=None)
       parser.add_argument("--version", type=str, default=None,
                          help="Package version for source links (e.g., 0.3.0)")
       args = parser.parse_args()
       
       # ... existing code ...
       
       for f in mdx_files:
           if process_mdx_file(f, version=args.version):
               changed += 1
   ```
```

#### 4. **Phase 2: Coverage Audit Script - Missing Error Handling**

**Issue**: Plan references `audit_coverage.py` but doesn't specify error handling for edge cases.

**Recommended Addition to Plan**:
```markdown
### Phase 2: audit_coverage.py - Error Handling

Add robust error handling for:

1. **Malformed `__all__`**:
   ```python
   try:
       all_value = ast.literal_eval(node.value)
   except (ValueError, SyntaxError):
       warnings.append(f"Malformed __all__ in {module_path}: {node.value}")
       all_value = None
   ```

2. **Import errors during dynamic `__all__` inspection**:
   ```python
   try:
       spec = importlib.util.spec_from_file_location("module", module_path)
       module = importlib.util.module_from_spec(spec)
       spec.loader.exec_module(module)
       return set(getattr(module, '__all__', []))
   except Exception as e:
       warnings.append(f"Failed to import {module_path}: {e}")
       return set()  # Fall back to AST-based detection
   ```

3. **Circular imports**:
   ```python
   # Use importlib with isolated namespace
   import types
   module_namespace = types.ModuleType("__temp__")
   # Execute in isolated namespace to prevent circular import issues
   ```

4. **Missing MDX files**:
   ```python
   if not docs_path.exists():
       warnings.append(f"Docs directory not found: {docs_path}")
       documented = set()
   ```

**Output format**:
```json
{
  "mellea": {
    "coverage": 0.95,
    "warnings": [
      "Malformed __all__ in mellea/helpers/_internal.py",
      "Failed to import mellea/experimental/new_feature.py: ModuleNotFoundError"
    ],
    "missing": [...]
  }
}
```
```

#### 5. **Phase 3: Pre-commit Hook - Configuration Missing**

**Issue**: Plan mentions "Pre-commit hook to prevent regression" but doesn't specify the configuration.

**Recommended Addition to Plan**:
```markdown
### Phase 3: Pre-commit Hook Configuration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  # ... existing hooks ...
  
  - repo: local
    hooks:
      - id: ruff-docstrings
        name: Check docstring compliance (Google style)
        entry: uv run ruff check --select D
        language: system
        types: [python]
        files: ^(mellea|cli)/.*\.py$
        pass_filenames: true
```

**Alternative**: Use ruff's pre-commit hook directly:
```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--select, D, --fix]
        files: ^(mellea|cli)/.*\.py$
```

**Verification**:
```bash
# Test the hook
pre-commit run ruff-docstrings --all-files

# Should fail on violations, pass after fixes
```
```

#### 6. **Phase 4: Mintlify Anchor Probe - Methodology Missing**

**Issue**: Plan identifies this as a BLOCKER but doesn't specify how to probe Mintlify's anchor algorithm.

**Recommended Addition to Plan**:
```markdown
### Phase 4A: Mintlify Anchor Probe - Detailed Methodology

**Objective**: Determine Mintlify's anchor generation rules for headings.

**Approach**:

1. **Create test MDX file** (`tooling/docs-autogen/test_anchors.mdx`):
   ```markdown
   ---
   title: "Anchor Test"
   ---
   
   ## `ClassName`
   ## `function_name`
   ## `Class.method`
   ## `__init__`
   ## `_private_func`
   ## `CONSTANT_NAME`
   ## `Type[Generic]`
   ```

2. **Deploy to Mintlify staging**:
   ```bash
   # Add to docs.json temporarily
   {
     "navigation": {
       "tabs": [{
         "tab": "Test",
         "pages": ["test_anchors"]
       }]
     }
   }
   
   # Deploy
   mintlify dev  # or deploy to staging environment
   ```

3. **Scrape generated anchors**:
   ```python
   # tooling/docs-autogen/probe_mintlify_anchors.py
   import requests
   from bs4 import BeautifulSoup
   
   def probe_anchors(url: str) -> dict[str, str]:
       """Scrape Mintlify page and extract heading → anchor mappings."""
       response = requests.get(url)
       soup = BeautifulSoup(response.content, 'html.parser')
       
       anchors = {}
       for heading in soup.find_all(['h2', 'h3', 'h4']):
           text = heading.get_text(strip=True)
           anchor_id = heading.get('id')
           if anchor_id:
               anchors[text] = anchor_id
       
       return anchors
   
   if __name__ == '__main__':
       url = "http://localhost:3000/test_anchors"  # or staging URL
       anchors = probe_anchors(url)
       
       print("Mintlify Anchor Generation Rules:")
       print("=" * 60)
       for text, anchor in anchors.items():
           print(f"{text:30} → #{anchor}")
   ```

4. **Document the pattern**:
   ```markdown
   ### Mintlify Anchor Rules (Discovered)
   
   | Heading Text | Generated Anchor | Rule |
   |--------------|------------------|------|
   | `ClassName` | `classname` | Lowercase, remove backticks |
   | `function_name` | `function_name` | Keep underscores |
   | `Class.method` | `classmethod` | Remove dots |
   | `__init__` | `__init__` | Keep double underscores |
   | `_private_func` | `_private_func` | Keep single underscore |
   | `CONSTANT_NAME` | `constant_name` | Lowercase |
   | `Type[Generic]` | `typegeneric` | Remove brackets |
   
   **General Rule**: Lowercase, remove backticks/dots/brackets, keep underscores.
   ```

5. **Implement anchor generator**:
   ```python
   def generate_mintlify_anchor(heading_text: str) -> str:
       """Generate anchor matching Mintlify's algorithm."""
       # Remove backticks
       text = heading_text.strip('`')
       # Remove dots
       text = text.replace('.', '')
       # Remove brackets
       text = re.sub(r'[\[\]]', '', text)
       # Lowercase
       text = text.lower()
       return text
   ```

**Timeline**: 1-2 days for Phase 4A investigation.
```

#### 7. **Phase 6: Validation Report - Schema Missing**

**Issue**: Plan mentions `.validation-report.json` but doesn't specify the schema.

**Recommended Addition to Plan**:
```markdown
### Phase 6: Validation Report Schema

**File**: `docs/docs/api/.validation-report.json`

```json
{
  "timestamp": "2026-03-10T10:00:00Z",
  "version": "0.3.0",
  "summary": {
    "passed": false,
    "total_checks": 4,
    "passed_checks": 3,
    "failed_checks": 1
  },
  "checks": {
    "source_links": {
      "passed": true,
      "total_links": 1234,
      "venv_links": 0,
      "invalid_links": 0,
      "details": []
    },
    "api_coverage": {
      "passed": true,
      "mellea": {
        "coverage": 0.96,
        "target": 0.95,
        "total_public_symbols": 234,
        "documented_symbols": 225,
        "missing": [
          {"module": "mellea.helpers._internal", "symbols": ["helper_func"]}
        ]
      },
      "cli": {
        "coverage": 0.94,
        "target": 0.95,
        "total_public_symbols": 45,
        "documented_symbols": 42,
        "missing": []
      }
    },
    "cross_references": {
      "passed": false,
      "total_links": 567,
      "broken_links": 3,
      "success_rate": 0.995,
      "details": [
        {
          "file": "docs/docs/api/mellea/core/backend.mdx",
          "symbol": "MelleaSession",
          "url": "/api/mellea/stdlib/session/#melleasession",
          "error": "Target file not found"
        }
      ]
    },
    "docstring_compliance": {
      "passed": true,
      "ruff_violations": 0,
      "dropped_sections": 0
    }
  },
  "warnings": [
    "3 cross-reference links are broken",
    "mellea.helpers._internal.helper_func is undocumented"
  ]
}
```

**CI Integration**:
```yaml
- name: Generate validation report
  run: |
    uv run python tooling/docs-autogen/validate.py \
      --api-dir docs/docs/api \
      --output docs/docs/api/.validation-report.json

- name: Check validation
  run: |
    PASSED=$(jq -r '.summary.passed' docs/docs/api/.validation-report.json)
    if [ "$PASSED" != "true" ]; then
      echo "❌ Validation failed"
      jq '.warnings' docs/docs/api/.validation-report.json
      exit 1
    fi

- name: Comment PR with metrics
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const report = JSON.parse(fs.readFileSync('docs/docs/api/.validation-report.json'));
      
      const body = `## 📊 Documentation Validation Report
      
      **Status**: ${report.summary.passed ? '✅ PASSED' : '❌ FAILED'}
      
      ### Metrics
      - **API Coverage**: mellea ${(report.checks.api_coverage.mellea.coverage * 100).toFixed(1)}%, cli ${(report.checks.api_coverage.cli.coverage * 100).toFixed(1)}%
      - **Source Links**: ${report.checks.source_links.total_links} total, ${report.checks.source_links.venv_links} broken
      - **Cross-References**: ${report.checks.cross_references.total_links} total, ${report.checks.cross_references.broken_links} broken
      - **Docstring Compliance**: ${report.checks.docstring_compliance.ruff_violations} violations
      
      ${report.warnings.length > 0 ? '### ⚠️ Warnings\n' + report.warnings.map(w => `- ${w}`).join('\n') : ''}
      `;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.name,
        body: body
      });
```
```

#### 8. **Makefile - Complete Implementation Missing**

**Issue**: Plan mentions `Makefile` with `docs` / `docs-clean` targets but doesn't provide full implementation.

**Recommended Addition to Plan**:
```markdown
### Phase 0: Makefile Implementation

Create `Makefile` in repo root:

```makefile
.PHONY: docs docs-clean docs-validate docs-test help

# Default target
help:
	@echo "Documentation targets:"
	@echo "  make docs          - Generate API documentation"
	@echo "  make docs-clean    - Clean generated documentation"
	@echo "  make docs-validate - Validate generated documentation"
	@echo "  make docs-test     - Run documentation tests"

# Generate documentation
docs:
	@echo "Generating API documentation..."
	uv run python tooling/docs-autogen/build.py \
		--docs-json docs/docs/docs.json \
		--docs-root docs/docs

# Clean generated files
docs-clean:
	@echo "Cleaning generated documentation..."
	rm -rf .venv-docs-autogen
	rm -rf .mdxify-run-cwd
	rm -rf docs/api
	rm -rf docs/docs/api
	@echo "✅ Clean complete"

# Validate documentation
docs-validate: docs
	@echo "Validating documentation..."
	uv run python tooling/docs-autogen/validate.py \
		--api-dir docs/docs/api \
		--output docs/docs/api/.validation-report.json
	@echo "✅ Validation complete"

# Run documentation tests
docs-test:
	@echo "Running documentation tests..."
	uv run pytest test/tooling/docs-autogen/ -v
	@echo "✅ Tests complete"

# Development: generate docs with local changes (no wheel build)
docs-dev:
	@echo "Generating docs from local source..."
	PYTHONPATH=. uv run python tooling/docs-autogen/generate-ast.py \
		--docs-json docs/docs/docs.json \
		--docs-root docs/docs \
		--pypi-name mellea
	uv run python tooling/docs-autogen/decorate_api_mdx.py \
		--docs-root docs/docs
```

**Usage**:
```bash
# Generate docs
make docs

# Clean and regenerate
make docs-clean docs

# Generate and validate
make docs-validate

# Run tests
make docs-test
```
```

### 🔍 Additional Observations

#### 1. **Missing: Dependency Version Specifications**

**Issue**: Plan doesn't specify required versions for new dependencies.

**Recommendation**:
```markdown
### Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
docs = [
    "mdxify>=0.2.0",  # Specify minimum version
    "griffe>=1.0.0",   # For Phase 4 symbol resolution
]
```

Or add to `tooling/docs-autogen/requirements.txt` (if keeping it):
```
mdxify>=0.2.0
griffe>=1.0.0
```
```

#### 2. **Missing: CI Job Timeout**

**Issue**: Current CI has no timeout. Long-running jobs could waste resources.

**Recommendation**:
```yaml
jobs:
  docs_autogen:
    runs-on: ubuntu-latest
    timeout-minutes: 30  # Add timeout
```

#### 3. **Missing: Artifact Retention**

**Issue**: Plan mentions uploading wheel as artifact but doesn't specify retention.

**Recommendation**:
```yaml
- name: Upload wheel artifact
  uses: actions/upload-artifact@v4
  with:
    name: mellea-wheel-${{ steps.ver.outputs.version }}
    path: dist/*.whl
    retention-days: 7  # Keep for 1 week
```

#### 4. **Missing: Local Development Workflow**

**Issue**: Plan focuses on CI but doesn't document local development workflow for contributors.

**Recommendation**:
```markdown
### Local Development Workflow

**For contributors working on documentation tooling**:

1. **Set up environment**:
   ```bash
   uv sync --all-extras
   ```

2. **Generate docs locally**:
   ```bash
   make docs
   ```

3. **Test changes**:
   ```bash
   # Run specific test
   uv run pytest test/tooling/docs-autogen/test_source_links.py -v
   
   # Run all docs tests
   make docs-test
   ```

4. **Validate output**:
   ```bash
   make docs-validate
   ```

5. **Preview in Mintlify**:
   ```bash
   cd docs
   mintlify dev
   # Open http://localhost:3000
   ```

**For contributors updating docstrings**:

1. **Check current violations**:
   ```bash
   uv run ruff check --select D mellea/ cli/
   ```

2. **Auto-fix where possible**:
   ```bash
   uv run ruff check --select D --fix mellea/ cli/
   ```

3. **Verify docs render correctly**:
   ```bash
   make docs
   # Check docs/docs/api/ for your module
   ```
```

### 📋 Summary of Gaps

| Gap | Priority | Phase | Impact |
|-----|----------|-------|--------|
| Smart CI trigger implementation | HIGH | 0 | Could waste CI resources |
| build.py specification | HIGH | 0 | Unclear interface |
| fix_source_links() integration | MEDIUM | 1 | Implementation incomplete |
| audit_coverage.py error handling | MEDIUM | 2 | Could crash on edge cases |
| Pre-commit hook configuration | MEDIUM | 3 | Regression prevention incomplete |
| Mintlify anchor probe methodology | HIGH | 4A | BLOCKER for Phase 4 |
| Validation report schema | MEDIUM | 6 | Unclear output format |
| Makefile complete implementation | LOW | 0 | Developer experience |
| Dependency version specs | LOW | 0 | Reproducibility |
| Local development workflow | LOW | All | Contributor onboarding |

### ✅ Recommended Actions

1. **Immediate** (before Phase 0):
   - Add smart CI trigger implementation to plan
   - Specify build.py interface
   - Add Mintlify anchor probe methodology

2. **Phase 0**:
   - Implement Makefile with all targets
   - Add dependency version specifications
   - Document local development workflow

3. **Phase 1**:
   - Provide complete fix_source_links() integration steps

4. **Phase 2**:
   - Add error handling specification to audit_coverage.py

5. **Phase 3**:
   - Add pre-commit hook configuration

6. **Phase 4A**:
   - Execute Mintlify anchor probe (BLOCKER)

7. **Phase 6**:
   - Define validation report schema
   - Implement CI comment integration

---

**Review Completed**: 2026-03-10 (Second Pass)
**Status**: Plan is 85% complete. Addressing the gaps above will bring it to 100% execution-ready.