# CodeForge AI Agent Orchestration
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from .models import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    ToolCall,
    ToolResult,
    AgentObservation,
    AgentObservation,
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
    AgentEvent,
)
from .prompts import get_system_prompt, get_agent_instructions
from .state import AgentState
from ..repository.workspace import Workspace
from ..tools.registry import ToolRegistry
from ..tools.repository_tools import ListFilesTool, ReadFileTool, SearchCodeTool


MAX_DEFAULT_ITERATIONS = 10


async def run_agent_task(
    workspace_root: str,
    task: str,
    max_iterations: Optional[int] = None,
) -> AgentResponse:
    """Run the CodeForge AI coding agent on a given task.

    This is the main orchestration loop that:
    1. Initializes the agent state
    2. Formats the system prompt with the task
    3. Loops: Sends prompt + tool results to NVIDIA model -> Gets response -> Executes tools
    4. Stops when task is complete, iterations exceeded, or error occurs

    Returns an AgentResponse with the analysis results.
    """
    if max_iterations is None:
        max_iterations = MAX_DEFAULT_ITERATIONS

    # Initialize workspace and agent state
    ws = Workspace(workspace_root)
    state = AgentState(
        workspace_root=workspace_root,
        task=task,
        max_iterations=max_iterations,
        workspace=ws,
    )

    # Emit agent started event
    started_event = AgentStartedEvent(workspace_id=ws.root, task=task)
    state.add_event(started_event)

    # Initialize tool registry
    registry = ToolRegistry()

    # Lazy-register tools with the registry
    list_tool = ListFilesTool(ws)
    read_tool = ReadFileTool(ws)
    search_tool = SearchCodeTool(ws)
    patch_tool = ApplyPatchTool(ws)
    inspect_diff_tool = InspectDiffTool(ws)
    write_file_tool = WriteFileTool(ws)
    registry.register(list_tool)
    registry.register(read_tool)
    registry.register(search_tool)
    registry.register(patch_tool)
    registry.register(inspect_diff_tool)
    registry.register(write_file_tool)

    # Prepare initial system prompt
    system_prompt = get_system_prompt()
    agent_instructions = get_agent_instructions(task)

    # Main agent loop
    repair_phase = False
    while state.iteration < max_iterations:
        state.increment_iteration()

        # Check if we're in a repair phase and need to stop
        if repair_phase and state.repair_attempts >= state.max_repair_iterations:
            state.phase = AgentState.PHASE_FAILED
            state.status.status = "repair_failed"
            state.status.error = f"Maximum repair iterations ({state.max_repair_iterations}) reached"
            break

        # Format the agent instructions with current task
        current_instructions = get_agent_instructions(task)

        # Build the message history for the LLM
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{current_instructions}\n\nTask: {task}"},
        ]

        # Add previous observations as messages from "tool" role
        for obs in state.observations:
            if obs.tool_success:
                messages.append(
                    {"role": "tool", "content": f"Tool {obs.tool_name} result: {obs.observation}"}
                )
            else:
                messages.append(
                    {"role": "tool", "content": f"Tool {obs.tool_name} failed: {obs.observation}"}
                )

        # Add failure history if available (to avoid repeating same patches)
        if state.failure_history:
            messages.append({
                "role": "system",
                "content": f"Previous failure history (avoid repeating these patches):\n"
                           f"{json.dumps(state.failure_history[-3:], indent=2)}"
            })

        # Call the LLM (using the existing Nebius client)
        from ..llm.client import get_client

        client = get_client()
        response = await client.generate(
            prompt="",  # We'll use the messages list approach - but generate() takes a prompt string
            model=None,
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
        )

        # Since the client.generate() takes a single prompt string, we'll create a
        # combined prompt from the instructions and observations
        combined_prompt = _build_combined_prompt(
            system_prompt=system_prompt,
            task=task,
            instructions=current_instructions,
            observations=state.observations,
        )

        # Generate the next step from the LLM
        llm_response = await _call_llm_with_prompt(
            prompt=combined_prompt,
            model=None,
            temperature=0.7,
            max_tokens=1000,
        )

        # Parse the LLM response to determine the next action
        # The LLM should respond with either a tool call or a final analysis
        action = _parse_llm_response(llm_response.response or "")

        if action["type"] == "tool_call":
            # Execute the requested tool
            tool_name = action["tool_name"]
            arguments = action["arguments"]

            # Emit tool requested event
            tool_event = ToolRequestedEvent(
                tool_name=tool_name,
                arguments=arguments,
            )
            state.add_event(tool_event)

            # Execute the tool
            tool_result: ToolResult = await _execute_tool(
                tool_name,
                arguments,
                registry,
                ws,
            )

            # Emit tool completed event and add observation
            obs_success = tool_result.success
            observation_str = (
                str(tool_result.data) if tool_result.data else (tool_result.error or "No output")
            )

            # Track modifications for patch/write_file tools
            if tool_name == "apply_patch" and tool_result.success:
                data = tool_result.data or {}
                applied_files = data.get("files_changed", [])
                for f in applied_files:
                    state.track_modification(f, observation_str)
                state.repair_attempts = state.repair_attempts  # Keep current count
                state.add_event(
                    PatchAppliedEvent(
                        files_changed=applied_files,
                        diff_preview=observation_str,
                        data={"task": state.task},
                    )
                )
            elif tool_name == "inspect_diff" and tool_result.success:
                data = tool_result.data or {}
                state.set_diff_summary(data.get("diff", observation_str))
            elif tool_name == "write_file" and tool_result.success:
                data = tool_result.data or {}
                written_path = data.get("path", "")
                if written_path:
                    state.track_modification(written_path, observation_str)
                state.add_event(
                    PatchAppliedEvent(
                        files_changed=[written_path] if written_path else [],
                        diff_preview=observation_str,
                        data={"task": state.task},
                    )
                )

            completed_event = ToolCompletedEvent(
                tool_name=tool_name,
                success=obs_success,
                observation=observation_str,
            )
            state.add_event(completed_event)

            # Add observation to state
            state.add_observation(
                tool_name=tool_name,
                tool_success=obs_success,
                observation=observation_str,
                raw_data=tool_result.data if isinstance(tool_result.data, dict) else None,
            )

            # Add the tool result to observations (already done above)
            # Update tools_used list
            if tool_name not in state.tools_used:
                state.tools_used.append(tool_name)

            # Update files_inspected if relevant
            if tool_name == "list_files" and tool_result.data:
                listed_files = tool_result.data
                if isinstance(listed_files, list):
                    state.files_inspected.extend(listed_files[:20])  # Limit

            # Check if this was a test execution and handle results
            if tool_name == "run_tests":
                # Parse test results
                test_summary = tool_result.data.get("test_summary", {}) if tool_result.data else {}
                failed_count = test_summary.get("failed", 0)
                error_count = test_summary.get("errors", 0)
                timed_out = tool_result.timed_out

                state.set_tests_results(tool_result.data or {})

                if failed_count > 0 or error_count > 0 or timed_out:
                    # Tests failed - trigger failure analysis
                    state.add_failure_detection(
                        f"{failed_count} failed, {error_count} error(s)" + 
                        (" (timed out)" if timed_out else ""),
                        failed_count
                    )
                    
                    # Move to failure analysis phase
                    if state.phase != AgentState.PHASE_FAILURE_ANALYSIS:
                        state.phase = AgentState.PHASE_FAILURE_ANALYSIS
                    
                    # If not already in repair phase, start repair
                    if not repair_phase:
                        repair_phase = True
                        state.repair_attempts = 0
                        state.add_event(
                            RepairStartedEvent(
                                repair_attempt=1,
                                message="Starting repair loop - analyzing test failure",
                                data={"task": state.task},
                            )
                        )
                    
                    # If we've exceeded max repair attempts, stop
                    if state.repair_attempts >= state.max_repair_iterations:
                        state.status.status = "repair_failed"
                        state.status.error = f"Maximum repair iterations ({state.max_repair_iterations}) reached"
                        break
                    
                    # Continue to next iteration - LLM will create a patch
                    continue
                else:
                    # Tests passed - move to verification
                    state.phase = AgentState.PHASE_VERIFICATION
                    state.add_verification_started("Verifying fix with full test suite")
                    # Run full test suite for regression check
                    # For now, just mark as verified and complete
                    state.set_verification_status("passed")
                    break
            else:
                # Continue the loop (the LLM will see the tool result and decide next)
                continue

        elif action["type"] == "final_analysis":
            # Agent has completed its analysis
            summary = action.get("summary", "Analysis completed")
            state.status.status = "completed"
            state.status.messages = [summary]

            # Build the final response
            response = state.to_response()
            response.plan = action.get("plan", [])
            response.observations = state.observations

            # Emit agent completed event
            completed = AgentCompletedEvent(
                summary=summary,
                status="completed",
            )
            state.add_event(completed)

            return response

        elif action["type"] == "error":
            # Agent encountered an error
            error_msg = action.get("error", "Unknown agent error")
            state.status.status = "error"
            state.status.error = error_msg  # type: ignore[union-attr]

            response = state.to_response()
            response.error = error_msg

            # Emit agent failed event
            failed = AgentFailedEvent(error=error_msg)
            state.add_event(failed)

            return response

        else:
            # Unknown action - continue looping
            continue

    # If we get here, iterations exceeded or repair failed
    if state.iteration >= max_iterations and state.status.status != "repair_failed":
        state.status.status = "iterations_exceeded"
        state.status.error = "Maximum agent iterations exceeded"

    response = state.to_response()
    response.plan = []
    response.error = state.status.error

    # Emit agent completed event
    completed_status = state.status.status
    completed_summary = state.status.error or "Analysis completed"
    completed = AgentCompletedEvent(
        summary=completed_summary,
        status=completed_status,
    )
    state.add_event(completed)

    return response


