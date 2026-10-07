from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class Workspace:
    """Repository workspace abstraction with path safety.

    Ensures the agent can never read arbitrary files from the user's Mac.
    All paths are resolved relative to an explicit workspace root, and paths
    outside the root are rejected.
    """

    def __init__(self, root: str) -> None:
        self.root = os.path.abspath(root)
        self._root_path = Path(self.root)

    def resolve(self, path: str) -> Optional[Path]:
        """Resolve a path relative to the workspace root.

        Returns None if the resolved path is outside the workspace root,
        if the path involves traversal outside the root, or if the path
        does not exist within the workspace.
        """
        # Normalize the input path
        normalized = os.path.normpath(path)

        # Reject absolute paths
        if os.path.isabs(normalized):
            return None

        # Reject paths that go above the root (path traversal)
        # Join the root with the normalized path and check it's still under root
        resolved = self._root_path / normalized
        resolved_str = str(resolved.resolve())
        root_str = str(self._root_path.resolve())

        if not resolved_str.startswith(root_str + os.sep) and resolved_str != root_str:
            return None

        # Check the path exists within the workspace
        if not resolved.exists():
            return None

        # Check it's not a symlink pointing outside (basic protection)
        try:
            resolved.resolve(strict=False)
        except Exception:
            return None

        return resolved

    def list_directory(self, path: str = ".") -> list[str]:
        """List files/directories inside the workspace at the given relative path.

        Returns a sorted list of names (files and directories).
        Prevents .git directory listing and limits output depth/size.
        """
        resolved = self.resolve(path)
        if resolved is None:
            return []

        # Avoid .git directory
        if resolved.name == ".git":
            return []

        try:
            entries = []
            for entry in sorted(resolved.iterdir()):
                # Skip .git entries at any level
                if entry.name == ".git":
                    continue
                entries.append(entry.name)
            # Limit output to prevent large responses
            return entries[:500]
        except (PermissionError, OSError):
            return []

    def file_exists(self, path: str) -> bool:
        """Check if a file exists within the workspace."""
        resolved = self.resolve(path)
        if resolved is None:
            return False
        return resolved.is_file()

    def directory_exists(self, path: str) -> bool:
        """Check if a directory exists within the workspace."""
        resolved = self.resolve(path)
        if resolved is None:
            return False
        return resolved.is_dir()

    def read_file(self, path: str) -> Optional[str]:
        """Read a file's contents from within the workspace.

        Returns the file contents as a string, or None if the path is invalid.
        Enforces maximum file size.
        """
        resolved = self.resolve(path)
        if resolved is None:
            return None

        # Reject directories
        if resolved.is_dir():
            return None

        # Enforce maximum file size (1MB default)
        max_size = 1_000_000  # 1MB
        try:
            file_size = resolved.stat().st_size
        except OSError:
            return None

        if file_size > max_size:
            return None

        if not resolved.is_file():
            return None

        try:
            return resolved.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError):
            return None

    def read_file_with_line_numbers(self, path: str, max_lines: int = 1000) -> Optional[str]:
        """Read a file's contents with line numbers.

        Returns formatted string like:
            1 | from fastapi import ...
            2 |
            3 | def login(...):
        """
        resolved = self.resolve(path)
        if resolved is None:
            return None

        # Reject directories
        if resolved.is_dir():
            return None

        # Enforce maximum file size
        max_size = 1_000_000
        try:
            file_size = resolved.stat().st_size
        except OSError:
            return None

        if file_size > max_size:
            return None

        if not resolved.is_file():
            return None

        try:
            lines = resolved.read_text(encoding="utf-8").splitlines()
            # Limit lines shown
            lines = lines[:max_lines]
            formatted = []
            for i, line in enumerate(lines, 1):
                formatted.append(f"{i} | {line}")
            return "\n".join(formatted)
        except (UnicodeDecodeError, PermissionError, OSError):
            return None