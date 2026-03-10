#!/usr/bin/env python3
"""Audit API documentation coverage.

Discovers all public classes and functions in mellea/ and cli/ using Griffe,
then checks which ones have generated MDX documentation. Constants and module
attributes are excluded from the count — they are not expected to have
standalone documentation.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import griffe
except ImportError:
    print("ERROR: griffe not installed. Run: uv pip install griffe", file=sys.stderr)
    sys.exit(1)


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

    # Load the package using Griffe
    try:
        package = griffe.load(source_dir.name, search_paths=[str(source_dir.parent)])
    except Exception as e:
        print(f"WARNING: Failed to load {source_dir}: {e}", file=sys.stderr)
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
        import re

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
        import re

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

    # Print report
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

    # Save report if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2))
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