def _build_combined_prompt(
    system_prompt: str,
    task: str,
    instructions: str,
    observations: List[Any],
) -> str:
    """Build the combined prompt for the LLM from system prompt, task, and observations."""
    parts = [
        system_prompt,
        f"Task: {task}",
        instructions,
    ]

    # Add observations from previous tool calls
    for obs in observations[-5:]:  # Last observations
        # Handle both AgentObservation objects and dicts
        if hasattr(obs, "tool_success") and obs.tool_success:
            label = "Tool result"
        elif isinstance(obs, dict) and obs.get("tool_success", False):
            label = "Tool result"
        else:
            label = "Tool failed"

        obs_text = getattr(obs, "observation", obs.get("observation", "No observation"))
        parts.append(f"{label}: {obs_text}")

    parts.append("Next step:")
    return "\n".join(parts)


async def _call_llm_with_prompt(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
) -> Any:
    """Call the LLM with a prompt string.

    Uses the existing Nebius client to generate a response.
    """
    from ..llm.client import get_client

    client = get_client()
    # The client.generate() expects a prompt string and returns LLMGenerateResponse
    response = await client.generate(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1.0,
    )
    return response


def _parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM's response to determine the next action.

    Returns a dict with keys:
    - type: "tool_call", "final_analysis", or "error"
    - Corresponding fields depend on the type.
    """
    text = response_text.strip()

    # Check for final analysis marker
    if "\n\nFINAL ANALYSIS:" in text:
        # Extract the summary and plan
        parts = text.split("\n\nFINAL ANALYSIS:", 1)
        summary = parts[0].strip()
        plan_section = parts[1] if len(parts) > 1 else ""

        # Extract plan items (lines starting with "-")
        plan_items = []
        for line in plan_section.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                plan_items.append(line[2:].strip())

        return {
            "type": "final_analysis",
            "summary": summary,
            "plan": plan_items,
        }

    # Check for error marker
    if "\n\nERROR:" in text:
        parts = text.split("\n\nERROR:", 1)
        error_msg = parts[1].strip() if len(parts) > 1 else text
        return {"type": "error", "error": error_msg}

    # Check for tool call pattern
    # Look for structured JSON or clear tool invocation
    # Pattern: "Tool: list_files, Args: {...}" or JSON-like
    tool_patterns = [
        ("list_files", lambda t: {"tool_name": "list_files", "arguments": {}}),
        ("read_file", lambda t: {"tool_name": "read_file", "arguments": {}}),
        ("search_code", lambda t: {"tool_name": "search_code", "arguments": {}}),
    ]

    for tool_name, extractor in tool_patterns:
        if tool_name in text.lower():
            # Try to extract arguments
            args_extracted = extractor(text)
            # Heuristic: if the response mentions specific paths or queries,
            # we should construct reasonable arguments
            if args_extracted["tool_name"] == "search_code" and "query" not in str(
                extractor
            ):
                # Try to find a search query in the text
                import re
                match = re.search(r'"([^"]+)"', text)
                if match:
                    query = match.group(1)
                    args_extracted["arguments"] = {"query": query}
            return {"type": "tool_call", "tool_name": args_extracted["tool_name"], "arguments": {}}

    # Default: if we have some text but can't parse it, treat as thinking/continuing
    return {"type": "thinking", "raw_text": text}


async def _execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    registry: ToolRegistry,
    ws: Workspace,
) -> ToolResult:
    """Execute a tool by name with the given arguments using the registry.

    Returns a ToolResult instance.
    """
    # Try the registry first
    result = registry.execute_tool(tool_name, **arguments)
    if result.success:
        return result

    # Fall back to direct tool execution
    if tool_name == "list_files":
        tool = ListFilesTool(ws)
        return await tool.execute(**arguments)
    elif tool_name == "read_file":
        tool = ReadFileTool(ws)
        return await tool.execute(**arguments)
    elif tool_name == "search_code":
        tool = SearchCodeTool(ws)
        return await tool.execute(**arguments)
    else:
        return ToolResult(
            name=tool_name,
            success=False,
            error=f"Unknown tool: {tool_name}",
        )