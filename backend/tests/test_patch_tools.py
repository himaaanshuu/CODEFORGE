"""Tests for the real unified-diff apply_patch and git-based inspect_diff."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from backend.app.repository.workspace import Workspace
from backend.app.tools.modification_tools import (
    _apply_hunks_to_lines,
    _parse_unified_diff,
    apply_patch,
    inspect_diff,
)

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Original Title</title>
</head>
<body>
    <h1>Hello</h1>
    <p>Body paragraph one.</p>
    <p>Body paragraph two.</p>
    <footer>The end.</footer>
</body>
</html>
"""


@pytest.fixture
def ws(tmp_path: Path) -> Workspace:
    (tmp_path / "index.html").write_text(SAMPLE_HTML, encoding="utf-8")
    return Workspace(root=str(tmp_path))


def test_parse_unified_diff_single_file() -> None:
    patch = (
        "--- a/index.html\n"
        "+++ b/index.html\n"
        "@@ -2,3 +2,3 @@\n"
        " <html>\n"
        " <head>\n"
        "-    <title>Original Title</title>\n"
        "+    <title>New Title</title>\n"
        " </head>\n"
    )
    patches, err = _parse_unified_diff(patch)
    assert err is None
    assert len(patches) == 1
    assert patches[0].new_path == "index.html"
    assert len(patches[0].hunks) == 1
    hunk = patches[0].hunks[0]
    assert hunk.old_start == 2
    assert hunk.new_start == 2
    assert any(l.startswith("+    <title>New") for l in hunk.lines)


def test_parse_multi_file_patch() -> None:
    patch = (
        "--- a/a.txt\n"
        "+++ b/a.txt\n"
        "@@ -1 +1 @@\n"
        "-old a\n"
        "+new a\n"
        "--- a/b.txt\n"
        "+++ b/b.txt\n"
        "@@ -1 +1 @@\n"
        "-old b\n"
        "+new b\n"
    )
    patches, err = _parse_unified_diff(patch)
    assert err is None
    assert len(patches) == 2
    assert {p.new_path for p in patches} == {"a.txt", "b.txt"}


def test_apply_hunks_preserves_rest_of_file(ws: Workspace) -> None:
    """A one-line patch must NOT destroy the rest of the file (old bug)."""
    patch = (
        "--- a/index.html\n"
        "+++ b/index.html\n"
        "@@ -3,3 +3,3 @@\n"
        " <head>\n"
        "-    <title>Original Title</title>\n"
        "+    <title>Forge Test</title>\n"
        " </head>\n"
    )
    result = apply_patch(patch, ws)
    assert result.success, result.error
    content = Path(ws.root, "index.html").read_text(encoding="utf-8")
    # The patched line changed…
    assert "<title>Forge Test</title>" in content
    # …and EVERYTHING ELSE is intact.
    assert "<!DOCTYPE html>" in content
    assert "<footer>The end.</footer>" in content
    assert "<p>Body paragraph two.</p>" in content
    assert content.count("<p>") == 2  # both paragraphs survived


def test_apply_hunks_line_offset_tolerance(ws: Workspace) -> None:
    """Hunk header slightly off (LLM math) still applies via context search."""
    patch = (
        "--- a/index.html\n"
        "+++ b/index.html\n"
        "@@ -30,2 +30,2 @@\n"  # wrong start line; context still matches nearby
        " <h1>Hello</h1>\n"
        "-    <p>Body paragraph one.</p>\n"
        "+    <p>CHANGED paragraph one.</p>\n"
    )
    result = apply_patch(patch, ws)
    assert result.success, result.error
    content = Path(ws.root, "index.html").read_text(encoding="utf-8")
    assert "CHANGED paragraph one." in content
    assert "The end." in content


def test_apply_patch_bad_context_fails_cleanly(ws: Workspace) -> None:
    before = Path(ws.root, "index.html").read_text(encoding="utf-8")
    patch = (
        "--- a/index.html\n"
        "+++ b/index.html\n"
        "@@ -1,2 +1,2 @@\n"
        "-totally different line\n"
        "+replacement\n"
        "-another wrong line\n"
        "+replacement two\n"
    )
    result = apply_patch(patch, ws)
    assert not result.success
    assert "context not found" in (result.error or "").lower()
    # File untouched.
    assert Path(ws.root, "index.html").read_text(encoding="utf-8") == before


def test_apply_patch_new_file(ws: Workspace) -> None:
    patch = (
        "--- /dev/null\n"
        "+++ b/notes.txt\n"
        "@@ -0,0 +1,2 @@\n"
        "+line one\n"
        "+line two\n"
    )
    result = apply_patch(patch, ws)
    assert result.success, result.error
    created = Path(ws.root, "notes.txt").read_text(encoding="utf-8")
    assert created == "line one\nline two\n"
    assert result.data and result.data["files_changed"] == ["notes.txt"]


def test_apply_patch_rejects_traversal(ws: Workspace) -> None:
    patch = (
        "--- a/../evil.txt\n"
        "+++ b/../evil.txt\n"
        "@@ -1 +1 @@\n"
        "-x\n"
        "+y\n"
    )
    result = apply_patch(patch, ws)
    assert not result.success
    assert "outside workspace" in (result.error or "")


def test_apply_hunks_multi_hunk_same_file() -> None:
    original = [f"line {i}" for i in range(1, 21)]
    patch = (
        "--- a/f.txt\n"
        "+++ b/f.txt\n"
        "@@ -2,3 +2,3 @@\n"
        " line 2\n"
        "-line 3\n"
        "+line 3 EDITED\n"
        " line 4\n"
        "@@ -17,3 +17,3 @@\n"
        " line 17\n"
        "-line 18\n"
        "+line 18 EDITED\n"
        " line 19\n"
    )
    patches, err = _parse_unified_diff(patch)
    assert err is None
    updated, err2 = _apply_hunks_to_lines(original, patches[0].hunks)
    assert err2 is None
    assert updated is not None
    assert updated[2] == "line 3 EDITED"
    assert updated[17] == "line 18 EDITED"
    assert updated[9] == "line 10"  # untouched middle
    assert len(updated) == 20


def test_inspect_diff_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"], cwd=tmp_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "t"], cwd=tmp_path, capture_output=True
    )
    f = tmp_path / "file.txt"
    f.write_text("alpha\nbeta\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True
    )
    f.write_text("alpha\nBETA EDITED\n", encoding="utf-8")

    result = inspect_diff(Workspace(root=str(tmp_path)))
    assert result.success
    assert result.data is not None
    assert "file.txt" in result.data["files_changed"]
    assert result.data["insertions"] >= 1
    assert result.data["deletions"] >= 1
    assert "-beta" in result.data["diff"]
    assert "+BETA EDITED" in result.data["diff"]


def test_inspect_diff_clean_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"], cwd=tmp_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "t"], cwd=tmp_path, capture_output=True
    )
    (tmp_path / "a.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True
    )
    result = inspect_diff(Workspace(root=str(tmp_path)))
    assert result.success
    assert result.data is not None
    assert result.data["files_changed"] == []
    assert "clean" in result.data["diff"].lower()


def test_inspect_diff_non_git_honest(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("hi\n", encoding="utf-8")
    result = inspect_diff(Workspace(root=str(tmp_path)))
    assert result.success
    assert result.data is not None
    assert result.data["files_changed"] == []
    assert "not a git repository" in result.data["diff"]


def test_apply_patch_empty() -> None:
    result = apply_patch("", Workspace(root="/tmp"))
    assert not result.success
