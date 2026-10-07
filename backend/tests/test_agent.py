"""Unit tests for CodeForge AI coding agent.

These tests mock the LLM and test the agent orchestration logic,
tool execution, and state management without requiring a live Nebius API call.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

import pytest

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.agent.agent import (
    run_agent_task,
    _parse_llm_response,
    _build_combined_prompt,
)
from backend.app.agent.models import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    ToolCall,
    ToolResult,
    AgentObservation,
    AgentResponse as AR,
    AgentStartedEvent,
    ToolRequestedEvent,
    ToolCompletedEvent,
    AgentFailedEvent,
    AgentEvent,
)
from backend.app.tools.repository_tools import ListFilesTool, ReadFileTool, SearchCodeTool
from backend.app.agent.state import AgentState
from backend.app.repository.workspace import Workspace


def test_parse_llm_response_final_analysis() -> None:
    """Test parsing LLM response with FINAL ANALYSIS marker."""
    # The summary is the text before FINAL ANALYSIS:
    # The plan items are extracted from after the marker
    response = "Analysis complete.\n\nFINAL ANALYSIS: Here is what I found.\n- Plan item 1\n- Plan item 2"
    result = _parse_llm_response(response)
    assert result["type"] == "final_analysis"
    assert "Analysis complete." in result["summary"]
    assert len(result["plan"]) == 2
    assert result["plan"][0] == "Plan item 1"
    assert result["plan"][1] == "Plan item 2"
    print("PASS: test_parse_llm_response_final_analysis")


def test_parse_llm_response_error() -> None:
    """Test parsing LLM response with ERROR marker."""
    response = "Something went wrong\n\nERROR: Failed to connect to model"
    result = _parse_llm_response(response)
    assert result["type"] == "error"
    assert "Failed to connect to model" in result["error"]
    print("PASS: test_parse_llm_response_error")


def test_parse_llm_response_tool_call() -> None:
    """Test parsing LLM response that mentions a tool name."""
    response = "I'll use the search_code tool to find the answer."
    result = _parse_llm_response(response)
    # Should return thinking or tool_call
    assert result["type"] in ("tool_call", "thinking")
    print("PASS: test_parse_llm_response_tool_call")


def test_build_combined_prompt() -> None:
    """Test building the combined prompt for the LLM."""
    system_prompt = "You are CodeForge AI"
    task = "Find the add function"
    instructions = "Use tools to investigate"
    observations = [
        {"tool_name": "list_files", "tool_success": True, "observation": "Found app.py"}
    ]

    prompt = _build_combined_prompt(
        system_prompt=system_prompt,
        task=task,
        instructions=instructions,
        observations=observations,
    )

    assert system_prompt in prompt
    assert "Task: Find the add function" in prompt
    assert "Found app.py" in prompt
    assert "Next step:" in prompt
    print("PASS: test_build_combined_prompt")


@pytest.mark.asyncio
async def test_agent_task_without_llm() -> None:
    """Test agent task orchestration with a mock workspace.

    This test verifies the agent loop structure without requiring
    a live Nebius API call. We test the workspace and tool
    integration points.
    """
    # Create a temporary test repository
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample app file
        app_file = os.path.join(tmpdir, "app.py")
        with open(app_file, "w") as f:
            f.write("def add(x, y):\n    return x + y\n\ndef multiply(x, y):\n    return x * y\n")

        # Create a Workspace
        ws = Workspace(tmpdir)

        # Test list_files
        list_tool_result = await ListFilesTool(ws).execute()
        assert list_tool_result.success is True
        assert isinstance(list_tool_result.data, list)

        # Test reading a file
        read_result = await ReadFileTool(ws).execute(path="app.py")
        assert read_result.success is True

        # Test that path traversal is rejected
        traverse_result = await ListFilesTool(ws).execute(path="../etc/passwd")
        assert traverse_result.success is False or traverse_result.data is None

        # Test read_file with invalid path
        read_invalid = await ReadFileTool(ws).execute(path="../etc/passwd")
        assert read_invalid.success is False

        print("PASS: test_agent_task_without_llm")


def test_agent_status_initialization() -> None:
    """Test AgentStatus initialization."""
    status = AgentStatus(status="running", iteration=0, max_iterations=10)
    assert status.status == "running"
    assert status.iteration == 0
    assert status.max_iterations == 10

    # Test iteration increment
    status.iteration += 1
    assert status.iteration == 1
    print("PASS: test_agent_status_initialization")


def test_agent_observation_creation() -> None:
    """Test AgentObservation creation and validation."""
    obs = AgentObservation(
        tool_name="read_file",
        tool_success=True,
        observation="File contained a function definition.",
    )
    assert obs.tool_name == "read_file"
    assert obs.tool_success is True
    assert "function definition" in obs.observation

    # Observation with raw data
    obs2 = AgentObservation(
        tool_name="search_code",
        tool_success=True,
        observation="Found 3 matches.",
        raw_data={"results": 3, "files": ["app.py"]},
    )
    assert obs2.raw_data == {"results": 3, "files": ["app.py"]}
    print("PASS: test_agent_observation_creation")


def test_agent_response_creation() -> None:
    """Test AgentResponse creation."""
    response = AR(
        success=True,
        status="completed",
        summary="Analysis complete",
        files_inspected=["app.py", "app.py"],
        tools_used=["list_files", "read_file"],
        plan=["Implement the feature"],
        observations=[],
        error=None,
        iteration=5,
    )

    assert response.success is True
    assert response.status == "completed"
    assert response.summary == "Analysis complete"
    assert len(response.files_inspected) == 2
    assert len(response.tools_used) == 2
    assert len(response.plan) == 1
    assert response.iteration == 5
    print("PASS: test_agent_response_creation")


def test_agent_event_types() -> None:
    """Test that all agent event types are valid."""
    from backend.app.agent.models import AgentStartedEvent, ToolRequestedEvent, ToolCompletedEvent, AgentCompletedEvent, AgentFailedEvent

    # AgentStartedEvent
    ev1 = AgentStartedEvent(workspace_id="ws1", task="test task")
    assert ev1.type == "agent_started"
    assert ev1.workspace_id == "ws1"
    assert ev1.task == "test task"

    # ToolRequestedEvent
    ev2 = ToolRequestedEvent(tool_name="list_files", arguments={"path": "."})
    assert ev2.type == "tool_requested"
    assert ev2.tool_name == "list_files"

    # ToolCompletedEvent
    ev3 = ToolCompletedEvent(tool_name="read_file", success=True, observation="File read successfully")
    assert ev3.type == "tool_completed"
    assert ev3.success is True

    # AgentCompletedEvent
    ev4 = AgentCompletedEvent(summary="Done", status="completed")
    assert ev4.type == "agent_completed"

    # AgentFailedEvent
    ev5 = AgentFailedEvent(error="Something went wrong")
    assert ev5.type == "agent_failed"

    print("PASS: test_agent_event_types")


def main() -> None:
    """Run all agent unit tests."""
    tests = [
        test_parse_llm_response_final_analysis,
        test_parse_llm_response_error,
        test_parse_llm_response_tool_call,
        test_build_combined_prompt,
        test_agent_status_initialization,
        test_agent_observation_creation,
        test_agent_response_creation,
        test_agent_event_types,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    # Also run the async test
    try:
        asyncio.run(test_agent_task_without_llm())
        passed += 1
    except Exception as e:
        print(f"ERROR: test_agent_task_without_llm: {e}")
        failed += 1

    print(f"\n{'='*50}")
    print(f"Agent tests: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())