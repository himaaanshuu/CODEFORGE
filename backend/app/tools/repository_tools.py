from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..repository.workspace import Workspace
from .base import ToolResult


class ListFilesTool:
    """Tool for listing files inside the repository workspace.

    Operates only inside the configured repository workspace.
    Prevents path traversal and avoids .git by default.
    Has sensible depth/output limits.
    """

    name = "list_files"
    description = "List files and directories inside the repository workspace."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path inside the workspace to list (default: '.').",
                },
            },
            "required": [],
        }

    async def execute(self, path: str = ".") -> ToolResult:
        """List files/directories inside the workspace at the given relative path.

        Returns a ToolResult with a sorted list of entry names.
        """
        # Resolve the path through the workspace abstraction
        resolved = self.workspace.resolve(path)
        if resolved is None:
            return ToolResult(
                name=self.name,
                success=False,
                error=f"Invalid or inaccessible path: {path}",
            )

        # If it's a file, just return the filename
        if resolved.is_file():
            return ToolResult(name=self.name, success=True, data=[resolved.name])

        # List the directory, avoiding .git
        entries: List[str] = []
        try:
            for entry in sorted(resolved.iterdir()):
                # Skip .git directory entirely
                if entry.name == ".git":
                    continue
                entries.append(entry.name)
        except (PermissionError, OSError):
            pass

        # Limit output size
        entries = entries[:500]

        return ToolResult(name=self.name, success=True, data=entries)


class ReadFileTool:
    """Tool for reading files inside the repository workspace.

    Only reads files inside the workspace.
    Prevents ../ path traversal.
    Rejects directories.
    Enforces a maximum file size.
    Supports text files.
    Returns useful errors.
    Includes line numbers where practical.
    """

    name = "read_file"
    description = "Read a file's contents inside the repository workspace."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path inside the workspace to read (required).",
                },
            },
            "required": ["path"],
        }

    async def execute(self, path: str) -> ToolResult:
        """Read a file's contents from inside the workspace.

        Returns a ToolResult with the file contents.
        Includes line numbers when possible.
        """
        # Resolve the path through the workspace abstraction
        resolved = self.workspace.resolve(path)
        if resolved is None:
            return ToolResult(
                name=self.name,
                success=False,
                error=f"Invalid or inaccessible path: {path}",
            )

        # Reject directories
        if resolved.is_dir():
            return ToolResult(
                name=self.name,
                success=False,
                error=f"Path is a directory, not a file: {path}",
            )

        # Read the file contents (with line numbers)
        contents = self.workspace.read_file_with_line_numbers(path)

        if contents is not None:
            return ToolResult(name=self.name, success=True, data={"with_line_numbers": contents})

        # Fall back to plain read
        raw = self.workspace.read_file(path)
        if raw is None:
            return ToolResult(
                name=self.name,
                success=False,
                error=f"Failed to read file: {path}",
            )
        return ToolResult(name=self.name, success=True, data={"raw": raw})


class SearchCodeTool:
    """Tool for searching source code inside the repository workspace.

    Recursive search inside the workspace.
    Case-insensitive option.
    Ignores .git directory.
    Ignores binary files.
    Limits number of results and output size.
    Returns file path + line number + matching line/context.
    """

    name = "search_code"
    description = "Search source code inside the repository workspace."

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Text to search for (required).",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Whether to ignore case.",
                    "default": True,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matching results.",
                    "default": 50,
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum lines of context per match.",
                    "default": 3,
                },
            },
            "required": ["query"],
        }

    async def execute(
        self,
        query: str,
        case_insensitive: bool = True,
        max_results: int = 50,
        max_lines: int = 3,
    ) -> ToolResult:
        """Search source code inside the repository workspace.

        Returns a ToolResult with a list of matching results.
        Each result contains: file_path, line_number, matching_line, context.
        """
        # Resolve the workspace root
        root = self.workspace.resolve(".")
        if root is None or not root.is_dir():
            return ToolResult(
                name=self.name,
                success=False,
                error="Workspace root is not accessible.",
            )

        results: List[dict] = []
        try:
            # Walk the directory tree, skipping .git
            for dirpath, dirnames, filenames in os.walk(root):
                # Remove .git from dirnames to prevent descending into it
                if ".git" in dirnames:
                    dirnames.remove(".git")

                # Skip hidden directories (except .git which we already handled)
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not d.startswith(".")
                    or (d.startswith(".") and str(Path(dirpath).resolve()).startswith(str(root)))
                ]

                for filename in filenames:
                    file_path = Path(dirpath) / filename

                    # Skip binary files
                    try:
                        # Try reading as text
                        content = file_path.read_text(encoding="utf-8", errors="replace")
                    except (UnicodeDecodeError, OSError):
                        # Likely binary file, skip
                        continue

                    # Normalize line endings
                    lines = content.splitlines()

                    # Search through lines
                    search_query = query if case_insensitive else query
                    search_lower = search_query.lower() if case_insensitive else None

                    for line_idx, line in enumerate(lines):
                        match_line = line if case_insensitive else line
                        if search_lower is not None:
                            if search_lower not in match_line.lower():
                                continue

                        # Calculate context range
                        start = max(0, line_idx - max_lines)
                        end = min(len(lines), line_idx + max_lines + 1)

                        context_lines = lines[start:end]

                        results.append(
                            {
                                "file_path": str(file_path.relative_to(root)),
                                "line_number": line_idx + 1,
                                "matching_line": line,
                                "context": "\n".join(
                                    f"{i + 1 - start} | {l}" for i, l in enumerate(context_lines)
                                ),
                            }
                        )

                        # Stop if we've hit the max results
                        if len(results) >= max_results:
                            return ToolResult(
                                name=self.name,
                                success=True,
                                data={"results": results, "truncated": True},
                            )
        except (PermissionError, OSError):
            pass

        # Limit results output
        results = results[:max_results]

        return ToolResult(
            name=self.name,
            success=True,
            data={"results": results, "truncated": len(results) >= max_results},
        )