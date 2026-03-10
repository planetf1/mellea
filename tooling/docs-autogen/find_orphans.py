#!/usr/bin/env python3
"""Find orphaned modules not linked in navigation.

Scans generated MDX files and checks which ones aren't referenced
in the Mintlify navigation configuration.
"""

import argparse
import json
from pathlib import Path


def find_mdx_files(docs_dir: Path) -> set[str]:
    """Find all generated MDX files.

    Args:
        docs_dir: Directory containing MDX files (e.g., docs/docs/api)

    Returns:
        Set of module paths (e.g., {"mellea/core/base", "cli/m"})
    """
    mdx_files = set()

    for mdx_file in docs_dir.rglob("*.mdx"):
        # Get path relative to docs_dir
        rel_path = mdx_file.relative_to(docs_dir)
        # Remove .mdx extension
        module_path = str(rel_path.with_suffix(""))
        mdx_files.add(module_path)

    return mdx_files


def find_navigation_refs(mint_json: Path) -> set[str]:
    """Find all API references in mint.json navigation.

    Args:
        mint_json: Path to mint.json file

    Returns:
        Set of referenced paths (e.g., {"api/mellea/core/base"})
    """
    if not mint_json.exists():
        return set()

    refs = set()
    config = json.loads(mint_json.read_text())

    def extract_refs(obj):
        """Recursively extract page references."""
        if isinstance(obj, dict):
            if "page" in obj:
                page = obj["page"]
                if page.startswith("api/"):
                    refs.add(page[4:])  # Remove "api/" prefix
            for value in obj.values():
                extract_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_refs(item)

    extract_refs(config)
    return refs


def main():
    parser = argparse.ArgumentParser(description="Find orphaned API documentation")
    parser.add_argument(
        "--docs-dir",
        default="docs/docs/api",
        help="Directory containing generated MDX files",
    )
    parser.add_argument(
        "--mint-json",
        default="docs/mint.json",
        help="Path to mint.json navigation config",
    )
    parser.add_argument("--output", help="Output JSON file with orphans list")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    mint_json = Path(args.mint_json)

    print("🔍 Finding orphaned modules...")
    print(f"   Docs directory: {docs_dir}")
    print(f"   Navigation config: {mint_json}")
    print()

    # Find all MDX files
    mdx_files = find_mdx_files(docs_dir)
    print(f"Found {len(mdx_files)} MDX files")

    # Find navigation references
    nav_refs = find_navigation_refs(mint_json)
    print(f"Found {len(nav_refs)} navigation references")

    # Find orphans (MDX files not in navigation)
    orphans = mdx_files - nav_refs

    print(f"\n{'=' * 60}")
    print(f"Orphaned Modules: {len(orphans)}")
    print(f"{'=' * 60}")

    if orphans:
        print("\nModules not linked in navigation:")
        for orphan in sorted(orphans):
            print(f"  • {orphan}")

        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(
                    {
                        "total_mdx_files": len(mdx_files),
                        "navigation_refs": len(nav_refs),
                        "orphan_count": len(orphans),
                        "orphans": sorted(orphans),
                    },
                    indent=2,
                )
            )
            print(f"\n📄 Report saved to {output_path}")
    else:
        print("\n✅ No orphaned modules found!")

    return 0 if len(orphans) == 0 else 1


if __name__ == "__main__":
    exit(main())

# Made with Bob
