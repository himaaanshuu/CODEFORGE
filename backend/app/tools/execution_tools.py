from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Sandboxed test execution tool
# Runs repository tests in a controlled, workspace-scoped environment


def _get_python_path() -> str:
    """Get the Python executable to use for running tests.

    Prefers the project venv (Windows Scripts/ and Unix bin/ layouts), then
    falls back to the current interpreter — never a bare "python3" that may
    not exist on Windows.
    """
    here = Path(__file__).resolve()
    candidates = [
        here.parents[3] / "venv" / "Scripts" / "python.exe",  # Windows venv
        here.parents[3] / ".venv" / "Scripts" / "python.exe",
        here.parents[3] / "venv" / "bin" / "python",  # Unix venv
        here.parents[3] / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


FORBIDDEN_COMMANDS = {"rm", "sudo", "curl", "wget", "ssh", "scp", "kill", "killall"}
ALLOWED_TEST_COMMANDS = {"pytest", "python", "python3"}


def run_tests(test_command: str, workspace_root: str) -> Dict[str, Any]:
    """Run tests in a sandboxed environment.

    Validates the command against the execution policy,
    runs the tests inside the workspace, and returns structured results.

    Args:
        test_command: The test command to execute (e.g., "pytest")
        workspace_root: The root directory of the workspace/repo

    Returns:
        Dictionary with test execution results.
    """
    # Parse the command
    cmd_parts = test_command.split()
    cmd_name = cmd_parts[0] if cmd_parts else ""

    # Validate the command against policy
    if cmd_name in FORBIDDEN_COMMANDS:
        return {
            "success": False,
            "error": f"Command '{test_command}' is not allowed by the execution policy.",
            "exit_code": None,
            "duration_ms": 0,
            "timed_out": False,
            "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        }

    # Only allow specific test commands
    if cmd_name not in ALLOWED_TEST_COMMANDS:
        return {
            "success": False,
            "error": f"Test command '{test_command}' is not supported. Allowed: {', '.join(ALLOWED_TEST_COMMANDS)}",
            "exit_code": None,
            "duration_ms": 0,
            "timed_out": False,
            "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        }

    # Determine the Python executable and test command. Extra arguments after
    # the allow-listed command name (e.g. a specific test path) are passed
    # through so the model can target a single test file.
    python_path = _get_python_path()
    extra_args = cmd_parts[1:] if len(cmd_parts) > 1 else []

    actual_cmd = [python_path, "-m", "pytest", "-v", "--tb=short", *extra_args]

    # Set timeout (subprocess timeout — portable, no signal.alarm)
    timeout = 60  # seconds

    # Sanitize environment - only pass through safe variables
    env = os.environ.copy()
    # Remove potentially sensitive variables
    for key in list(env.keys()):
        if any(key.startswith(prefix) for prefix in ("SECRET", "KEY", "TOKEN", "PASSWORD", "API")):
            del env[key]

    # Execute the command
    start_time = time.time()
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code: Optional[int] = None
    max_output = 100_000  # 100KB limit
    max_error = 10_000  # 10KB limit

    try:
        completed = subprocess.run(
            actual_cmd,
            cwd=workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            timeout=timeout,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Python interpreter not found: {python_path}",
            "exit_code": None,
            "duration_ms": int((time.time() - start_time) * 1000),
            "timed_out": False,
            "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Execution error: {str(e)[:200]}",
            "exit_code": None,
            "duration_ms": int((time.time() - start_time) * 1000),
            "timed_out": False,
            "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        }

    duration_ms = int((time.time() - start_time) * 1000)
    stdout_size = min(len(stdout.encode()), max_output)
    stderr_size = min(len(stderr.encode()), max_error)
    if len(stdout.encode()) > max_output:
        stdout = stdout[:max_output] + "\n... [output truncated] ..."
    if len(stderr.encode()) > max_error:
        stderr = stderr[:max_error] + "\n... [error output truncated] ..."

    # Parse each count independently — pytest omits zero counts entirely
    # (e.g. "84 passed, 15 warnings in 0.40s") and ordering varies.
    output_text = stdout + stderr
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Case-sensitive on purpose: verbose per-test lines end in uppercase
    # PASSED/FAILED and can contain digits (e.g. "..._is_401 PASSED"), while
    # the final summary line is lowercase ("84 passed, 15 warnings in ...").
    passed_match = re.search(r"(\d+)\s+passed", output_text)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r"(\d+)\s+failed", output_text)
    if failed_match:
        failed = int(failed_match.group(1))

    skipped_match = re.search(r"(\d+)\s+skipped", output_text)
    if skipped_match:
        skipped = int(skipped_match.group(1))

    # Pattern: "ERROR: N errors" / "N errors"
    error_match = re.search(r"ERROR[:\s]+(\d+)", output_text, re.IGNORECASE)
    if not error_match:
        error_match = re.search(r"(\d+)\s+errors?\b", output_text, re.IGNORECASE)
    if error_match:
        errors = int(error_match.group(1))

    # Determine overall success
    success = not timed_out and exit_code == 0 and failed == 0 and errors == 0

    message_parts: List[str] = []
    if success:
        message_parts.append("All tests passed.")
    else:
        message_parts.append(
            f"Tests {'completed' if not timed_out else 'timed out'}. "
            f"{failed} failed, {errors} error(s)."
        )
    if timed_out:
        message_parts.append("Execution timed out after 60 seconds.")
    if stdout_size > max_output or stderr_size > max_error:
        message_parts.append("Output was truncated due to size limits.")

    return {
        "success": success,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "test_summary": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
        },
        "message": " . ".join(message_parts),
    }


class RunTestsTool:
    """Tool for running repository tests in a sandboxed environment."""

    name = "run_tests"
    description = "Run repository tests in a sandboxed environment with policy validation."

    def __init__(self, workspace_root: str) -> None:
        self.workspace_root = workspace_root

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "test_command": {
                    "type": "string",
                    "description": "The test command to execute (e.g., 'pytest'). Defaults to 'pytest' for Python projects.",
                    "default": "pytest",
                },
            },
            "required": [],
        }

    async def execute(self, test_command: Optional[str] = None) -> Dict[str, Any]:
        """Execute the test command in a sandboxed environment.

        Args:
            test_command: The test command to run. Defaults to "pytest".

        Returns:
            Dictionary with structured test execution results.
        """
        cmd = test_command or "pytest"
        return run_tests(cmd, self.workspace_root)