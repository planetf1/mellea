.PHONY: docs docs-clean docs-validate docs-test docs-dev docs-orphans

# Get version from pyproject.toml
VERSION := $(shell uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

docs:
	@echo "Building API docs (version=$(VERSION))..."
	@uv run python tooling/docs-autogen/build.py --version $(VERSION)

docs-clean:
	@echo "Cleaning generated API docs..."
	@rm -rf docs/docs/api/*.mdx
	@rm -rf .venv-docs-autogen

docs-validate:
	@echo "Validating API docs (version=$(VERSION))..."
	@uv run python tooling/docs-autogen/validate.py docs/docs/api --version $(VERSION) --coverage-threshold 80

docs-test:
	@echo "Running docs tooling tests..."
	@uv run pytest tooling/docs-autogen/test/

docs-dev:
	@echo "Building API docs from local source (no wheel)..."
	@uv run python tooling/docs-autogen/build.py --version $(VERSION)-dev

docs-orphans:
	@echo "Finding orphaned API documentation..."
	@uv run python tooling/docs-autogen/find_orphans.py