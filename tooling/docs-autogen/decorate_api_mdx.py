#!/usr/bin/env python3
"""decorate_api_mdx_merged.py

Merges the two behaviors you were running back-to-back:

1) decorate_api_mdx.py behavior:
   - Adds CLASS/FUNC pills to headings
   - Inserts divider lines
   - Skips <br />

2) v3 behavior:
   - Injects SidebarFix import + render so Mintlify sidebar badges/icons work:
       import { SidebarFix } from "/snippets/SidebarFix.mdx";
       <SidebarFix />

3) GitHub source link fixing:
   - Corrects GitHub URLs to point to ibm-granite/mellea repository
   - Uses version tags instead of branch names

Usage examples:

# (Recommended) Point at the Mintlify docs root (the folder that contains api/ and snippets/)
python3 decorate_api_mdx_merged.py --docs-root /path/to/docs/docs --version 0.5.0

# Or point directly at api directory
python3 decorate_api_mdx_merged.py --api-dir /path/to/docs/docs/api --version 0.5.0
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

# =========================
# SidebarFix injection
# =========================

FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.S)

# Canonical Mintlify docs-root absolute import (this is what worked for you)
SIDEBAR_IMPORT_LINE = 'import { SidebarFix } from "/snippets/SidebarFix.mdx";'
SIDEBAR_RENDER_LINE = "<SidebarFix />"

IMPORT_RE = re.compile(
    r'(?m)^\s*import\s+\{\s*SidebarFix\s*\}\s+from\s+["\']\/snippets\/SidebarFix\.mdx["\']\s*;?\s*$'
)
RENDER_RE = re.compile(
    r"(?m)^\s*<\s*SidebarFix\s*\/\s*>\s*$|^\s*<\s*SidebarFix\s*>\s*<\/\s*SidebarFix\s*>\s*$"
)

SIDEBAR_BLOCK = SIDEBAR_IMPORT_LINE + "\n\n" + SIDEBAR_RENDER_LINE + "\n\n"


def inject_sidebar_fix(mdx_text: str) -> str:
    """Insert SidebarFix import + render right after frontmatter (or at top if none)."""
    has_import = bool(IMPORT_RE.search(mdx_text))
    has_render = bool(RENDER_RE.search(mdx_text))
    if has_import and has_render:
        return mdx_text

    # Normalize: remove any partial remnants and add canonical block
    mdx_text = IMPORT_RE.sub("", mdx_text)
    mdx_text = RENDER_RE.sub("", mdx_text)

    m = FRONTMATTER_RE.match(mdx_text)
    if m:
        insert_at = m.end()
        return (
            mdx_text[:insert_at]
            + "\n"
            + SIDEBAR_BLOCK
            + mdx_text[insert_at:].lstrip("\n")
        )

    return SIDEBAR_BLOCK + mdx_text.lstrip("\n")


# =========================
# GitHub source link fixing
# =========================


def fix_source_links(content: str, version: str) -> str:
    """Fix GitHub source links to point to correct repository and version.

    Args:
        content: MDX file content
        version: Package version (e.g., "0.5.0")

    Returns:
        Content with corrected GitHub links

    Example:
        Input:  [View source](https://github.com/pypa/pip/blob/main/src/pip/_internal/cli/base_command.py#L123)
        Output: [View source](https://github.com/ibm-granite/mellea/blob/v0.5.0/src/pip/_internal/cli/base_command.py#L123)
    """
    # Pattern: [View source](https://github.com/OWNER/REPO/blob/BRANCH/PATH#LINE)
    pattern = r"\[View source\]\(https://github\.com/[^/]+/[^/]+/blob/[^/]+/([^)]+)\)"

    def replace_link(match):
        path = match.group(1)
        # Extract just the file path and line number
        # path might be like "src/pip/_internal/cli/base_command.py#L123"
        # We need to map this to the actual mellea path

        # For mellea, the source is in mellea/ or cli/ directories
        # The mdxify tool should have preserved the correct path
        # We just need to fix the repository URL

        return f"[View source](https://github.com/ibm-granite/mellea/blob/v{version}/{path})"

    return re.sub(pattern, replace_link, content)


# =========================
# MDX escaping
# =========================


def escape_mdx_syntax(content: str) -> str:
    """Escape MDX-sensitive characters in code blocks.

    MDX interprets curly braces as JSX expressions, which breaks
    Python dict literals and JSON. This function escapes them.
    
    Also fixes blockquote continuations in tracebacks.

    Args:
        content: MDX file content

    Returns:
        Content with escaped MDX syntax in code blocks
    """
    lines = content.splitlines(keepends=True)
    result = []
    in_code_block = False
    in_blockquote = False
    code_fence_pattern = re.compile(r"^```")
    blockquote_pattern = re.compile(r"^>>>?\s")

    for line in lines:
        # Track code block boundaries
        if code_fence_pattern.match(line):
            in_code_block = not in_code_block
            in_blockquote = False  # Reset blockquote when entering/exiting code
            result.append(line)
            continue

        # Escape curly braces inside code blocks
        if in_code_block:
            # Check if this is a blockquote line (>>> or Traceback)
            if blockquote_pattern.match(line) or line.strip().startswith("Traceback"):
                in_blockquote = True
                # Escape braces in blockquote lines too
                escaped = line.replace("{", "{{").replace("}", "}}")
                result.append(escaped)
            elif in_blockquote and line.strip() and not line.startswith(">>>"):
                # Continuation of blockquote - prefix with >
                escaped = line.replace("{", "{{").replace("}", "}}")
                result.append("> " + escaped)
            else:
                # Reset blockquote if we hit an empty line or new prompt
                if not line.strip() or line.startswith(">>>"):
                    in_blockquote = False
                # Simple approach: just escape all { and }
                # This is safe because mdxify generates fresh content without escapes
                escaped = line.replace("{", "{{").replace("}", "}}")
                result.append(escaped)
        else:
            result.append(line)

    return "".join(result)


# =========================
# Preamble injection
# =========================


def inject_preamble(content: str, module_path: str) -> str:
    """Inject preamble text after frontmatter.

    Args:
        content: MDX file content
        module_path: Module path (e.g., "mellea.core.base")

    Returns:
        Content with preamble injected
    """
    # Define preambles for key modules
    preambles = {
        "mellea.core": (
            "The `mellea.core` module provides the foundational abstractions for building "
            "LLM-powered applications. It includes the base classes for backends, formatters, "
            "and the `@generative` decorator for creating LLM-powered functions.\n\n"
        ),
        "mellea.backends": (
            "The `mellea.backends` module provides integrations with various LLM providers. "
            "Each backend implements the `Backend` interface and handles provider-specific "
            "authentication, API calls, and response formatting.\n\n"
        ),
        "mellea.formatters": (
            "The `mellea.formatters` module provides output formatters that parse and validate "
            "LLM responses into structured Python types. Formatters handle JSON parsing, "
            "type validation, and error recovery.\n\n"
        ),
        "mellea.stdlib": (
            "The `mellea.stdlib` module provides high-level components for common LLM patterns. "
            "It includes sessions for conversation management, context handling, and reusable "
            "components for building complex workflows.\n\n"
        ),
        "cli": (
            "The `cli` module provides command-line tools for working with Mellea. "
            "It includes commands for serving models, generating documentation, and "
            "running evaluations.\n\n"
        ),
    }

    # Find matching preamble (exact match or parent module)
    preamble_text = None
    for key, text in preambles.items():
        if module_path == key or module_path.startswith(key + "."):
            preamble_text = text
            break

    if not preamble_text:
        return content

    # Find end of frontmatter
    if not content.startswith("---\n"):
        return content

    frontmatter_end = content.find("\n---\n", 4)
    if frontmatter_end == -1:
        return content

    # Inject preamble after frontmatter
    before = content[: frontmatter_end + 5]  # Include closing ---\n
    after = content[frontmatter_end + 5 :]

    return f"{before}\n{preamble_text}{after}"


# =========================
# Heading decoration (pills/dividers)
# =========================

CLASS_SPAN = (
    '<span className="ml-2 inline-flex items-center rounded-full '
    "px-2 py-1 text-[0.7rem] font-bold tracking-wide "
    'bg-[#4ADE8033]/20 text-[#15803D]">CLASS</span>'
)

FUNC_SPAN = (
    '<span className="ml-2 inline-flex items-center rounded-full '
    "px-2 py-1 text-[0.7rem] font-bold tracking-wide "
    'bg-[#3064E3]/20 text-[#1D4ED8]">FUNC</span>'
)

SPAN_RE = re.compile(r'\s*<span className="[^"]*rounded-full[^"]*">.*?</span>\s*')
LABEL_RE = re.compile(r"^\[(class|func|Class|funct)\]\s+")
# DIVIDER_LINE = '---'
DIVIDER_LINE = '<div className="w-full h-px bg-gray-200 dark:bg-gray-700 my-4" />'
SPACER_BLOCK = '<div className="h-8" />'


def pick_kind(name: str, level: int, current_section: str | None) -> str | None:
    if level >= 4:
        return "func"
    if level == 3:
        if current_section == "functions":
            return "func"
        if current_section == "classes":
            return "class"
        return "class" if name and name[0].isupper() else "func"
    return None


def label_heading(line: str, current_section: str | None) -> str:
    head_match = re.match(r"^(#{2,6})\s+(.*)$", line)
    if not head_match:
        return line

    hashes = head_match.group(1)
    body = LABEL_RE.sub("", head_match.group(2)).strip()
    body = SPAN_RE.sub(" ", body).strip()

    # Only decorate headings that look like: ## `Something`
    m = re.match(r"^`([^`]+)`(.*)$", body)
    if not m:
        return line

    name = m.group(1)
    rest = m.group(2).rstrip()
    level = len(hashes)

    kind = pick_kind(name, level, current_section)
    if not kind:
        return f"{hashes} `{name}`{rest}"

    span = CLASS_SPAN if kind == "class" else FUNC_SPAN

    if rest:
        return f"{hashes} {span} `{name}`{rest}"
    return f"{hashes} {span} `{name}`"


def line_has_pill(line: str) -> bool:
    return line.strip().startswith("#") and (
        "bg-[#3064E3]/20" in line or "bg-[#4ADE8033]/20" in line
    )


def last_non_empty_is_divider(lines: list[str]) -> bool:
    for line in reversed(lines):
        if line.strip() != "":
            return line.strip() == DIVIDER_LINE
    return False


def decorate_mdx_body(full_text: str) -> str:
    """Applies the pill/divider logic with tight HR placement, WITHOUT triggering
    Setext headings.
    """
    lines = full_text.splitlines()
    out: list[str] = []

    current_section: str | None = None  # None | "classes" | "functions"
    in_item: bool = False  # inside a class/function block?

    # Detect an "item heading" inside a section (class/function entry)
    item_heading_re = re.compile(r"^(#{3,6})\s+.*`[^`]+`")

    def last_non_empty_is_divider_local() -> bool:
        for ln in reversed(out):
            if ln.strip() != "":
                return ln.strip() == DIVIDER_LINE
        return False

    def append_divider():
        # Ensure previous line is blank to prevent Setext headings.
        if out and out[-1].strip() != "":
            out.append("")
        if not last_non_empty_is_divider_local():
            out.append(DIVIDER_LINE)
        out.append("")

    def close_item_if_open():
        nonlocal in_item
        if in_item:
            append_divider()
            in_item = False

    for line in lines:
        stripped = line.strip()

        # Skip <br />
        if stripped == "<br />":
            continue

        # --- NEW LOGIC START ---
        # Inject spacer before "**Methods:**"
        if stripped == "**Methods:**":
            out.append("")  # Ensure we are on a new line
            out.append(SPACER_BLOCK)  # Insert the height div
            out.append(line)
            continue
        # --- NEW LOGIC END ---

        # Section headers
        if stripped == "## Classes":
            close_item_if_open()
            current_section = "classes"
            out.append(line)
            append_divider()
            continue

        if stripped == "## Functions":
            close_item_if_open()
            current_section = "functions"
            out.append(line)
            append_divider()
            continue

        # Any other H2 header exits the section
        if stripped.startswith("## ") and stripped not in (
            "## Classes",
            "## Functions",
        ):
            close_item_if_open()
            current_section = None
            in_item = False
            out.append(line)
            continue

        # Decorate headings (but do not add HR here)
        labeled = label_heading(line, current_section)
        stripped_labeled = labeled.strip()

        # Within Classes/Functions: a new item heading closes the prior item
        if current_section in ("classes", "functions") and item_heading_re.match(
            stripped_labeled
        ):
            close_item_if_open()
            in_item = True
            out.append(labeled)
            continue

        out.append(labeled)

    close_item_if_open()

    while out and out[-1].strip() == "":
        out.pop()

    return "\n".join(out) + "\n"


# =========================
# Cross-reference functions
# =========================


def extract_type_references(content: str) -> set[str]:
    """Extract type references from docstrings and signatures.

    Looks for:
    - Type annotations: Backend, Optional[Backend], List[str]
    - Docstring references: See `Backend` for details
    - Return types: Returns Backend instance

    Args:
        content: MDX file content

    Returns:
        Set of type names referenced (e.g., {"Backend", "Session"})
    """
    refs = set()

    # Pattern 1: Type annotations in code blocks
    # Example: def foo(backend: Backend) -> Session:
    type_pattern = r":\s*([A-Z][a-zA-Z0-9_]*)"
    refs.update(re.findall(type_pattern, content))

    # Pattern 2: Backtick references in text
    # Example: See `Backend` for details
    backtick_pattern = r"`([A-Z][a-zA-Z0-9_]*)`"
    refs.update(re.findall(backtick_pattern, content))

    # Pattern 3: Generic types
    # Example: Optional[Backend], List[Session]
    generic_pattern = r"\[([A-Z][a-zA-Z0-9_]*)\]"
    refs.update(re.findall(generic_pattern, content))

    return refs


def resolve_symbol_path(symbol_name: str, source_dir: Path) -> str | None:
    """Resolve symbol name to module path using Griffe.

    Args:
        symbol_name: Symbol to resolve (e.g., "Backend")
        source_dir: Project source directory

    Returns:
        Module path if found (e.g., "mellea.core.backend"), None otherwise
    """
    try:
        import griffe
    except ImportError:
        return None

    # Load mellea package
    try:
        package = griffe.load("mellea", search_paths=[str(source_dir.parent)])
    except Exception:
        return None

    # Search for symbol in all modules
    for module_path, module in package.modules.items():
        if symbol_name in module.members:
            # Use the canonical path which points to the actual definition
            member = module.members[symbol_name]
            canonical = member.canonical_path
            # canonical is like "mellea.core.base.Component"
            # We want "mellea.core.base" (the module path)
            parts = canonical.split(".")
            if len(parts) > 1:
                return ".".join(parts[:-1])  # Remove the symbol name
            return f"mellea.{module_path}"

    return None


def add_cross_references(content: str, module_path: str, source_dir: Path) -> str:
    """Add cross-reference links to type mentions.

    Args:
        content: MDX file content
        module_path: Current module path (e.g., "mellea.core.base")
        source_dir: Project source directory

    Returns:
        Content with cross-reference links added
    """
    # Import mintlify_anchor from test file
    import sys

    test_anchors_path = Path(__file__).parent / "test_mintlify_anchors.py"
    if test_anchors_path.exists():
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "test_mintlify_anchors", test_anchors_path
        )
        if spec and spec.loader:
            test_anchors = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_anchors)
            mintlify_anchor = test_anchors.mintlify_anchor
        else:
            # Fallback if import fails
            def mintlify_anchor(heading: str) -> str:
                anchor = heading.lower().replace(" ", "-")
                anchor = re.sub(r"[^a-z0-9-]", "", anchor)
                anchor = re.sub(r"-+", "-", anchor)
                return anchor.strip("-")
    else:
        # Fallback if file doesn't exist
        def mintlify_anchor(heading: str) -> str:
            anchor = heading.lower().replace(" ", "-")
            anchor = re.sub(r"[^a-z0-9-]", "", anchor)
            anchor = re.sub(r"-+", "-", anchor)
            return anchor.strip("-")

    # Extract type references
    refs = extract_type_references(content)

    # Resolve each reference to a module path
    resolved = {}
    for ref in refs:
        target_module = resolve_symbol_path(ref, source_dir)
        if target_module and target_module != module_path:
            # Convert module path to relative MDX path
            # e.g., mellea.core.backend -> ../core/backend
            resolved[ref] = target_module

    # Replace backtick references with links
    # Example: `Backend` -> [`Backend`](../core/backend#class-backend)
    def replace_ref(match):
        symbol = match.group(1)
        if symbol in resolved:
            target_module = resolved[symbol]
            # Calculate relative path
            # module_path is like "mellea.core.formatter" (the current file)
            # target_module is like "mellea.core.base" (the target file)
            current_parts = module_path.split(".")
            target_parts = target_module.split(".")

            # Find common prefix
            common = 0
            for i in range(min(len(current_parts), len(target_parts))):
                if current_parts[i] == target_parts[i]:
                    common += 1
                else:
                    break

            # Build relative path
            # We need to go up from the current file's directory, not from the file itself
            # current_parts[-1] is the file name, so we exclude it
            up_levels = (
                len(current_parts) - common - 1
            )  # -1 because we're in a file, not a dir

            # If we're in the same directory (e.g., both in mellea.core), up_levels will be 0
            # and we just need the target file name
            if up_levels == 0:
                rel_path = target_parts[-1]  # Just the filename in same directory
            else:
                rel_path = "../" * up_levels + "/".join(target_parts[common:])

            # Generate anchor
            anchor = mintlify_anchor(f"class {symbol}")

            return f"[`{symbol}`]({rel_path}#{anchor})"
        return match.group(0)

    # First, fix existing markdown links that may have wrong paths
    # Pattern: [`Symbol`](path#anchor)
    def fix_existing_link(match):
        symbol = match.group(1)
        # old_path = match.group(2)  # Not needed, we recalculate
        anchor = match.group(3)

        if symbol in resolved:
            target_module = resolved[symbol]
            current_parts = module_path.split(".")
            target_parts = target_module.split(".")

            # Find common prefix
            common = 0
            for i in range(min(len(current_parts), len(target_parts))):
                if current_parts[i] == target_parts[i]:
                    common += 1
                else:
                    break

            # Build relative path
            up_levels = len(current_parts) - common - 1

            if up_levels == 0:
                rel_path = target_parts[-1]
            else:
                rel_path = "../" * up_levels + "/".join(target_parts[common:])

            # Keep the existing anchor
            return f"[`{symbol}`]({rel_path}#{anchor})"
        return match.group(0)

    # Fix existing links first
    existing_link_pattern = r"\[`([A-Z][a-zA-Z0-9_]*)`\]\(([^)#]+)#([^)]+)\)"
    content = re.sub(existing_link_pattern, fix_existing_link, content)

    # Then add links to plain backtick references
    pattern = r"`([A-Z][a-zA-Z0-9_]*)`"
    content = re.sub(pattern, replace_ref, content)

    return content


# =========================
# Path resolution + processing
# =========================


def resolve_api_dir(docs_root: Path | None, api_dir: Path | None) -> Path:
    if api_dir is not None:
        return api_dir
    if docs_root is not None:
        return docs_root / "api"

    cwd = Path.cwd()
    candidates = [cwd / "docs" / "api", cwd / "docs" / "docs" / "api"]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def process_mdx_file(
    path: Path,
    version: str,
    api_dir: Path | None = None,
    source_dir: Path | None = None,
) -> bool:
    """Process a single MDX file.

    Args:
        path: Path to MDX file
        version: Package version for GitHub links
        api_dir: API directory (for extracting module path)
        source_dir: Project source directory (for cross-reference resolution)

    Returns:
        True if file was modified, False otherwise
    """
    original = path.read_text(encoding="utf-8")

    # Extract module path from filepath
    # e.g., docs/docs/api/mellea/core/base.mdx -> mellea.core.base
    if api_dir:
        try:
            rel_path = path.relative_to(api_dir)
            module_path = str(rel_path.with_suffix("")).replace("/", ".")
        except ValueError:
            # If path is not relative to api_dir, use filename
            module_path = path.stem
    else:
        module_path = path.stem

    # Step 1: Fix GitHub source links
    text = fix_source_links(original, version)

    # Step 2: Inject preamble
    text = inject_preamble(text, module_path)

    # Step 3: inject SidebarFix
    text = inject_sidebar_fix(text)

    # Step 4: Escape MDX syntax in code blocks
    text = escape_mdx_syntax(text)

    # Step 5: Add cross-references (if source_dir provided)
    if source_dir:
        text = add_cross_references(text, module_path, source_dir)

    # Step 6: decorate headings/dividers
    text = decorate_mdx_body(text)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Decorate API MDX files")
    parser.add_argument(
        "--docs-root", type=Path, default=None, help="Mintlify docs root directory"
    )
    parser.add_argument(
        "--api-dir", type=Path, default=None, help="API directory containing MDX files"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Package version for GitHub links (e.g., 0.5.0)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Project source directory for cross-reference resolution",
    )
    args = parser.parse_args()

    api_dir = resolve_api_dir(args.docs_root, args.api_dir)
    if not api_dir.exists():
        raise SystemExit(
            f"❌ API directory not found: {api_dir}\n"
            "Try:\n"
            "  python3 decorate_api_mdx_merged.py --docs-root /path/to/docs/docs --version 0.5.0\n"
            "or\n"
            "  python3 decorate_api_mdx_merged.py --api-dir /path/to/docs/docs/api --version 0.5.0\n"
        )

    # Resolve source directory (default to mellea/ in current directory)
    source_dir = args.source_dir
    if source_dir is None:
        source_dir = Path.cwd() / "mellea"
        if not source_dir.exists():
            source_dir = None  # Disable cross-references if source not found

    mdx_files = list(api_dir.rglob("*.mdx"))
    if not mdx_files:
        print(f"⚠️ No .mdx files found under: {api_dir}")
        return

    changed = 0
    for f in mdx_files:
        if process_mdx_file(f, args.version, api_dir, source_dir):
            changed += 1

    print(
        f"✅ Done. Processed {len(mdx_files)} MDX files under {api_dir}. Updated {changed}."
    )


if __name__ == "__main__":
    main()
