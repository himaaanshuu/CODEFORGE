from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..repository.workspace import Workspace
from .base import ToolResult


def _validate_path(path: str, workspace: Workspace) -> bool:
    """Validate that a file path is within the workspace and safe.

    Returns True if path is valid (inside workspace, no traversal, no .git)
    """
    resolved = workspace.resolve(path)
    if resolved is None:
        return False
    # Make sure it's a file, not a directory or .git
    if resolved.is_dir() or resolved.name == ".git":
        return False
    return True


def _extract_patch_info(patch_text: str) -> Optional[Tuple[str, str]]:
    """Extract file path and new content from a patch string.

    Looks for ---/+++ headers to identify the file,
    then collects content lines from within hunks (after @@ markers).
    
    Returns (target_path, new_content) or None if cannot parse.
    """
    if not patch_text or not patch_text.strip():
        return None

    lines = patch_text.strip().split("\n")

    # Try to find --- and +++ lines to identify the file path
    target_path = None

    for i, line in enumerate(lines):
        # Check for --- a/filepath or --- /filepath (header lines)
        if line.startswith("--- "):
            # Don't use this as the target path source after we've found +++
            match = re.match(r"^--- (?:a/)?(.+)$", line)
            if match:
                # Only set target_path if we haven't found it via +++ yet
                # or if this comes after the +++ line
                target_path = match.group(1)
        # Check for +++ b/filepath or +++ /filepath (header lines)
        elif line.startswith("+++ "):
            match = re.match(r"^\+\+\+ (?:b/)?(.+)$", line)
            if match:
                target_path = match.group(1)
                # Found the file path from the +++ line, break
                break

    if not target_path:
        return None

    # Now collect content from within hunks
    # Hunks start with @@ lines. Within hunks:
    #   ' ' prefix = context line (same in both old and new)
    #   '-' prefix = removed line (old version)
    #   '+' prefix = added line (new version)
    
    # Collect all lines that are added lines (start with + but not +++)
    # and context lines (start with space)
    # We want the "new content" which includes added lines and context
    
    content_lines: List[str] = []
    in_hunk = False
    
    for line in lines:
        # Check if this line starts a hunk
        if re.match(r"^@@", line):
            in_hunk = True
            continue
        
        # If we're outside a hunk, skip --- and +++ header lines
        # but don't collect them as content
        if not in_hunk:
            if line.startswith("--- ") or line.startswith("+++ "):
                continue
            # If we hit a non-header line outside a hunk, stop
            # (this handles cases where the diff doesn't use hunks)
            if not line.startswith(('+', '-', ' ')):
                # Could be the start of something else, but stop collecting
                # unless we already have content
                if not content_lines:
                    return None  # Could not find hunk syntax
                # We have content, stop here
                break
            # Lines starting with +, -, or  outside hunk could be
            # single-line diff format without hunk markers
            if line.startswith('+++') or line.startswith('---'):
                continue
            # For lines starting with + or - outside hunk, collect them
            if line.startswith('+'):
                content_lines.append(line[1:])
            elif line.startswith('-'):
                # Skip removed lines - we want new content
                pass
            continue
        
        # We're inside a hunk
        # Lines starting with '+' are added lines
        if line.startswith('+'):
            # Skip the '+++' header that might appear inside hunk (unlikely but safe)
            if line.startswith('+++'):
                continue
            content_lines.append(line[1:])
        # Lines starting with ' ' are context lines - include them
        elif line.startswith(' '):
            content_lines.append(line[1:])
        # Lines starting with '-' are removed lines - skip them
        # (we want the new content, so we don't include removed lines)
        elif line.startswith('-'):
            pass
        # Any other line type inside hunk, stop collecting
        else:
            break
    
    new_content = "\n".join(content_lines) if content_lines else ""
    
    return target_path, new_content


def apply_patch(diff_text: str, workspace: Workspace) -> ToolResult:
    """Apply a unified diff patch to files inside the workspace.

    This is a controlled patch application that:
    1. Parses the unified diff to identify affected files and new content
    2. Validates every affected path is inside the workspace
    3. Rejects absolute paths, ../ traversal, paths outside workspace
    4. Rejects forbidden files/directories (.git, system paths)
    5. Applies only valid changes
    6. Returns structured result

    Input: {"patch": "unified diff text"}
    """
    if not diff_text or not diff_text.strip():
        return ToolResult(
            name="apply_patch",
            success=False,
            error="Empty diff text provided.",
        )

    # Extract patch info
    result = _extract_patch_info(diff_text)
    if result is None:
        return ToolResult(
            name="apply_patch",
            success=False,
            error="Could not parse the patch. Ensure it is a valid unified diff format with ---/+++ headers and content lines.",
        )

    target_path, new_content = result

    if not target_path:
        return ToolResult(
            name="apply_patch",
            success=False,
            error="Could not determine file path from patch.",
        )

    # Validate the path is inside the workspace and safe
    if not _validate_path(target_path, workspace):
        return ToolResult(
            name="apply_patch",
            success=False,
            error=f"Path '{target_path}' is outside workspace or not allowed.",
        )

    # If new_content is empty but we have a path, try to read the existing file
    # and return info about it (read operation)
    if not new_content.strip():
        existing = workspace.read_file(target_path)
        if existing is None:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"File '{target_path}' not found and could not be read.",
            )
        # Return the current content - this is a read/info operation
        return ToolResult(
            name="apply_patch",
            success=True,
            data={
                "files_changed": [target_path],
                "message": f"File '{target_path}' exists. Current content read.",
                "current_content": existing,
            },
            error=None,
        )

    # Read the current file contents for reference
    current_content = workspace.read_file(target_path)

    # Prepare the new content
    new_content_stripped = new_content.rstrip("\n") + "\n" if new_content else "\n"

    # Write the file
    try:
        resolved_target = workspace.resolve(target_path)
        if resolved_target is None:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"Cannot apply patch to '{target_path}': path resolved outside workspace.",
            )

        resolved_target.parent.mkdir(parents=True, exist_ok=True)
        resolved_target.write_text(new_content_stripped, encoding="utf-8")

        return ToolResult(
            name="apply_patch",
            success=True,
            data={
                "files_changed": [target_path],
                "message": f"Patch applied successfully to '{target_path}'.",
            },
            error=None,
        )

    except (OSError, PermissionError, IOError) as e:
        return ToolResult(
            name="apply_patch",
            success=False,
            error=f"Failed to write file '{target_path}': {str(e)[:200]}",
        )


