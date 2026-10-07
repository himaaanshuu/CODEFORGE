# CodeForge AI Agent Models
from __future__ import annotations

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


# Agent execution status
class AgentStatus(BaseModel):
    """Status of agent execution during a task."""

    status: Literal["running", "completed", "failed", "iterations_exceeded"] = Field(
        ...,
        description="Current agent execution status.",
    )
    iteration: int = Field(
        0,
        description="Current iteration step number.",
    )
    max_iterations: int = Field(
        10,
        description="Maximum number of agent iterations allowed.",
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Names of tools executed so far.",
    )
    messages: List[str] = Field(
        default_factory=list,
        description="High-level summaries of agent reasoning.",
    )


# Agent request
class AgentRequest(BaseModel):
    """Request model for the coding agent analysis endpoint."""

    workspace_id: str = Field(
        ...,
        description="Identifier mapping to a configured workspace root directory.",
    )
    task: str = Field(
        ...,
        description="The coding task or question for the agent to analyze.",
    )
    max_iterations: Optional[int] = Field(
        None,
        description="Override maximum agent iterations (defaults to 10).",
    )


# Tool call
class ToolCall(BaseModel):
    """Model representing a single tool call by the agent."""

    tool_name: str = Field(
        ...,
        description="Name of the tool to execute (list_files, read_file, search_code).",
    )
    arguments: Dict[str, Any] = Field(
        ...,
        description="Tool-specific arguments matching the input schema.",
    )


# Tool result
class ToolResult(BaseModel):
    """Model representing the result of a tool execution."""

    tool_name: str = Field(
        ...,
        description="Name of the tool that was executed.",
    )
    success: bool = Field(
        ...,
        description="Whether the tool execution succeeded.",
    )
    data: Optional[Any] = Field(
        None,
        description="Tool execution result data.",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if execution failed.",
    )


# Agent observation
class AgentObservation(BaseModel):
    """Model representing an observation after a tool call."""

    tool_name: str = Field(
        ...,
        description="Name of the tool that was executed.",
    )
    tool_success: bool = Field(
        ...,
        description="Whether the tool execution succeeded.",
    )
    observation: str = Field(
        ...,
        description="Human-readable summary of what the tool revealed.",
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Raw data from the tool, if useful for debugging.",
    )


# Agent response
class AgentResponse(BaseModel):
    """Response model from the coding agent analysis endpoint."""

    success: bool = Field(
        ...,
        description="Whether the agent successfully completed the analysis.",
    )
    status: str = Field(
        ...,
        description="Final agent execution status.",
    )
    summary: str = Field(
        ...,
        description="High-level summary of the agent's findings.",
    )
    files_inspected: List[str] = Field(
        default_factory=list,
        description="List of file paths the agent inspected.",
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Names of tools executed during the analysis.",
    )
    plan: List[str] = Field(
        default_factory=list,
        description="Structured implementation or analysis plan.",
    )
    observations: List[AgentObservation] = Field(
        default_factory=list,
        description="Observations from each tool call.",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if the analysis failed.",
    )
    iteration: int = Field(
        0,
        description="Final iteration count.",
    )


# System prompt for the agent
SYSTEM_PROMPT = """You are CodeForge AI, a software engineering analysis and modification agent.

Your responsibility is to understand a software repository and analyze coding tasks,
and when needed, make controlled modifications to address the task.

You have access to these tools:
- list_files: List files and directories inside the repository workspace
- read_file: Read a file's contents inside the repository workspace (includes line numbers)
- search_code: Search source code inside the repository workspace
- apply_patch: Apply a unified diff patch to modify files inside the repository workspace
- inspect_diff: Inspect the current changes/diff in the repository workspace
- write_file: Write content to a file inside the repository workspace (restricted)

Rules:
1. Never assume file contents - always use read_file or search_code to inspect
2. Inspect the repository before making conclusions about its structure or behavior
3. Use tools when repository information is required - do not guess
4. Do not invent files, functions, or dependencies
5. Keep investigation focused on the task at hand
6. Explain your reasoning at a high level in observations
7. When modifications are needed, use apply_patch as the primary mechanism
8. Inspect the diff after modification using inspect_diff
9. Do not modify files randomly - have a reasoned justification
10. Do not execute commands - do not attempt shell/terminal execution
11. Do not access anything outside the repository workspace
12. After modifying, run tests to verify the changes
13. Use write_file only when apply_patch is not sufficient, and only for files inside the workspace

Do not expose hidden chain-of-thought.

Return concise reasoning summaries and evidence gathered from tools instead of speculative reasoning.
"""


# Agent instructions for the LLM
AGENT_INSTRUCTIONS = """You are CodeForge AI analyzing a coding task.

Current task: {task}

Available tools:
1. list_files: List files/directories in the repository workspace
   - Input: {{"path": "relative/path"}}
   - Output: sorted list of entry names

2. read_file: Read a file's contents with line numbers
   - Input: {{"path": "relative/path/to/file"}}
   - Output: formatted string like "1 | line1\n2 | line2" or {{"raw": "raw content"}}

3. search_code: Search for text in source files
   - Input: {{"query": "text to search", "case_insensitive": true, "max_results": 50, "max_lines": 3}}
   - Output: list of {{"file_path": "...", "line_number": N, "matching_line": "...", "context": "..."}}

4. apply_patch: Apply a unified diff patch to modify files
   - Input: {{"patch": "unified diff text"}}
   - Output: {{"success": true, "files_changed": ["file.py"], "message": "Patch applied successfully."}}
   - Use this as the primary modification mechanism
   - The patch should be a valid unified diff format

5. inspect_diff: Inspect current changes/diff in the workspace
   - Input: (no inputs required)
   - Output: {{"files_changed": [...], "insertions": N, "deletions": N, "diff": "..."}}

6. write_file: Write content to a file (restricted, use apply_patch first)
   - Input: {{"path": "relative/path/to/file", "content": "file contents"}}
   - Output: {{"success": true, "bytes_written": N, "message": "File written successfully."}}
   - Only use when apply_patch cannot achieve the desired change
   - Must be inside the repository workspace

Rules:
- Never assume file contents - always use the tools
- Inspect the repository structure first with list_files
- Use read_file to inspect specific files
- Use search_code to find relevant code patterns
- Keep investigation focused on the task
- Provide a concise analysis summary when sufficient information is gathered
- Preferred sequence: list_files -> search_code -> read_file -> reason -> plan -> apply_patch -> inspect_diff
- Do not modify files randomly - have a reasoned justification
- After modifying, always inspect the diff to verify changes
- Run tests to verify changes are correct
- Stay within the repository workspace

Think step by step and use tools when you need repository information.
"""


