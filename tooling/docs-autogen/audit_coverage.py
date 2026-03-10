#!/usr/bin/env python3
"""Audit API documentation coverage and docstring quality.

Discovers all public classes and functions in mellea/ and cli/ using Griffe,
then checks which ones have generated MDX documentation. Constants and module
attributes are excluded from the count — they are not expected to have
standalone documentation.

With --quality, also audits docstring quality: flags missing docstrings,
very short docstrings, and functions whose Args/Returns sections are absent.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import griffe
except ImportError:
    print("ERROR: griffe not installed. Run: uv pip install griffe", file=sys.stderr)
    sys.exit(1)


def _load_package(source_dir: Path, package_name: str):
    """Load a package with Griffe. Returns the package object or None on failure."""
    try:
        return griffe.load(source_dir.name, search_paths=[str(source_dir.parent)])
    except Exception as e:
        print(f"WARNING: Failed to load {source_dir}: {e}", file=sys.stderr)
        return None


def discover_public_symbols(
    source_dir: Path, package_name: str
) -> dict[str, list[str]]:
    """Discover all public symbols using Griffe.

    Args:
        source_dir: Root directory to scan (e.g., mellea/ or cli/)
        package_name: Package name to prepend (e.g., "mellea" or "cli")

    Returns:
        Dict mapping full symbol paths to empty lists (for compatibility)
        Example: {"mellea.core.base.Component": [], "mellea.core.base.generative": []}
    """
    symbols: dict[str, list[str]] = {}
    package = _load_package(source_dir, package_name)
    if package is None:
        return symbols

    def walk_module(module, module_path: str):
        """Recursively walk through module and submodules."""
        # Skip internal modules (starting with _)
        if any(part.startswith("_") for part in module_path.split(".")):
            return

        # Get public classes and functions (not starting with _).
        # Constants/attributes are excluded — they are not expected to have
        # standalone documentation and would skew the coverage metric.
        # Aliases (re-exports from other modules) are also excluded — they are
        # documented at their canonical definition, not at each re-export site.
        for name, member in module.members.items():
            if not name.startswith("_"):
                try:
                    if getattr(member, "is_alias", False):
                        continue
                    if member.is_class or member.is_function:
                        full_path = f"{module_path}.{name}"
                        symbols[full_path] = []
                except Exception:
                    # Skip members that can't be resolved (e.g., aliases to stdlib)
                    pass

        # Recursively walk submodules (but skip internal ones)
        if hasattr(module, "modules"):
            for submodule_name, submodule in module.modules.items():
                if not submodule_name.startswith("_"):
                    submodule_path = f"{module_path}.{submodule_name}"
                    walk_module(submodule, submodule_path)

    # Walk through all top-level modules
    for module_name, module in package.modules.items():
        if not module_name.startswith("_"):
            module_path = f"{package_name}.{module_name}"
            walk_module(module, module_path)

    return symbols


# ---------------------------------------------------------------------------
# Docstring quality audit
# ---------------------------------------------------------------------------

_ARGS_RE = re.compile(r"^\s*(Args|Arguments|Parameters)\s*:", re.MULTILINE)
_RETURNS_RE = re.compile(r"^\s*Returns\s*:", re.MULTILINE)
# Return annotations that need no Returns section
_TRIVIAL_RETURNS = {"None", "NoReturn", "Never", "never", ""}


def _check_member(member, full_path: str, short_threshold: int) -> list[dict]:
    """Return quality issues for a single class or function member."""
    issues: list[dict] = []

    doc = getattr(member, "docstring", None)
    doc_text = doc.value.strip() if (doc and doc.value) else ""

    if not doc_text:
        issues.append({"path": full_path, "kind": "missing", "detail": "no docstring"})
        return issues  # no further checks without a docstring

    word_count = len(doc_text.split())
    if word_count < short_threshold:
        preview = doc_text[:70].replace("\n", " ")
        issues.append(
            {
                "path": full_path,
                "kind": "short",
                "detail": f'{word_count} word(s): "{preview}"',
            }
        )

    if getattr(member, "is_function", False):
        # Args section check: only flag when there are meaningful parameters
        params = getattr(member, "parameters", None)
        meaningful = [
            p.name
            for p in (params or [])
            if p.name not in ("self", "cls") and not p.name.startswith("*")
        ]
        if meaningful and not _ARGS_RE.search(doc_text):
            sample = ", ".join(meaningful[:3]) + ("..." if len(meaningful) > 3 else "")
            issues.append(
                {
                    "path": full_path,
                    "kind": "no_args",
                    "detail": f"params [{sample}] have no Args section",
                }
            )

        # Returns section check: only flag when there is an explicit non-trivial annotation
        returns = getattr(member, "returns", None)
        ret_str = str(returns).strip() if returns else ""
        if (
            ret_str
            and ret_str not in _TRIVIAL_RETURNS
            and not _RETURNS_RE.search(doc_text)
        ):
            issues.append(
                {
                    "path": full_path,
                    "kind": "no_returns",
                    "detail": f"return type {ret_str!r} has no Returns section",
                }
            )

    return issues


def audit_docstring_quality(
    source_dir: Path,
    package_name: str,
    short_threshold: int = 5,
    include_methods: bool = True,
) -> list[dict]:
    """Audit docstring quality for all public classes and functions.

    Checks each public symbol for:
    - missing: no docstring at all
    - short: docstring below short_threshold words
    - no_args: function with parameters but no Args/Parameters section
    - no_returns: function with a non-trivial return annotation but no Returns section

    Args:
        source_dir: Root directory to scan (e.g., mellea/ or cli/)
        package_name: Package name (e.g., "mellea" or "cli")
        short_threshold: Word count below which a docstring is flagged as short
        include_methods: Whether to audit public methods on classes in addition
            to top-level functions and classes

    Returns:
        List of issue dicts, each with keys: path, kind, detail
    """
    issues: list[dict] = []
    package = _load_package(source_dir, package_name)
    if package is None:
        return issues

    def walk_module(module, module_path: str) -> None:
        if any(part.startswith("_") for part in module_path.split(".")):
            return

        for name, member in module.members.items():
            if name.startswith("_"):
                continue
            try:
                if getattr(member, "is_alias", False):
                    continue
                if not (member.is_class or member.is_function):
                    continue
            except Exception:
                continue

            full_path = f"{module_path}.{name}"
            issues.extend(_check_member(member, full_path, short_threshold))

            if include_methods and getattr(member, "is_class", False):
                for mname, method in member.members.items():
                    if mname.startswith("_"):
                        continue
                    try:
                        if getattr(method, "is_alias", False):
                            continue
                        if not getattr(method, "is_function", False):
                            continue
                    except Exception:
                        continue
                    issues.extend(
                        _check_member(method, f"{full_path}.{mname}", short_threshold)
                    )

        if hasattr(module, "modules"):
            for submodule_name, submodule in module.modules.items():
                if not submodule_name.startswith("_"):
                    walk_module(submodule, f"{module_path}.{submodule_name}")

    for module_name, module in package.modules.items():
        if not module_name.startswith("_"):
            walk_module(module, f"{package_name}.{module_name}")

    return issues


def _print_quality_report(issues: list[dict]) -> None:
    """Print a grouped quality report to stdout."""
    by_kind: dict[str, list[dict]] = {}
    for issue in issues:
        by_kind.setdefault(issue["kind"], []).append(issue)

    kind_labels = {
        "missing": "Missing docstrings",
        "short": "Short docstrings",
        "no_args": "Missing Args section",
        "no_returns": "Missing Returns section",
    }

    total = len(issues)
    print(f"\n{'=' * 60}")
    print("Docstring Quality Report")
    print(f"{'=' * 60}")
    print(f"Total issues found: {total}")

    for kind in ("missing", "short", "no_args", "no_returns"):
        items = by_kind.get(kind, [])
        if not items:
            continue
        label = kind_labels.get(kind, kind)
        print(f"\n{'─' * 50}")
        print(f"  {label} ({len(items)})")
        print(f"{'─' * 50}")
        for item in sorted(items, key=lambda x: x["path"]):
            print(f"  {item['path']}")
            print(f"    {item['detail']}")


def discover_cli_commands(cli_dir: Path) -> list[str]:
    """Discover CLI commands from Typer applications.

    Args:
        cli_dir: Path to cli/ directory

    Returns:
        List of command names (e.g., ["m serve", "m alora", "m decompose"])
    """
    commands = []

    # Look for Typer app definitions
    # This is a simplified version - full implementation would parse the CLI structure
    main_file = cli_dir / "m.py"
    if main_file.exists():
        content = main_file.read_text()

        # Simple heuristic: look for @app.command() decorators or add_typer() calls

        # Find command decorators
        command_pattern = r'@app\.command\(["\']([^"\']+)["\']\)'
        commands.extend(re.findall(command_pattern, content))

        # Find subcommand additions
        typer_pattern = r'app\.add_typer\([^,]+,\s*name=["\']([^"\']+)["\']\)'
        commands.extend(re.findall(typer_pattern, content))

    return sorted(set(commands))


def find_documented_symbols(docs_dir: Path) -> set[str]:
    """Find which symbols have MDX documentation.

    Args:
        docs_dir: Path to docs/docs/api/ directory

    Returns:
        Set of documented symbol paths (e.g., {"mellea.core.base.Base"})
    """
    documented: set[str] = set()

    if not docs_dir.exists():
        return documented

    # Walk through all .mdx files
    for mdx_file in docs_dir.rglob("*.mdx"):
        # Convert file path to module path
        # e.g., mellea/core/base.mdx -> mellea.core.base
        rel_path = mdx_file.relative_to(docs_dir)
        module_path = str(rel_path.with_suffix("")).replace("/", ".")

        # Read file to find documented symbols
        content = mdx_file.read_text()

        # Look for heading patterns that indicate symbol documentation
        # The actual format is: ### <span>...FUNC</span> `symbol_name`
        # or: ### <span>...CLASS</span> `ClassName`

        # Match both old format and new format
        # Old: ## class Base, ## function generative
        # New: ### <span>...FUNC</span> `blockify`, ### <span>...CLASS</span> `Component`
        old_pattern = r"^##\s+(?:class|function|attribute)\s+(\w+)"
        new_pattern = r"###\s+<span[^>]*>(?:FUNC|CLASS|ATTR)</span>\s+`(\w+)`"

        for match in re.finditer(old_pattern, content, re.MULTILINE):
            symbol_name = match.group(1)
            documented.add(f"{module_path}.{symbol_name}")

        for match in re.finditer(new_pattern, content, re.MULTILINE):
            symbol_name = match.group(1)
            documented.add(f"{module_path}.{symbol_name}")

    return documented


def generate_coverage_report(
    discovered: dict[str, list[str]], documented: set[str], cli_commands: list[str]
) -> dict:
    """Generate coverage report.

    Args:
        discovered: Dict of full symbol paths (keys are "module.symbol", values are empty lists)
        documented: Set of documented symbols (full paths like "module.symbol")
        cli_commands: List of CLI commands

    Returns:
        Coverage report dict with statistics and missing symbols
    """
    # discovered is now a dict where keys are full paths like "mellea.core.base.Component"
    total_symbols = len(discovered)

    # Count how many discovered symbols are documented
    documented_count = len(discovered.keys() & documented)

    # Find missing symbols grouped by module
    missing: dict[str, list[str]] = {}
    for full_path in discovered.keys():
        if full_path not in documented:
            # Extract module and symbol name
            parts = full_path.rsplit(".", 1)
            if len(parts) == 2:
                module_path, symbol_name = parts
                if module_path not in missing:
                    missing[module_path] = []
                missing[module_path].append(symbol_name)

    coverage_pct = (documented_count / total_symbols * 100) if total_symbols > 0 else 0

    return {
        "total_symbols": total_symbols,
        "documented_symbols": documented_count,
        "coverage_percentage": round(coverage_pct, 2),
        "missing_symbols": missing,
        "cli_commands": cli_commands,
        "cli_documented": [],  # TODO: check CLI documentation
    }


def main():
    parser = argparse.ArgumentParser(description="Audit API documentation coverage")
    parser.add_argument("--source-dir", default=".", help="Project root directory")
    parser.add_argument(
        "--docs-dir", default="docs/docs/api", help="Generated docs directory"
    )
    parser.add_argument("--output", help="Output JSON file for report")
    parser.add_argument(
        "--threshold", type=float, default=80.0, help="Minimum coverage threshold"
    )
    parser.add_argument(
        "--quality",
        action="store_true",
        help="Run docstring quality audit (missing, short, no Args/Returns sections)",
    )
    parser.add_argument(
        "--short-threshold",
        type=int,
        default=5,
        metavar="N",
        help="Flag docstrings with fewer than N words as short (default: 5)",
    )
    parser.add_argument(
        "--no-methods",
        action="store_true",
        help="Exclude class methods from quality audit (check top-level symbols only)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    docs_dir = Path(args.docs_dir)

    print("🔍 Discovering public symbols...")
    mellea_symbols = discover_public_symbols(source_dir / "mellea", "mellea")
    cli_symbols = discover_public_symbols(source_dir / "cli", "cli")

    print("🔍 Discovering CLI commands...")
    cli_commands = discover_cli_commands(source_dir / "cli")

    print("📚 Finding documented symbols...")
    documented = find_documented_symbols(docs_dir)

    print("📊 Generating coverage report...")
    all_symbols = {**mellea_symbols, **cli_symbols}
    report = generate_coverage_report(all_symbols, documented, cli_commands)

    # Print coverage report
    print(f"\n{'=' * 60}")
    print("API Documentation Coverage Report")
    print(f"{'=' * 60}")
    print(f"Total classes + functions: {report['total_symbols']}")
    print(f"Documented: {report['documented_symbols']}")
    print(f"Coverage: {report['coverage_percentage']}%")
    print(f"CLI commands: {len(report['cli_commands'])}")

    if report["missing_symbols"]:
        print(
            f"\n⚠️  Missing documentation for {len(report['missing_symbols'])} modules:"
        )
        for module, symbols in sorted(report["missing_symbols"].items()):
            print(f"  {module}: {', '.join(symbols)}")

    # Quality audit
    quality_issues: list[dict] = []
    if args.quality:
        print("\n🔬 Running docstring quality audit...")
        include_methods = not args.no_methods
        for pkg, pkg_name in [("mellea", "mellea"), ("cli", "cli")]:
            pkg_dir = source_dir / pkg
            if pkg_dir.exists():
                quality_issues.extend(
                    audit_docstring_quality(
                        pkg_dir,
                        pkg_name,
                        short_threshold=args.short_threshold,
                        include_methods=include_methods,
                    )
                )
        _print_quality_report(quality_issues)

    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        full_report = {**report}
        if args.quality:
            full_report["quality_issues"] = quality_issues
        output_path.write_text(json.dumps(full_report, indent=2))
        print(f"\n✅ Report saved to {output_path}")

    # Check threshold
    if report["coverage_percentage"] < args.threshold:
        print(
            f"\n❌ Coverage {report['coverage_percentage']}% below threshold {args.threshold}%"
        )
        sys.exit(1)
    else:
        print(f"\n✅ Coverage meets threshold {args.threshold}%")
        sys.exit(0)


if __name__ == "__main__":
    main()

# Made with Bob
