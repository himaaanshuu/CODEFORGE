from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def _validate_new_path(path: str, workspace: Workspace) -> bool:
    """Validate a path for a file that does not exist yet (same rules as
    _validate_path, minus the existence check)."""
    normalized = os.path.normpath(path)
    if os.path.isabs(normalized):
        return False
    root = Path(workspace.root).resolve()
    resolved = (root / normalized).resolve()
    if not str(resolved).startswith(str(root) + os.sep):
        return False
    if resolved.name == ".git" or ".git" in resolved.relative_to(root).parts:
        return False
    return True


@dataclass
class _Hunk:
    """One @@ -a,b +c,d @@ hunk from a unified diff."""

    old_start: int  # 1-based line number in old file
    old_count: int
    new_start: int  # 1-based line number in new file
    new_count: int
    lines: List[str] = field(default_factory=list)  # each line keeps its ' ', '-', '+' prefix


@dataclass
class _FilePatch:
    """One --- a/... +++ b/... section of a unified diff."""

    old_path: str
    new_path: str
    hunks: List[_Hunk] = field(default_factory=list)
    is_new: bool = False
    is_delete: bool = False


def _parse_hunk_header(line: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse '@@ -a,b +c,d @@' (counts optional, defaulting to 1)."""
    m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    if not m:
        return None
    old_start = int(m.group(1))
    old_count = int(m.group(2)) if m.group(2) is not None else 1
    new_start = int(m.group(3))
    new_count = int(m.group(4)) if m.group(4) is not None else 1
    return old_start, old_count, new_start, new_count


def _parse_unified_diff(patch_text: str) -> Tuple[List[_FilePatch], Optional[str]]:
    """Parse a unified diff into per-file patches.

    Returns (patches, error). Patches is empty when nothing could be parsed;
    error is None on success, otherwise a human-readable parse failure.
    """
    if not patch_text or not patch_text.strip():
        return [], "Empty diff text provided."

    lines = patch_text.replace("\r\n", "\n").split("\n")
    patches: List[_FilePatch] = []
    i = 0
    n = len(lines)

    while i < n:
        # Locate a '--- old' header line; the next non-empty line must be '+++ new'.
        if not lines[i].startswith("--- "):
            i += 1
            continue

        old_m = re.match(r"^--- (?:a/)?(.+?)(?:\t.*)?$", lines[i])
        if not old_m:
            i += 1
            continue

        # Find the '+++' header (skip blanks a lazy LLM may have inserted).
        j = i + 1
        while j < n and lines[j].strip() == "":
            j += 1
        if j >= n or not lines[j].startswith("+++ "):
            i += 1
            continue
        new_m = re.match(r"^\+\+\+ (?:b/)?(.+?)(?:\t.*)?$", lines[j])
        if not new_m:
            i += 1
            continue

        old_path = old_m.group(1).strip()
        new_path = new_m.group(1).strip()
        file_patch = _FilePatch(
            old_path=old_path,
            new_path=new_path,
            is_new=old_path in ("/dev/null", "dev/null"),
            is_delete=new_path in ("/dev/null", "dev/null"),
        )

        i = j + 1
        # Consume hunks until the next '--- ' file header or end of text.
        while i < n:
            line = lines[i]
            if line.startswith("--- "):
                break  # next file section
            header = _parse_hunk_header(line)
            if header is None:
                # Skip 'diff --git', 'index', 'Binary files', blank padding, etc.
                if line.startswith("diff --git") or line.strip() == "" or line.startswith("index "):
                    i += 1
                    continue
                # A stray content-looking line outside any hunk: ignore it.
                i += 1
                continue

            old_start, old_count, new_start, new_count = header
            hunk = _Hunk(old_start=old_start, old_count=old_count, new_start=new_start, new_count=new_count)
            i += 1
            # Consume exactly old_count source lines and new_count new lines
            # (standard patch semantics) so trailing blank lines from the
            # text ending in "\n" are not mistaken for context.
            old_seen = 0
            new_seen = 0
            while i < n and (old_seen < old_count or new_seen < new_count):
                hl = lines[i]
                if hl.startswith("\\"):  # '\ No newline at end of file'
                    i += 1
                    continue
                if hl.startswith("+"):
                    hunk.lines.append(hl)
                    new_seen += 1
                elif hl.startswith("-"):
                    hunk.lines.append(hl)
                    old_seen += 1
                elif hl.startswith(" "):
                    hunk.lines.append(hl)
                    old_seen += 1
                    new_seen += 1
                elif hl == "":
                    # Empty line inside a hunk body = context line with empty
                    # content (LLMs drop the leading space); only count it
                    # while the header still expects source lines.
                    if old_seen < old_count and new_seen < new_count:
                        hunk.lines.append(" ")
                        old_seen += 1
                        new_seen += 1
                    else:
                        break
                else:
                    break
                i += 1
            file_patch.hunks.append(hunk)

        if file_patch.hunks:
            patches.append(file_patch)

    if not patches:
        return [], (
            "Could not parse the patch. Provide a unified diff with "
            "'--- a/path' / '+++ b/path' headers and '@@ -a,b +c,d @@' hunks."
        )
    return patches, None


def _apply_hunks_to_lines(
    original: List[str],
    hunks: List[_Hunk],
) -> Tuple[Optional[List[str]], Optional[str]]:
    """Apply hunks to original file lines, preserving everything outside hunks.

    Each hunk is located by matching its leading context/removal lines against
    the current file, anchored on the header's expected line number first and
    then searched outward (the file may already have been shifted by earlier
    hunks in the same patch). Returns (new_lines, error).
    """
    result = list(original)
    for hunk in hunks:
        # Build the expected source block (context + removal lines, in order).
        expected = [l[1:] for l in hunk.lines if l[:1] in (" ", "-")]
        replacement = [l[1:] for l in hunk.lines if l[:1] in (" ", "+")]

        if hunk.old_count == 0 and not expected:
            # Pure insertion anchored at old_start (insert after old_start lines).
            pos = min(hunk.old_start, len(result))
            result = result[:pos] + replacement + result[pos:]
            continue

        if not expected:
            return None, f"Hunk at line {hunk.old_start} has no source context to match against."

        # 1) Try the exact line the header claims.
        start = hunk.old_start - 1  # to 0-based
        candidates = [start]
        # 2) Then a small window around it (tolerate earlier edits / off-by-a-few).
        for delta in range(1, 6):
            candidates.extend([start - delta, start + delta])
        # 3) Finally a full-file scan (LLMs often get the line number badly
        #    wrong; workspace files are small enough for a linear search).
        candidates.extend(range(len(result)))

        applied = False
        for pos in candidates:
            if pos < 0 or pos + len(expected) > len(result):
                continue
            if result[pos : pos + len(expected)] == expected:
                result = result[:pos] + replacement + result[pos + len(expected) :]
                applied = True
                break

        # Whitespace-tolerant pass: LLM patches often drop the file's leading
        # indentation on context lines. Match on stripped content, but keep the
        # ORIGINAL file's context lines (preserving indentation) and only apply
        # the patch's removals/additions.
        if not applied:
            expected_stripped = [e.strip() for e in expected]
            for pos in candidates:
                if pos < 0 or pos + len(expected) > len(result):
                    continue
                window = result[pos : pos + len(expected)]
                if [w.strip() for w in window] != expected_stripped:
                    continue
                rebuilt: List[str] = []
                orig_idx = 0
                for l in hunk.lines:
                    prefix = l[:1]
                    if prefix == " ":
                        rebuilt.append(window[orig_idx])
                        orig_idx += 1
                    elif prefix == "+":
                        rebuilt.append(l[1:])
                    elif prefix == "-":
                        orig_idx += 1
                result = result[:pos] + rebuilt + result[pos + len(expected) :]
                applied = True
                break

        if not applied:
            snippet = expected[0][:60] if expected else ""
            return None, (
                f"Hunk context not found near line {hunk.old_start} "
                f"(first expected line: {snippet!r}). The file may have changed; "
                "re-read it and regenerate the patch."
            )

    return result, None


def apply_patch(diff_text: str, workspace: Workspace) -> ToolResult:
    """Apply a unified diff patch to files inside the workspace.

    Real unified-diff application: each @@ hunk is matched against the current
    file content and only its own region is rewritten — the rest of the file is
    preserved. Supports multi-file patches, new files (/dev/null), and deletions.

    Input: {"patch": "unified diff text"}
    """
    if not diff_text or not diff_text.strip():
        return ToolResult(
            name="apply_patch",
            success=False,
            error="Empty diff text provided.",
        )

    patches, parse_error = _parse_unified_diff(diff_text)
    if parse_error:
        return ToolResult(name="apply_patch", success=False, error=parse_error)

    # Validate all paths up-front; nothing is written if any path is unsafe.
    for fp in patches:
        target = fp.new_path if not fp.is_delete else fp.old_path
        if target in ("/dev/null", "dev/null"):
            continue
        ok = _validate_new_path(target, workspace) if fp.is_new else _validate_path(target, workspace)
        if not ok:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"Path '{target}' is outside workspace or not allowed.",
            )

    files_changed: List[str] = []
    messages: List[str] = []

    for fp in patches:
        target = fp.old_path if fp.is_delete else fp.new_path
        if target in ("/dev/null", "dev/null"):
            target = fp.old_path if fp.old_path not in ("/dev/null", "dev/null") else fp.new_path

        if fp.is_new:
            # New file: assemble content purely from the hunks. Path safety
            # was already validated above; resolve() cannot be used because
            # the file does not exist yet.
            new_lines: List[str] = []
            for hunk in fp.hunks:
                new_lines.extend(l[1:] for l in hunk.lines if l[:1] in (" ", "+"))
            content = "\n".join(new_lines).rstrip("\n") + "\n" if new_lines else ""
            resolved = (Path(workspace.root) / os.path.normpath(target)).resolve()
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.write_text(content, encoding="utf-8")
            files_changed.append(target)
            messages.append(f"Created new file '{target}' ({len(new_lines)} lines).")
            continue

        resolved = workspace.resolve(target)
        if resolved is None:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"Cannot apply patch to '{target}': path resolved outside workspace.",
            )

        existing = workspace.read_file(target)
        if existing is None:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"File '{target}' not found; use write_file (or a --- /dev/null header) to create it.",
            )

        original_lines = existing.split("\n")
        # Preserve the common no-trailing-newline convention: a file that did
        # not end with a blank line after split keeps its final line intact.
        if original_lines and original_lines[-1] == "":
            original_lines = original_lines[:-1]

        updated, err = _apply_hunks_to_lines(original_lines, fp.hunks)
        if err is not None:
            return ToolResult(
                name="apply_patch",
                success=False,
                error=f"Failed to apply patch to '{target}': {err}",
            )

        assert updated is not None
        content = "\n".join(updated) + "\n" if updated else ""
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        files_changed.append(target)
        messages.append(f"Applied {len(fp.hunks)} hunk(s) to '{target}'.")

    if not files_changed:
        return ToolResult(
            name="apply_patch",
            success=False,
            error="Patch contained no applicable file changes.",
        )

    return ToolResult(
        name="apply_patch",
        success=True,
        data={
            "files_changed": files_changed,
            "message": " ".join(messages),
        },
        error=None,
    )


def inspect_diff(workspace: Workspace) -> ToolResult:
    """Inspect real pending changes in the workspace.

    Uses `git diff` / `git status` when the workspace is a git repository
    (cloned repos and the local project both are). For non-git directories the
    tool reports that honestly rather than inventing a diff.
    """
    root = Path(workspace.root)
    git_dir = root / ".git"
    if not git_dir.exists():
        return ToolResult(
            name="inspect_diff",
            success=True,
            data={
                "files_changed": [],
                "insertions": 0,
                "deletions": 0,
                "diff": (
                    "Workspace is not a git repository, so no diff is available. "
                    "Use read_file / write_file / apply_patch results to reason about changes."
                ),
            },
            error=None,
        )

    def _git(*args: str) -> str:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return proc.stdout if proc.returncode == 0 else ""

    # Untracked files count as changes too (but skip ignored/untracked noise).
    status = _git("status", "--short", "--untracked-files=normal")
    diff_text = _git("diff", "--no-color")
    numstat = _git("diff", "--numstat", "--no-color")

    files_changed: List[str] = []
    for line in status.splitlines():
        if len(line) >= 4:
            path = line[3:].strip().strip('"')
            if " -> " in path:  # renames
                path = path.split(" -> ", 1)[1]
            if path and path not in files_changed:
                files_changed.append(path)

    insertions = 0
    deletions = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            try:
                insertions += int(parts[0])
                deletions += int(parts[1])
            except ValueError:
                pass  # binary files report '-'

    # Cap the diff text the model has to read (huge diffs waste context).
    max_chars = 12_000
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars] + f"\n... [diff truncated at {max_chars} characters]"

    if not files_changed and not diff_text:
        diff_text = "No pending changes — the working tree is clean."

    return ToolResult(
        name="inspect_diff",
        success=True,
        data={
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "diff": diff_text or "No textual diff (changes may be untracked/binary).",
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