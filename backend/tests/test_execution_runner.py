from __future__ import annotations

from pathlib import Path

from backend.app.tools import execution_tools
from backend.app.execution.models import ExecutionRequest
from backend.app.execution.runner import ExecutionRunner


def test_test_environment_does_not_inherit_secrets(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEBIUS_API_KEY", "secret")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "secret")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")

    env = execution_tools._build_test_environment(str(tmp_path))

    assert "NEBIUS_API_KEY" not in env
    assert "SUPABASE_SERVICE_ROLE_KEY" not in env
    assert "GITHUB_TOKEN" not in env
    assert env["HOME"] == str(tmp_path)
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_inline_python_is_rejected_before_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        execution_tools.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("process started")),
    )

    result = execution_tools.run_tests("python -c 'print(1)'", str(tmp_path))

    assert not result["success"]
    assert "Only Python's pytest module" in result["error"]


def test_legacy_runner_delegates_to_local_test_runner(
    tmp_path: Path, monkeypatch
) -> None:
    called: dict[str, object] = {}

    def fake_run_tests(command: str, workspace: str, timeout_seconds: int):
        called.update(command=command, workspace=workspace, timeout=timeout_seconds)
        return {
            "success": True,
            "exit_code": 0,
            "duration_ms": 10,
            "timed_out": False,
            "stdout": "1 passed",
            "stderr": "",
            "message": "All tests passed.",
        }

    monkeypatch.setattr("backend.app.execution.runner.run_tests", fake_run_tests)
    runner = ExecutionRunner(workspace_root=str(tmp_path))
    result = runner.execute(
        ExecutionRequest(
            command="python",
            args=["-m", "pytest", "tests/test_sample.py"],
            timeout=25,
        )
    )

    assert result.success
    assert called == {
        "command": "pytest tests/test_sample.py",
        "workspace": str(tmp_path.resolve()),
        "timeout": 25,
    }
