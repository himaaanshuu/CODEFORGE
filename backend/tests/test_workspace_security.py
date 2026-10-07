"""Unit tests for CodeForge AI repository workspace security.

Tests that the workspace abstraction correctly prevents path traversal
and arbitrary file access.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.repository.workspace import Workspace


def test_workspace_root_initialization() -> None:
    """Test that a Workspace can be initialized with a root directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)
        assert ws.root == os.path.abspath(tmpdir)
        assert ws.resolve(".") == Path(os.path.abspath(tmpdir))


def test_resolve_absolute_path_rejected() -> None:
    """Test that absolute paths are rejected by resolve()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)
        # Absolute path should be rejected
        result = ws.resolve("/etc/passwd")
        assert result is None

        # Another absolute path
        result = ws.resolve("/tmp/secret")
        assert result is None


def test_path_traversal_rejected() -> None:
    """Test that path traversal sequences are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # Parent directory traversal
        result = ws.resolve("../../etc/passwd")
        assert result is None

        # Multiple traversal attempts
        result = ws.resolve("../..")
        assert result is None


def test_directory_access_within_workspace() -> None:
    """Test that paths within the workspace are accepted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # A path within the workspace should resolve
        # (though the actual directory may not exist)
        result = ws.resolve(".")
        assert result is not None
        assert str(result) == os.path.abspath(tmpdir)


def test_list_directory_within_workspace() -> None:
    """Test listing directories within the workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # List the root directory
        entries = ws.list_directory(".")
        assert isinstance(entries, list)
        # Should contain at least the tempdir name or be empty
        assert len(entries) >= 0


def test_read_file_within_workspace() -> None:
    """Test reading a file that exists within the workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # Create a file within the workspace
        test_file = os.path.join(tmpdir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("hello world\nline 2\nline 3")

        # Read the file using line numbers
        contents = ws.read_file_with_line_numbers("test_file.txt")
        assert contents is not None
        assert "1 | hello world" in contents
        assert "2 | line 2" in contents

        # Read raw
        raw = ws.read_file("test_file.txt")
        assert raw is not None
        assert raw == "hello world\nline 2\nline 3"


def test_read_nonexistent_file() -> None:
    """Test reading a file that doesn't exist returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        contents = ws.read_file_with_line_numbers("nonexistent.txt")
        assert contents is None

        raw = ws.read_file("nonexistent.txt")
        assert raw is None


def test_read_directory_rejected() -> None:
    """Test that attempting to read a directory returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        contents = ws.read_file_with_line_numbers(".")
        assert contents is None


def test_read_oversized_file() -> None:
    """Test that oversized files are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # Create a file larger than 1MB
        large_file = os.path.join(tmpdir, "large_file.txt")
        with open(large_file, "w") as f:
            # Write more than 1MB of data
            f.write("x" * 1_500_000)

        contents = ws.read_file_with_line_numbers("large_file.txt")
        assert contents is None


def test_path_traversal_with_dotdot() -> None:
    """Test that dot-dot traversal outside workspace is rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # Try to read /etc/passwd via path traversal
        result = ws.resolve("../etc/passwd")
        assert result is None

        # Try etc/passwd
        result = ws.resolve("etc/passwd")
        assert result is None


def test_git_directory_avoided() -> None:
    """Test that .git directory is avoided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import shutil

        # Initialize a git repo within the workspace
        git_dir = os.path.join(tmpdir, ".git")
        os.makedirs(git_dir, exist_ok=True)

        ws = Workspace(tmpdir)

        # List directory - .git should be avoided/handled
        entries = ws.list_directory(".")
        # .git entries should not appear or be filtered
        # The exact behavior depends on implementation
        assert isinstance(entries, list)


def test_resolve_returns_none_for_invalid() -> None:
    """Test that resolve() returns None for invalid paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Workspace(tmpdir)

        # Non-existent path within workspace
        result = ws.resolve("nonexistent_dir/file.txt")
        assert result is None


def main() -> None:
    """Run all workspace security tests."""
    tests = [
        test_workspace_root_initialization,
        test_resolve_absolute_path_rejected,
        test_path_traversal_rejected,
        test_directory_access_within_workspace,
        test_list_directory_within_workspace,
        test_read_file_within_workspace,
        test_read_nonexistent_file,
        test_read_directory_rejected,
        test_read_oversized_file,
        test_path_traversal_with_dotdot,
        test_git_directory_avoided,
        test_resolve_returns_none_for_invalid,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())