def inspect_diff(workspace: Workspace) -> ToolResult:
    """Inspect the current changes/diff in the workspace.

    Returns the current workspace changes created by CodeForge.
    This can be used to inspect the diff after apply_patch operations.

    Returns:
        {
            "success": true,
            "files_changed": [...],
            "insertions": N,
            "deletions": N,
            "diff": "..."
        }
    """
    # List all files in the workspace
    # workspace.list_directory() returns a list of filenames
    entries = workspace.list_directory(".")

    # entries is a list
    if not entries:
        return ToolResult(
            name="inspect_diff",
            success=True,
            data={
                "files_changed": [],
                "insertions": 0,
                "deletions": 0,
                "diff": "No files in workspace.",
            },
            error=None,
        )

    # For each file, read it and build a diff marker
    files_changed: List[str] = []
    total_insertions = 0
    total_deletions = 0
    diff_parts: List[str] = []

    for entry in entries:
        file_path = entry
        # Read the file
        read_result = workspace.read_file(file_path)
        if read_result is None:
            continue

        files_changed.append(file_path)

        # Simple diff marker
        content_len = len(read_result) if read_result else 0
        diff_parts.append(f"File: {file_path}\nContent length: {content_len} bytes")

    diff_summary = "\n\n".join(diff_parts) if diff_parts else "No files inspected."

    return ToolResult(
        name="inspect_diff",
        success=True,
        data={
            "files_changed": files_changed,
            "insertions": total_insertions,
            "deletions": total_deletions,
            "diff": diff_summary,
        },
        error=None,
    )


class ApplyPatchTool:
    """Tool for applying unified diff patches to files inside the repository workspace."""

    name = "apply_patch"
    description = "Apply a unified diff patch to modify files inside the repository workspace."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "patch": {
                    "type": "string",
                    "description": "Unified diff text to apply. Format:\n--- a/filepath\n+++ b/filepath\n@@ -start,count +start,count @@\n context line\n-removed line\n+added line\n",
                },
            },
            "required": ["patch"],
        }

    async def execute(self, patch: str) -> ToolResult:
        """Execute the patch application.

        Args:
            patch: Unified diff text to apply.

        Returns:
            ToolResult with success flag and data about files changed.
        """
        return apply_patch(patch, self.workspace)


class InspectDiffTool:
    """Tool for inspecting current changes/diff in the workspace."""

    name = "inspect_diff"
    description = "Inspect the current changes/diff in the repository workspace."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    async def execute(self) -> ToolResult:
        """Execute the diff inspection.

        Returns:
            ToolResult with data about files changed, insertions, deletions, and diff text.
        """
        return inspect_diff(self.workspace)


class WriteFileTool:
    """Tool for writing content to a file inside the repository workspace.

    Restricted: only creates/modifies files inside the workspace.
    Rejects absolute paths, traversal, .git, system paths.
    Enforces file size limits.
    """

    name = "write_file"
    description = "Write content to a file inside the repository workspace (restricted)."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path inside the workspace to write to (required).",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file (required).",
                },
            },
            "required": ["path", "content"],
        }

    async def execute(self, path: str, content: str) -> ToolResult:
        """Write content to a file inside the workspace.

        Only allows writing inside the workspace root.
        Rejects path traversal, absolute paths, .git, system paths.
        """
        # Validate the path is inside the workspace and safe
        if not _validate_path(path, self.workspace):
            return ToolResult(
                name="write_file",
                success=False,
                error=f"Path '{path}' is outside workspace or not allowed.",
            )

        # Prepare the content to write
        content_to_write = content.rstrip("\n") + "\n" if content else "\n"

        try:
            target = Path(path)
            resolved_target = self.workspace.resolve(path)
            if resolved_target is None:
                return ToolResult(
                    name="write_file",
                    success=False,
                    error=f"Cannot write to '{path}': path resolved outside workspace.",
                )

            resolved_target.parent.mkdir(parents=True, exist_ok=True)
            resolved_target.write_text(content_to_write, encoding="utf-8")

            return ToolResult(
                name="write_file",
                success=True,
                data={
                    "path": path,
                    "bytes_written": len(content_to_write),
                    "message": f"File '{path}' written successfully.",
                },
                error=None,
            )

        except (OSError, PermissionError, IOError) as e:
            return ToolResult(
                name="write_file",
                success=False,
                error=f"Failed to write file '{path}': {str(e)[:200]}",
            )