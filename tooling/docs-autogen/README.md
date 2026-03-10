# API Documentation Build System

## Overview
Automated system for generating, decorating, and validating Mellea API documentation using Mintlify.

## Quick Start

### Build All Documentation
```bash
make docs-clean  # Remove old docs
make docs        # Generate + decorate
make docs-validate  # Verify quality
make docs-serve  # Start test server at http://localhost:3000
```

### Individual Commands
```bash
# Generate AST and MDX from source
uv run python tooling/docs-autogen/generate-ast.py --docs-root docs/docs --no-venv

# Decorate MDX files (add links, escaping, formatting)
uv run python tooling/docs-autogen/decorate_api_mdx.py --api-dir docs/docs/api --version 0.3.2

# Validate documentation quality
uv run python tooling/docs-autogen/validate.py --api-dir docs/docs/api --version 0.3.2

# Unified build script
uv run python tooling/docs-autogen/build.py --version 0.3.2
```

## Architecture

### Build Pipeline
```
Source Code (mellea/)
    ↓
[1] generate-ast.py → Extract API structure
    ↓
Raw MDX (docs/docs/api/)
    ↓
[2] decorate_api_mdx.py → Add links, formatting, escaping
    ↓
Decorated MDX
    ↓
[3] validate.py → Quality checks
    ↓
Quality Report
    ↓
[4] Mintlify → Live preview
```

### Step 1: AST Generation (`generate-ast.py`)
Extracts API structure from Python source using `mdxify`:
- Parses classes, functions, docstrings
- Generates MDX files with code examples
- Creates navigation structure
- Includes source code links

**Output:** Raw MDX files in `docs/docs/api/`

### Step 2: MDX Decoration (`decorate_api_mdx.py`)
Enhances raw MDX with six processing steps:

1. **Fix GitHub source links** - Update URLs to correct repository/version
2. **Inject preamble** - Add module metadata
3. **Inject SidebarFix** - Add Mintlify sidebar component
4. **Escape MDX syntax** - Escape `{` → `{{` and `}` → `}}` in code blocks
5. **Add cross-references** - Link type mentions to definitions using Griffe
6. **Decorate headings** - Add CLASS/FUNC pills and dividers

**Output:** Fully decorated MDX ready for Mintlify

### Step 3: Validation (`validate.py`)
Verifies documentation quality:

- **Source links** - GitHub URLs point to correct files/lines
- **API coverage** - Percentage of symbols documented (80% threshold)
- **MDX syntax** - No parsing errors
- **Internal links** - Cross-references resolve correctly
- **Anchor collisions** - No duplicate heading IDs

**Output:** Pass/fail report with detailed errors

### Step 4: Preview (`mintlify dev`)
Live preview at http://localhost:3000

```bash
cd docs/docs && npx mintlify dev
```

## File Structure

```
tooling/docs-autogen/
├── README.md                    # This file
├── build.py                     # Unified build script
├── generate-ast.py              # Step 1: AST extraction
├── decorate_api_mdx.py          # Step 2: MDX decoration
├── validate.py                  # Step 3: Quality validation
├── requirements.txt             # Python dependencies
└── test_*.py                    # Unit tests

docs/docs/
├── mint.json                    # Mintlify configuration
├── api/                         # Generated API docs
│   └── mellea/                  # Mirrors source structure
└── snippets/
    └── SidebarFix.mdx          # Mintlify component
```

## Configuration

### Version Management
Set in `Makefile`:
```makefile
DOCS_VERSION ?= 0.3.2
```

Or pass to scripts:
```bash
uv run python tooling/docs-autogen/build.py --version 0.3.2
```

### Coverage Threshold
Edit `validate.py`:
```python
COVERAGE_THRESHOLD = 80.0  # Percentage
```

### Navigation
Edit `docs/docs/mint.json` to control sidebar structure

## Development

### Running Tests
```bash
# All tests
uv run pytest tooling/docs-autogen/

# Specific test file
uv run pytest tooling/docs-autogen/test_escape_mdx.py -v
```

### Adding New Decorations
1. Add function to `decorate_api_mdx.py`
2. Add to `process_mdx_file()` pipeline
3. Write unit tests
4. Update this README

## Known Issues

### 1. Performance
Build takes ~3 minutes for 89 files due to repeated Griffe package loading in `add_cross_references()`. Caching would reduce to ~10 seconds.

### 2. Coverage
Currently 14.46% (target: 80%). Many internal functions lack docstrings.

### 3. Runtime Parsing Errors
4 files show parsing errors in Mintlify despite validation passing:
- `tools.mdx:198` - Blockquote continuation
- `output.mdx:52` - Multiline string
- `metrics.mdx:34` - Dict in example
- `telemetry.mdx:55` - Dict in example

Enhanced escaping logic added, needs testing.

## Troubleshooting

### "File does not exist" warnings
Check `generate-ast.py` output for errors, ensure source file exists

### "Could not parse expression with acorn"
Unescaped curly braces - run `make docs` to regenerate

### "Unexpected lazy line in expression"
Blockquote continuation issue - regenerate docs with enhanced escaping

### Server won't start
Port 3000 in use - Mintlify tries 3001 automatically, or:
```bash
lsof -ti:3000 | xargs kill -9
```

## References

- **Mintlify:** https://mintlify.com/docs
- **MDX:** https://mdxjs.com/
- **Griffe:** https://mkdocstrings.github.io/griffe/

---

**Last Updated:** 2026-03-10  
**Status:** Active development