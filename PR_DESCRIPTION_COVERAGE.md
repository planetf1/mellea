# Add Code Coverage Tracking

## Summary
Adds pytest-cov for code coverage tracking to improve test quality visibility.

## Changes
- Added `pytest-cov>=6.0.0` to dev dependencies
- Configured coverage for `mellea` and `cli` packages in `pyproject.toml`
- Added `.coveragerc` for HTML report configuration
- Excluded test files and scratchpad from coverage reports

## Usage
```bash
# Run tests with coverage (default behavior with new config)
uv run pytest test -v

# Generate HTML report
uv run pytest test --cov-report=html
open htmlcov/index.html

# Run specific tests with coverage
uv run pytest test/stdlib -v --cov=mellea --cov=cli
```

## Next Steps
Once baseline coverage metrics are established:
- Add coverage reporting to CI workflows
- Set minimum coverage thresholds
- Consider adding coverage badges to README

## Testing
- [x] `uv sync --group dev` installs pytest-cov successfully
- [x] Coverage reports generate correctly
- [x] Pre-commit hooks pass

---

**Type:** feat  
**Priority:** Medium  
**Effort:** Low (~30 min)