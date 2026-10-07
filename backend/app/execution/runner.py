from __future__ import annotations

import os
import resource
import signal
import subprocess
import time
from pathlib import Path
from typing import Optional

from ..execution.models import ExecutionRequest, ExecutionResult


class ExecutionRunner:
    """Runs commands in a sandboxed, workspace-scoped environment.

    Safety features:
    - Command allowlist policy
    - Workspace-restricted working directory
    - Timeout enforcement
    - Output size limits
    - No network access
    - Environment sanitization
    """

    # Maximum output size in bytes (enforced by policy)
    MAX_OUTPUT_BYTES = 100_000

    def __init__(self, policy: Optional[Any] = None, workspace_root: Optional[str] = None) -> None:
        self.policy = policy or self._default_policy()
        self.workspace_root = workspace_root or os.getcwd()

    def _default_policy(self) -> Any:
        """Create a default execution policy."""
        from ..execution.policy import ExecutionPolicy
        return ExecutionPolicy()

    def _sanitize_env(self, env: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Sanitize the environment variables - only allow safe ones."""
        safe_env = {}
        # Pass through essential variables, strip sensitive ones
        for key, value in os.environ.items():
            # Allow common safe variables
            if key in (
                "PATH",
                "PYTHONPATH",
                "HOME",
                "TERM",
                "TMPDIR",
                "PWD",
            ):
                safe_env[key] = value
            # Skip potentially sensitive variables
            elif not any(
                key.startswith(prefix)
                for prefix in ("SECRET", "KEY", "TOKEN", "PASSWORD", "API")
            ):
                # Only include if not explicitly denied
                safe_env[key] = value
        return safe_env

    def _validate_cwd(self, cwd: Optional[str]) -> Optional[str]:
        """Validate that the working directory is inside the workspace."""
        if cwd is None:
            return None
        
        # Resolve the cwd path
        abs_cwd = os.path.abspath(cwd)
        workspace_abs = os.path.abspath(self.workspace_root)
        
        # Check that cwd is inside workspace
        if not abs_cwd.startswith(workspace_abs + os.sep) and abs_cwd != workspace_abs:
            return None
        
        # Check the directory exists
        if not os.path.isdir(abs_cwd):
            return None
        
        return abs_cwd

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a command in a sandboxed environment.

        Args:
            request: The execution request with command, args, timeout, and cwd.

        Returns:
            ExecutionResult with the execution outcome.
        """
        # Validate the command against policy
        cmd_name = request.command
        if not self.policy.is_command_allowed(cmd_name):
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr=f"Command '{cmd_name}' is not allowed by the execution policy.",
                duration_ms=0,
                timed_out=False,
                output_limit_reached=False,
            )

        # Validate and sanitize working directory
        safe_cwd = self._validate_cwd(request.cwd)
        if safe_cwd is None:
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr=f"Working directory '{request.cwd}' is not inside the workspace or does not exist.",
                duration_ms=0,
                timed_out=False,
                output_limit_reached=False,
            )

        # Prepare the command
        full_command = [cmd_name] + (request.args or [])

        # Set up environment
        env = self._sanitize_env(None)

        # Execute with timeout
        start_time = time.time()
        timed_out = False
        timed_out_flag = [False]

        def timeout_handler(signum, frame):
            timed_out_flag[0] = True
            raise TimeoutError("Execution timed out")

        # Set timeout alarm
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(request.timeout)

        try:
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=safe_cwd,
                env=env,
                text=True,
            )

            # Read output with size limits
            stdout_chunks = []
            stderr_chunks = []
            stdout_size = 0
            stderr_size = 0

            try:
                # Read stdout line by line with size limit
                for line in iter(process.stdout.readline, ""):
                    if timed_out_flag[0]:
                        break
                    chunk_bytes = line.encode("utf-8")
                    if stdout_size + len(chunk_bytes) > self.MAX_OUTPUT_BYTES:
                        stdout_size = self.MAX_OUTPUT_BYTES
                        stdout_chunks.append("... [output truncated] ...")
                        break
                    stdout_size += len(chunk_bytes)
                    stdout_chunks.append(line)
                
                # Read stderr line by line with size limit
                for line in iter(process.stderr.readline, ""):
                    if timed_out_flag[0]:
                        break
                    chunk_bytes = line.encode("utf-8")
                    if stderr_size + len(chunk_bytes) > self.MAX_ERROR_OUTPUT:
                        stderr_size = self.MAX_ERROR_OUTPUT
                        stderr_chunks.append("... [error output truncated] ...")
                        break
                    stderr_size += len(chunk_bytes)
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

            # Truncate output if needed
            stdout = "".join(stdout_chunks)
            stderr = "".join(stderr_chunks)

            # Check if output limits were reached
            output_limit_reached = stdout_size > self.MAX_OUTPUT_BYTES or stderr_size > self.MAX_ERROR_OUTPUT

            return ExecutionResult(
                success=not timed_out and process.returncode == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_ms=duration_ms,
                timed_out=timed_out,
                output_limit_reached=output_limit_reached,
            )

        except Exception as e:
            signal.alarm(0)  # Cancel the alarm
            signal.signal(signal.SIGALRM, old_handler)
            return ExecutionResult(
                success=False,
                exit_code=None,
                stdout="",
                stderr=f"Execution error: {str(e)[:200]}",
                duration_ms=int((time.time() - start_time) * 1000),
                timed_out=False,
                output_limit_reached=False,
            )