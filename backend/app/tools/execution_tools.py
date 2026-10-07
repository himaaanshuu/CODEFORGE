from __future__ import annotations

import os
import re
import subprocess
import signal
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Sandboxed test execution tool
# Runs repository tests in a controlled, workspace-scoped environment


def _get_python_path() -> str:
    """Get the path to the Python executable to use for running tests."""
    # Use the Python executable from the environment
    # When running within the CodeForge AI venv, this will use the venv's Python
    # When running elsewhere, fall back to python3
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", "..", ".venv", "bin", "python")
    if os.path.exists(venv_path):
        return venv_path
    # Fall back to python3
    return "python3"


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

    # Determine the Python executable and test command
    python_path = _get_python_path()

    # Build the actual command to run based on the command name
    if cmd_name == "pytest":
        # Use python -m pytest with the workspace root as rootdir
        actual_cmd = [python_path, "-m", "pytest"]
        actual_cmd_args = ["-v", "--tb=short"]
        # Add the workspace root as the directory to search for tests
        # pytest will discover tests in the rootdir
    elif cmd_name in ("python", "python3"):
        # Run pytest discovery
        actual_cmd = [python_path, "-m", "pytest"]
        actual_cmd_args = ["-v", "--tb=short"]
    else:
        # Default to pytest
        actual_cmd = [python_path, "-m", "pytest"]
        actual_cmd_args = ["-v", "--tb=short"]

    # Set timeout
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

    def timeout_handler(signum, frame):
        nonlocal timed_out
        timed_out = True
        raise TimeoutError("Execution timed out")

    # Set timeout alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        # Run the test command in the workspace directory
        process = subprocess.Popen(
            actual_cmd + actual_cmd_args,
            cwd=workspace_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
        )

        # Read output with size limits
        stdout_chunks = []
        stderr_chunks = []
        stdout_size = 0
        stderr_size = 0
        max_output = 100_000  # 100KB limit
        max_error = 10_000  # 10KB limit

        try:
            # Read stdout
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                if stdout_size + len(line.encode()) > max_output:
                    stdout_chunks.append("... [output truncated] ...")
                    stdout_size = max_output
                    break
                stdout_size += len(line.encode())
                stdout_chunks.append(line)

            # Read stderr
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                if stderr_size + len(line.encode()) > max_error:
                    stderr_chunks.append("... [error output truncated] ...")
                    stderr_size = max_error
                    break
                stderr_size += len(line.encode())
                stderr_chunks.append(line)

        except TimeoutError:
            timed_out = True
            process.terminate()
            try:
                process.wait(timeout=5)
            except Exception:
                process.kill()
                process.wait()

        finally:
            signal.alarm(0)  # Cancel the alarm
            signal.signal(signal.SIGALRM, old_handler)

        # Get the exit code
        exit_code: Optional[int] = None
        try:
            exit_code = process.wait(timeout=5)
        except Exception:
            exit_code = None

        duration_ms = int((time.time() - start_time) * 1000)

    except Exception as e:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return {
            "success": False,
            "error": f"Execution error: {str(e)[:200]}",
            "exit_code": None,
            "duration_ms": int((time.time() - start_time) * 1000),
            "timed_out": False,
            "test_summary": {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
        }

    # Parse test results from output
    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)

    # Simple parsing of pytest output
    passed = 0
    failed = 0
    skipped = 0
    errors = 0

    # Pattern: "N passed, M failed, K skipped"
    summary_match = re.search(
        r"(\d+)\s+passed\s+(\d+)\s+failed\s+(\d+)\s+skipped",
        stdout + stderr,
        re.IGNORECASE,
    )
    if summary_match:
        passed = int(summary_match.group(1))
        failed = int(summary_match.group(2))
        skipped = int(summary_match.group(3))

    # Pattern: "ERROR: N errors"
    error_match = re.search(r"ERROR[:\s]+(\d+)", stdout + stderr, re.IGNORECASE)
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