# Event types for frontend display
class AgentEvent(BaseModel):
    """Event model for agent activity display.

    Allows the future frontend to display agent activity in real-time.
    Each event contains only useful information - no secrets, no hidden prompts.
    """

    type: Literal[
        "agent_started",
        "thinking",
        "tool_requested",
        "tool_completed",
        "analysis_updated",
        "agent_completed",
        "agent_failed",
        "plan_created",
        "patch_created",
        "patch_applied",
        "diff_inspected",
        "tests_started",
        "tests_completed",
        "failure_detected",
        "repair_started",
        "repair_attempt",
        "verification_started",
    ] = Field(..., description="Type of agent event.")
    timestamp: float = Field(
        default_factory=lambda: __import__("time").time(),
        description="Event timestamp in seconds since epoch.",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data - useful information only.",
    )


class AgentStartedEvent(AgentEvent):
    """Event emitted when agent starts analyzing a task."""

    type: Literal["agent_started"] = Field(default="agent_started")
    workspace_id: str = Field(..., description="Workspace identifier.")
    task: str = Field(..., description="The coding task.")


class ToolRequestedEvent(AgentEvent):
    """Event emitted when agent requests a tool call."""

    type: Literal["tool_requested"] = Field(default="tool_requested")
    tool_name: str = Field(..., description="Name of the tool requested.")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments.")


class ToolCompletedEvent(AgentEvent):
    """Event emitted when a tool call completes."""

    type: Literal["tool_completed"] = Field(default="tool_completed")
    tool_name: str = Field(..., description="Name of the tool executed.")
    success: bool = Field(..., description="Whether execution succeeded.")
    observation: str = Field(
        ...,
        description="High-level summary of what the tool revealed.",
    )


class AgentCompletedEvent(AgentEvent):
    """Event emitted when agent completes the analysis."""

    type: Literal["agent_completed"] = Field(default="agent_completed")
    summary: str = Field(..., description="High-level summary of findings.")
    status: str = Field(..., description="Final agent status.")


class AgentFailedEvent(AgentEvent):
    """Event emitted when agent fails the analysis."""

    type: Literal["agent_failed"] = Field(default="agent_failed")
    error: str = Field(..., description="Error message.")


class PlanCreatedEvent(AgentEvent):
    """Event emitted when a plan is created for the task."""

    type: Literal["plan_created"] = Field(default="plan_created")
    plan: List[str] = Field(..., description="The created implementation/analysis plan.")


class PatchCreatedEvent(AgentEvent):
    """Event emitted when a patch is created/modified."""

    type: Literal["patch_created"] = Field(default="patch_created")
    files_affected: List[str] = Field(..., description="List of files the patch will affect.")
    patch_summary: str = Field(..., description="Summary of the patch changes.")


class PatchAppliedEvent(AgentEvent):
    """Event emitted when a patch is applied to the repository."""

    type: Literal["patch_applied"] = Field(default="patch_applied")
    files_changed: List[str] = Field(..., description="List of files that were modified.")
    diff_preview: str = Field(..., description="Preview of the generated diff.")


class DiffInspectedEvent(AgentEvent):
    """Event emitted when a diff is inspected."""

    type: Literal["diff_inspected"] = Field(default="diff_inspected")
    files_inspected: List[str] = Field(..., description="Files inspected in the diff.")
    diff_summary: str = Field(..., description="Summary of the diff observations.")


class TestsStartedEvent(AgentEvent):
    """Event emitted when tests are started."""

    type: Literal["tests_started"] = Field(default="tests_started")
    test_command: str = Field(..., description="The test command being executed.")


class TestsCompletedEvent(AgentEvent):
    """Event emitted when tests complete."""

    type: Literal["tests_completed"] = Field(default="tests_completed")
    test_results: Dict[str, Any] = Field(..., description="Structured test results.")


class FailureDetectedEvent(AgentEvent):
    """Event emitted when test failures are detected."""

    type: Literal["failure_detected"] = Field(default="failure_detected")
    failure_summary: str = Field(..., description="Summary of the test failures.")
    failed_count: int = Field(..., description="Number of tests that failed.")


class RepairStartedEvent(AgentEvent):
    """Event emitted when repair loop starts."""

    type: Literal["repair_started"] = Field(default="repair_started")
    repair_attempt: int = Field(..., description="Current repair attempt number.")


class RepairAttemptEvent(AgentEvent):
    """Event emitted during each repair attempt."""

    type: Literal["repair_attempt"] = Field(default="repair_attempt")
    attempt: int = Field(..., description="Repair attempt number.")
    message: str = Field(..., description="Diagnostic message for this attempt.")


class VerificationStartedEvent(AgentEvent):
    """Event emitted when verification starts."""

    type: Literal["verification_started"] = Field(default="verification_started")
    description: str = Field(..., description="Description of what is being verified.")