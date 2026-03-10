#!/usr/bin/env python3
"""Audit API documentation coverage.

Discovers all public symbols in mellea/ and cli/ using Griffe,
then checks which ones have generated MDX documentation.
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


def discover_public_symbols(source_dir: Path) -> dict[str, list[str]]:
    """Discover all public symbols using Griffe.

    Args:
        source_dir: Root directory to scan (e.g., mellea/ or cli/)

    Returns:
        Dict mapping module paths to lists of public symbol names
        Example: {"mellea.core.base": ["Base", "Backend", "generative"]}
    """
    symbols: dict[str, list[str]] = {}

    # Load the package using Griffe
    try:
        package = griffe.load(source_dir.name, search_paths=[str(source_dir.parent)])
    except Exception as e:
        print(f"WARNING: Failed to load {source_dir}: {e}", file=sys.stderr)
        return symbols

    # Walk through all modules
    for module_path, module in package.modules.items():
        public_members = []

        # Get public members (not starting with _)
        for name, member in module.members.items():
            if not name.startswith("_"):
                # Include classes, functions, and important attributes
                try:
                    if member.is_class or member.is_function or member.is_attribute:
                        public_members.append(name)
                except Exception:
                    # Skip members that can't be resolved (e.g., aliases to stdlib)
                    pass

        if public_members:
            symbols[module_path] = sorted(public_members)

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
        # e.g., "## class Base", "## function generative"
        import re

        symbol_pattern = r"^##\s+(?:class|function|attribute)\s+(\w+)"
        for match in re.finditer(symbol_pattern, content, re.MULTILINE):
            symbol_name = match.group(1)
            documented.add(f"{module_path}.{symbol_name}")

    return documented


def generate_coverage_report(
    discovered: dict[str, list[str]], documented: set[str], cli_commands: list[str]
) -> dict:
    """Generate coverage report.

    Args:
        discovered: All discovered public symbols
        documented: Set of documented symbols
        cli_commands: List of CLI commands

    Returns:
        Coverage report dict with statistics and missing symbols
    """
    total_symbols = sum(len(symbols) for symbols in discovered.values())
    documented_count = len(documented)

    missing = {}
    for module_path, symbols in discovered.items():
        missing_in_module = []
        for symbol in symbols:
            full_path = f"{module_path}.{symbol}"
            if full_path not in documented:
                missing_in_module.append(symbol)

        if missing_in_module:
            missing[module_path] = missing_in_module

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
    mellea_symbols = discover_public_symbols(source_dir / "mellea")
    cli_symbols = discover_public_symbols(source_dir / "cli")

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
    print(f"Total symbols: {report['total_symbols']}")
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
