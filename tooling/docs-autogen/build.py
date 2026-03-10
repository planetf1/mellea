#!/usr/bin/env python3
"""Unified API documentation build script.

Usage:
    python build.py --version 0.5.0
    python build.py --version 0.5.0-rc1 --no-venv
    python build.py --version 0.5.0 --skip-decoration
"""

import argparse
import subprocess
import sys
from pathlib import Path


def normalize_version(version: str) -> str:
    """Strip pre-release suffixes for GitHub source links."""
    return version.split("-")[0]


def main():
    parser = argparse.ArgumentParser(description="Build API documentation")
    parser.add_argument(
        "--version", required=True, help="Package version (e.g., 0.5.0 or 0.5.0-rc1)"
    )
    parser.add_argument(
        "--output-dir", default="docs/docs/api", help="Output directory"
    )
    parser.add_argument(
        "--no-venv",
        action="store_true",
        help="Skip venv creation (pass to generate-ast.py)",
    )
    parser.add_argument(
        "--skip-generation", action="store_true", help="Skip AST generation"
    )
    parser.add_argument(
        "--skip-decoration", action="store_true", help="Skip MDX decoration"
    )
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    output_dir = Path(args.output_dir)
    normalized_version = normalize_version(args.version)

    # Step 1: Generate AST
    if not args.skip_generation:
        cmd = [
            sys.executable,
            str(script_dir / "generate-ast.py"),
            "--output-dir",
            str(output_dir),
        ]
        if args.no_venv:
            cmd.append("--no-venv")

        print(f"[build.py] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(
                f"[build.py] ERROR: generate-ast.py failed with code {result.returncode}",
                file=sys.stderr,
            )
            sys.exit(result.returncode)

    # Step 2: Decorate MDX
    if not args.skip_decoration:
        cmd = [
            sys.executable,
            str(script_dir / "decorate_api_mdx.py"),
            "--input-dir",
            str(output_dir),
            "--version",
            normalized_version,
        ]

        print(f"[build.py] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(
                f"[build.py] ERROR: decorate_api_mdx.py failed with code {result.returncode}",
                file=sys.stderr,
            )
            sys.exit(result.returncode)

    print(
        f"[build.py] ✅ Documentation build complete (version={args.version}, normalized={normalized_version})"
    )


if __name__ == "__main__":
    main()

# Made with Bob
