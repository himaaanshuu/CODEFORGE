# CodeForge AI Agent State
from __future__ import annotations

import json
from typing import Optional, List, Dict, Any

from .models import (
    AgentStatus,
    AgentRequest,
    ToolCall,
    ToolResult,
    AgentObservation,
    AgentResponse,
    AgentEvent,
    AgentStartedEvent,
    ToolRequestedEvent,
    ToolCompletedEvent,
    AgentCompletedEvent,
    AgentFailedEvent,
    PlanCreatedEvent,
    PatchCreatedEvent,
    PatchAppliedEvent,
    DiffInspectedEvent,
    TestsStartedEvent,
    TestsCompletedEvent,
    FailureDetectedEvent,
    RepairStartedEvent,
    RepairAttemptEvent,
    VerificationStartedEvent,
)


class AgentState:
    """State needed during a single agent execution.

    Holds the cumulative state as the agent loops through tool calls
    and LLM reasoning steps.
    """

    # Phase values for the agent lifecycle
    PHASE_EXPLORATION = "exploration"
    PHASE_PLANNING = "planning"
    PHASE_MODIFICATION = "modification"
    PHASE_TESTING = "testing"
    PHASE_FAILURE_ANALYSIS = "failure_analysis"
    PHASE_REPAIR = "repair"
    PHASE_VERIFICATION = "verification"
    PHASE_COMPLETED = "completed"
    PHASE_FAILED = "failed"

    def __init__(
        self,
        workspace_root: str,
        task: str,
        max_iterations: int = 10,
        max_repair_iterations: int = 5,
        workspace: Optional[Any] = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.task = task
        self.max_iterations = max_iterations
        self.max_repair_iterations = max_repair_iterations
        self.workspace = workspace  # Will be a Workspace instance if provided

        # Execution tracking
        self.iteration = 0
        self.status = AgentStatus(
            status="running", iteration=0, max_iterations=max_iterations
        )

        # Cumulative results
        self.tools_used: List[str] = []
        self.observations: List[AgentObservation] = []
        self.files_inspected: List[str] = []
        self.plan: List[str] = []
        self.files_changed: List[str] = []
        self.modification_count: int = 0
        self.diff_summary: str = ""

        # Repair loop tracking
        self.repair_attempts: int = 0
        self.last_test_result: Optional[Dict[str, Any]] = None
        self.failure_history: List[Dict[str, Any]] = []
        self.repeated_failure_count: int = 0

        # Current agent phase
        self.phase: str = self.PHASE_EXPLORATION

        # Verification tracking
        self.verification_status: Optional[str] = None

        # Event history (for frontend streaming)
        self.events: List[AgentEvent] = []

        # Tool instances (lazy-loaded)
        self._list_tool: Optional[ListFilesTool] = None
        self._read_tool: Optional[ReadFileTool] = None
        self._search_tool: Optional[SearchCodeTool] = None
        self._apply_patch_tool: Optional[Any] = None
        self._inspect_diff_tool: Optional[Any] = None
        self._write_file_tool: Optional[Any] = None
        self._run_tests_tool: Optional[Any] = None

    def _get_list_tool(self) -> ListFilesTool:
        if self._list_tool is None:
            from ..repository.workspace import Workspace
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._list_tool = ListFilesTool(ws)
        return self._list_tool

    def _get_read_tool(self) -> ReadFileTool:
        if self._read_tool is None:
            from ..repository.workspace import Workspace
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._read_tool = ReadFileTool(ws)
        return self._read_tool

    def _get_search_tool(self) -> SearchCodeTool:
        if self._search_tool is None:
            from ..repository.workspace import Workspace
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._search_tool = SearchCodeTool(ws)
        return self._search_tool

    def _get_apply_patch_tool(self) -> Any:
        if self._apply_patch_tool is None:
            from ..repository.workspace import Workspace
            from ..tools.modification_tools import ApplyPatchTool
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._apply_patch_tool = ApplyPatchTool(ws)
        return self._apply_patch_tool

    def _get_inspect_diff_tool(self) -> Any:
        if self._inspect_diff_tool is None:
            from ..repository.workspace import Workspace
            from ..tools.modification_tools import InspectDiffTool
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._inspect_diff_tool = InspectDiffTool(ws)
        return self._inspect_diff_tool

    def _get_write_file_tool(self) -> Any:
        if self._write_file_tool is None:
            from ..repository.workspace import Workspace
            from ..tools.modification_tools import WriteFileTool
            ws = (
                self.workspace
                if self.workspace is not None
                else Workspace(self.workspace_root)
            )
            self._write_file_tool = WriteFileTool(ws)
        return self._write_file_tool

    def increment_iteration(self) -> None:
        """Increment the iteration counter and update status."""
        self.iteration += 1
        self.status.iteration = self.iteration
        if self.iteration >= self.max_iterations:
            self.status.status = "iterations_exceeded"

    def add_observation(
        self,
        tool_name: str,
        tool_success: bool,
        observation: str,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add an observation from a tool call."""
        obs = AgentObservation(
            tool_name=tool_name,
            tool_success=tool_success,
            observation=observation,
            raw_data=raw_data,
        )
        self.observations.append(obs)

    def add_event(self, event: AgentEvent) -> None:
        """Add an event to the history."""
        self.events.append(event)

    def track_modification(self, file_path: str, diff_preview: str = "") -> None:
        """Track a file modification from apply_patch or write_file."""
        if file_path not in self.files_changed:
            self.files_changed.append(file_path)
        self.modification_count += 1

    def set_plan(self, plan: List[str]) -> None:
        """Set the implementation plan and emit plan_created event."""
        self.plan = plan
        self.add_event(
            PlanCreatedEvent(
                plan=plan,
                data={"task": self.task},
            )
        )

    def set_diff_summary(self, summary: str) -> None:
        """Set the diff summary and emit diff_inspected event."""
        self.diff_summary = summary
        self.add_event(
            DiffInspectedEvent(
                files_inspected=self.files_changed,
                diff_summary=summary,
                data={"task": self.task},
            )
        )

    def set_tests_results(self, results: Dict[str, Any]) -> None:
        """Set test results and emit tests_completed event."""
        self.last_test_result = results
        self.add_event(
            TestsCompletedEvent(
                test_results=results,
                data={"task": self.task},
            )
        )

    def add_failure_detection(self, summary: str, failed_count: int) -> None:
        """Record a test failure detection."""
        self.add_event(
            FailureDetectedEvent(
                failure_summary=summary,
                failed_count=failed_count,
                data={"task": self.task},
            )
        )
        # Add to failure history
        self.failure_history.append(
            {
                "attempt": self.repair_attempts + 1,
                "failure_summary": summary,
                "failed_count": failed_count,
                "modifications": self.files_changed.copy(),
            }
        )
        # Keep only last 10 failure entries
        if len(self.failure_history) > 10:
            self.failure_history = self.failure_history[-10:]

    def add_repair_attempt(self, attempt: int, message: str) -> None:
        """Record a repair attempt."""
        self.repair_attempts = attempt
        self.add_event(
            RepairAttemptEvent(
                attempt=attempt,
                message=message,
                data={"task": self.task},
            )
        )

    def add_verification_started(self, description: str) -> None:
        """Emit a verification started event."""
        self.verification_status = "started"
        self.add_event(
            VerificationStartedEvent(
                description=description,
                data={"task": self.task},
            )
        )

    def set_verification_status(self, status: str) -> None:
        """Set the verification status."""
        self.verification_status = status
        if status == "passed":
            self.phase = self.PHASE_COMPLETED
        elif status == "failed":
            self.phase = self.PHASE_REPAIR

    def can_attempt_repair(self) -> bool:
        """Check if another repair attempt is allowed."""
        return self.repair_attempts < self.max_repair_iterations and self.iteration < self.max_iterations

    def reset_repair_counter(self) -> None:
        """Reset the repair attempt counter for a new repair cycle."""
        self.repair_attempts = 0
        self.repeated_failure_count = 0

    def increment_repeated_failure_count(self) -> int:
        """Increment and return the repeated failure count."""
        self.repeated_failure_count += 1
        return self.repeated_failure_count

    def to_response(self) -> AgentResponse:
        """Convert current state to an AgentResponse."""
        return AgentResponse(
            success=self.status.status in ("completed", "iterations_exceeded")
            and self.iteration > 0,
            status=self.status.status,
            summary=" | ".join(self.status.messages or ["Analysis completed"]),
            files_inspected=self.files_inspected,
            tools_used=self.tools_used,
            plan=self.plan,
            observations=self.observations,
            files_changed=self.files_changed,
            modification_count=self.modification_count,
            diff_summary=self.diff_summary,
            error=self.status.error if hasattr(self.status, "error") else None,
            iteration=self.iteration,
            repair_attempts=self.repair_attempts,
            max_repair_iterations=self.max_repair_iterations,
            phase=self.phase,
        )