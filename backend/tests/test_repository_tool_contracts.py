from __future__ import annotations

from pathlib import Path

from backend.app.repository.workspace import Workspace
from backend.app.tools.modification_tools import _validate_new_path, apply_patch
from backend.app.tools.repository_tools import _format_file_lines, ReadFileTool


def test_read_file_supports_line_offset_and_limit() -> None:
    assert _format_file_lines("one\ntwo\nthree\nfour\n", offset=1, limit=2) == (
        "2 | two\n3 | three"
    )


def test_root_level_new_file_is_allowed(tmp_path: Path) -> None:
    workspace = Workspace(str(tmp_path))

    assert _validate_new_path("package.json", workspace)
    result = apply_patch(
        "--- /dev/null\n"
        "+++ b/package.json\n"
        "@@ -0,0 +1,3 @@\n"
        "+{\n"
        '+  "name": "codeforge"\n'
        "+}\n",
        workspace,
    )
    assert result.success, result.error
    assert (tmp_path / "package.json").exists()
    assert "offset" in ReadFileTool(workspace).input_schema["properties"]
