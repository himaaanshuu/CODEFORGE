from __future__ import annotations

import signal
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    """Structured execution request for sandboxed test execution."""

    command: str = Field(
        ...,
        description="The executable command to run (must be in the allowlist).",
    )
    args: Optional[List[str]] = Field(
        default_factory=list,
        description="Arguments to pass to the command.",
    )
    timeout: Optional[int] = Field(
        60,
        description="Maximum execution time in seconds.",
        ge=1,
        le=300,
    )
    cwd: Optional[str] = Field(
        None,
        description="Working directory for the command (must be inside workspace).",
    )


class ExecutionResult(BaseModel):
    """Structured result from sandboxed execution."""

    success: bool = Field(
        ...,
        description="Whether the execution completed successfully.",
    )
    exit_code: Optional[int] = Field(
        default=None,
        description="Process exit code.",
    )
    stdout: str = Field(
        default="",
        description="Captured standard output.",
    )
    stderr: str = Field(
        default="",
        description="Captured standard error.",
    )
    duration_ms: int = Field(
        ...,
        description="Execution duration in milliseconds.",
    )
    timed_out: bool = Field(
        default=False,
        description="Whether the execution was terminated due to timeout.",
    )
    output_limit_reached: bool = Field(
        default=False,
        description="Whether the output size limit was reached.",
    )


class ExecutionPolicy:
    """Policy governing what commands can be executed in the sandbox."""

    # Allowlist of safe executables for test execution
    ALLOWED_COMMANDS = {
        "pytest": True,
        "python": True,
        "python3": True,
    }

    # Forbidden commands (dangerous or unauthorized)
    FORBIDDEN_COMMANDS = {
        "rm": True,
        "sudo": True,
        "curl": True,
        "wget": True,
        "ssh": True,
        "scp": True,
        "kill": True,
        "killall": True,
        "reboot": True,
        "shutdown": True,
        "format": True,
    }

    # Resource limits
    DEFAULT_TIMEOUT_SECONDS = 60
    MAX_OUTPUT_BYTES = 100_000  # 100KB
    MAX_ERROR_OUTPUT = 10_000  # 10KB

    @classmethod
    def is_command_allowed(cls, command: str) -> bool:
        """Check if a command is allowed according to the policy."""
        # Check forbidden list first
        if command in cls.FORBIDDEN_COMMANDS:
            return False
        # Check allowlist (only allowed commands can run)
        if command not in cls.ALLOWED_COMMANDS:
            return False
        return True

    @classmethod
    def get_default_timeout(cls) -> int:
        """Get the default timeout in seconds."""
        return cls.DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def get_max_output_bytes(cls) -> int:
        """Get the maximum output size in bytes."""
        return cls.MAX_OUTPUT_BYTES