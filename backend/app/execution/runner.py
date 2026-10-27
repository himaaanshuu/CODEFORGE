from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import Optional

from ..execution.models import ExecutionRequest, ExecutionResult
from ..execution.models import ExecutionPolicy
from ..tools.execution_tools import run_tests


class ExecutionRunner:
    """Compatibility adapter that routes allowed test commands to the local runner."""

    def __init__(self, policy: Optional[ExecutionPolicy] = None, workspace_root: Optional[str] = None) -> None:
        self.policy = policy or ExecutionPolicy()
        self.workspace_root = str(Path(workspace_root or os.getcwd()).resolve())

    def _validate_cwd(self, cwd: Optional[str]) -> Optional[str]:
        if cwd is None:
            return self.workspace_root
        abs_cwd = os.path.abspath(cwd)
        workspace_abs = os.path.abspath(self.workspace_root)
        if not abs_cwd.startswith(workspace_abs + os.sep) and abs_cwd != workspace_abs:
            return None
        return abs_cwd if os.path.isdir(abs_cwd) else None

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Run allowlisted pytest on the backend host with a clean environment."""
        if not self.policy.is_command_allowed(request.command):
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr=f"Command '{request.command}' is not allowed by the execution policy.",
                duration_ms=0,
                timed_out=False,
                output_limit_reached=False,
            )

        safe_cwd = self._validate_cwd(request.cwd)
        if safe_cwd is None:
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr="Working directory is not inside the workspace or does not exist.",
                duration_ms=0,
                timed_out=False,
                output_limit_reached=False,
            )
        if safe_cwd != self.workspace_root:
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr="Select test paths relative to the workspace root.",
                duration_ms=0,
                timed_out=False,
                output_limit_reached=False,
            )

        args = request.args or []
        if request.command in {"python", "python3"}:
            if args[:2] == ["-m", "pytest"]:
                args = args[2:]
            elif args:
                return ExecutionResult(
                    success=False,
                    exit_code=None,
                    stdout="",
                    stderr="Only Python's pytest module is allowed by the execution policy.",
                    duration_ms=0,
                    timed_out=False,
                    output_limit_reached=False,
                )
        test_command = shlex.join(["pytest", *args])
        data = run_tests(
            test_command,
            self.workspace_root,
            timeout_seconds=request.timeout or 60,
        )
        message = data.get("message") or data.get("error") or "Test execution failed."
        return ExecutionResult(
            success=bool(data.get("success")),
            exit_code=data.get("exit_code"),
            stdout=str(data.get("stdout") or ""),
            stderr=str(data.get("stderr") or data.get("error") or ""),
            duration_ms=int(data.get("duration_ms") or 0),
            timed_out=bool(data.get("timed_out")),
            output_limit_reached="Output was truncated" in message,
        )
