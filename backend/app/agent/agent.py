# CodeForge AI Agent Orchestration
from __future__ import annotations

import asyncio
import inspect
import json
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from .models import (
    AgentRequest,
    AgentResponse,
    AgentStatus,
    ToolCall,
    ToolResult,
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
from ..tools.base import ToolResult as BaseToolResult
from ..tools.repository_tools import ListFilesTool, ReadFileTool, SearchCodeTool
from ..tools.modification_tools import ApplyPatchTool, InspectDiffTool, WriteFileTool
from ..tools.execution_tools import RunTestsTool


MAX_DEFAULT_ITERATIONS = 10


def _usage_total_tokens(usage: Optional[Dict[str, Any]]) -> int:
    """Extract total token count from a provider usage payload, if present."""
    if not isinstance(usage, dict):
        return 0
    total = usage.get("total_tokens", 0)
    try:
        return int(total)
    except (TypeError, ValueError):
        return 0


def _finalize_response(
    response: AgentResponse,
    state: AgentState,
    started_at: float,
    tokens_used: int,
    model: str = "",
) -> AgentResponse:
    """Attach real run metrics (duration, tokens, model) to a response."""
    response.duration_seconds = round(time.monotonic() - started_at, 3)
    response.tokens_used = tokens_used
    response.model = model or response.model
    response.max_iterations = state.max_iterations
    return response


async def _run_single_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    registry: ToolRegistry,
    ws: Workspace,
    state: AgentState,
    repair_phase: bool,
) -> Tuple[str, bool]:
    """Execute one tool call with full bookkeeping (events, observations, repair).

    Returns (signal, repair_phase); signal is "next" to keep the agent loop
    going or "break" to terminate it. Shared by single and batched tool calls.
    """
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
        # Parse test results from the tool's data payload
        data = tool_result.data if isinstance(tool_result.data, dict) else {}
        test_summary = data.get("test_summary", {}) or {}
        failed_count = test_summary.get("failed", 0)
        error_count = test_summary.get("errors", 0)
        timed_out = bool(data.get("timed_out", False))

        state.set_tests_results(data)

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
            else:
                # A subsequent failing run consumes one repair attempt.
                state.repair_attempts += 1
                state.add_event(
                    RepairAttemptEvent(
                        repair_attempt=state.repair_attempts,
                        message=(
                            f"Tests still failing after repair attempt "
                            f"{state.repair_attempts}"
                        ),
                        data={"task": state.task},
                    )
                )

            # If we've exceeded max repair attempts, stop
            if state.repair_attempts >= state.max_repair_iterations:
                state.status.status = "repair_failed"
                state.status.error = f"Maximum repair iterations ({state.max_repair_iterations}) reached"
                return "break", repair_phase

            # Continue to next iteration - LLM will create a patch
            return "next", repair_phase
        else:
            # Tests passed - move to verification
            state.phase = AgentState.PHASE_VERIFICATION
            state.add_verification_started("Verifying fix with full test suite")
            state.set_verification_status("passed")
            # Persist a real plan derived from what actually happened,
            # so the completed run is never stored with an empty plan.
            if not state.plan:
                plan_steps = [
                    "Inspected repository files",
                    "Ran the test suite and detected failures",
                    "Diagnosed the failing test and applied a patch",
                ]
                if state.files_changed:
                    plan_steps.append(
                        f"Modified: {', '.join(state.files_changed)}"
                    )
                plan_steps.append("Re-ran tests — all passed")
                state.set_plan(plan_steps)
            state.status.status = "completed"
            state.status.messages = ["All tests passed — verification complete."]
            return "break", repair_phase
    else:
        # Continue the loop (the LLM will see the tool result and decide next)
        return "next", repair_phase


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

    started_at = time.monotonic()
    total_tokens = 0
    model_name = ""

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
    run_tests_tool = RunTestsTool(ws.root)
    registry.register(list_tool)
    registry.register(read_tool)
    registry.register(search_tool)
    registry.register(patch_tool)
    registry.register(inspect_diff_tool)
    registry.register(write_file_tool)
    registry.register(run_tests_tool)

    # Prepare initial system prompt
    system_prompt = get_system_prompt()
    agent_instructions = get_agent_instructions(task)

    # Main agent loop
    repair_phase = False
    # Repeat guard: an identical non-test tool call issued twice in a row is
    # skipped instead of re-executed, so stuck loops cannot burn the budget.
    last_call_key: Optional[str] = None
    consecutive_repeats = 0
    # Previous raw LLM responses, fed back into the prompt so the model has
    # continuity across iterations (it can see what it already decided).
    previous_responses: List[str] = []
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

        # Call the LLM (using the existing Nebius client)
        # Build a combined prompt from the system prompt, task, and observations
        combined_prompt = _build_combined_prompt(
            system_prompt=system_prompt,
            task=task,
            instructions=current_instructions,
            observations=state.observations,
            previous_responses=previous_responses,
            failure_history=state.failure_history,
            iteration=state.iteration,
            max_iterations=max_iterations,
        )

        # Generate the next step from the LLM
        llm_response = await _call_llm_with_prompt(
            prompt=combined_prompt,
            model=None,
            temperature=0.3,
            max_tokens=2000,
        )

        # Fail fast on provider errors (missing API key, HTTP failure, ...)
        if not llm_response.success:
            error_msg = llm_response.error or "LLM request failed"
            state.status.status = "error"
            state.status.error = error_msg  # type: ignore[union-attr]
            response = state.to_response()
            response.error = error_msg
            state.add_event(AgentFailedEvent(error=error_msg))
            return _finalize_response(response, state, started_at, total_tokens, model_name)

        total_tokens += _usage_total_tokens(llm_response.usage)
        model_name = llm_response.model or model_name
        raw_text = (llm_response.response or "").strip()
        if raw_text:
            previous_responses.append(raw_text[:2000])

        # Parse the LLM response to determine the next action
        # The LLM should respond with either a tool call or a final analysis
        action = _parse_llm_response(raw_text)

        if action["type"] in ("tool_call", "tool_calls"):
            # Normalize to a batch: a lone tool call is a batch of one.
            if action["type"] == "tool_call":
                pending_calls = [
                    {
                        "tool_name": action["tool_name"],
                        "arguments": action["arguments"] or {},
                    }
                ]
            else:
                pending_calls = [
                    {
                        "tool_name": call["tool_name"],
                        "arguments": call["arguments"] or {},
                    }
                    for call in action["calls"]
                ]

            # Repeat guard: an identical non-test call twice in a row means the
            # model is stuck — skip re-execution and tell it to move on.
            # run_tests is exempt: re-running tests after a patch is the repair loop.
            if len(pending_calls) == 1:
                only = pending_calls[0]
                key = _call_key(only["tool_name"], only["arguments"])
                if only["tool_name"] != "run_tests" and key == last_call_key:
                    consecutive_repeats += 1
                    if consecutive_repeats >= 2:
                        # Third identical call in a row: stop honestly with a
                        # summary built from real observations, not an error.
                        bits = []
                        if state.tools_used:
                            bits.append(f"Tools used: {', '.join(state.tools_used)}.")
                        if state.files_changed:
                            bits.append(
                                f"Files changed: {', '.join(state.files_changed)}."
                            )
                        if state.files_inspected:
                            bits.append(
                                f"Files inspected: {len(state.files_inspected)}."
                            )
                        repeat_summary = (
                            f"Stopped: the agent repeated '{only['tool_name']}' "
                            f"without new information. " + " ".join(bits)
                        ).strip()
                        state.status.status = "completed"
                        state.status.messages = [repeat_summary or "Exploration complete."]
                        if state.files_changed and not state.plan:
                            state.set_plan(
                                [f"Modified: {f}" for f in state.files_changed]
                            )
                        response = state.to_response()
                        response = _finalize_response(
                            response, state, started_at, total_tokens, model_name
                        )
                        state.add_event(
                            AgentCompletedEvent(
                                summary=state.status.messages[0], status="completed"
                            )
                        )
                        return response
                    state.add_observation(
                        tool_name=only["tool_name"],
                        tool_success=True,
                        observation=(
                            "Skipped: this exact call was already executed just "
                            "before — its result is recorded above. Do NOT call "
                            "it again; finalize with the final JSON or choose a "
                            "different step."
                        ),
                    )
                    continue
                consecutive_repeats = 0
                last_call_key = key

            stop_outer = False
            for pending in pending_calls:
                if pending["tool_name"] != "run_tests":
                    last_call_key = _call_key(
                        pending["tool_name"], pending["arguments"]
                    )
                signal, repair_phase = await _run_single_tool(
                    pending["tool_name"],
                    pending["arguments"],
                    registry,
                    ws,
                    state,
                    repair_phase,
                )
                if signal == "break":
                    stop_outer = True
                    break
            if stop_outer:
                break
            consecutive_repeats = 0
            continue

        elif action["type"] == "final_analysis":
            # Agent has completed its analysis
            summary = action.get("summary", "Analysis completed")
            state.status.status = "completed"
            state.status.messages = [summary]

            # Register the plan on state so the plan_created event fires and
            # the persisted run carries it.
            plan_list = _normalize_plan(action.get("plan", []))
            if plan_list:
                state.set_plan(plan_list)

            # Build the final response
            response = state.to_response()
            response.observations = state.observations
            response = _finalize_response(response, state, started_at, total_tokens, model_name)

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
            response = _finalize_response(response, state, started_at, total_tokens, model_name)

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

    # to_response() already carries state.plan — do not blank it here (the
    # tests-passed break falls through to this block with status completed).
    response = state.to_response()
    response.error = state.status.error
    response = _finalize_response(response, state, started_at, total_tokens, model_name)

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
    previous_responses: Optional[List[str]] = None,
    failure_history: Optional[List[Dict[str, Any]]] = None,
    iteration: int = 1,
    max_iterations: int = MAX_DEFAULT_ITERATIONS,
) -> str:
    """Build the combined prompt for the LLM from system prompt, task, observations,
    and the model's own previous responses (for cross-iteration continuity)."""
    parts = [
        system_prompt,
        f"Task: {task}",
        instructions,
        f"Iteration {iteration} of at most {max_iterations}.",
    ]

    # The model's own previous decisions, so it can build on them instead of
    # re-issuing the same tool calls.
    if previous_responses:
        parts.append("Your previous responses (most recent last):")
        for prior in previous_responses[-3:]:
            parts.append(f"[previous response]\n{prior}")

    # Add observations from previous tool calls
    for obs in observations[-6:]:  # Last observations
        # Handle both AgentObservation objects and dicts
        if hasattr(obs, "tool_success") and obs.tool_success:
            label = "Tool result"
        elif isinstance(obs, dict) and obs.get("tool_success", False):
            label = "Tool result"
        else:
            label = "Tool failed"

        if isinstance(obs, dict):
            obs_text = obs.get("observation", "No observation")
        else:
            obs_text = getattr(obs, "observation", None) or "No observation"
        parts.append(f"{label}: {obs_text}")

    # Failed patches: tell the model exactly what to avoid repeating.
    if failure_history:
        parts.append(
            "Previous failed patches (do NOT repeat these; re-read the file first):\n"
            + json.dumps(failure_history[-3:], indent=2)
        )

    parts.append(
        "Next step: respond with JSON only — one tool call per line "
        '{"tool": "...", "arguments": {...}} (several independent calls may be '
        "batched, one per line, and all will run in order) or the final answer "
        '{"final": {"summary": "...", "plan": ["..."]}}. '
        "Never repeat a tool call already in the observations — its result is "
        "recorded above. Finish as soon as the task requirements are met; when "
        "files were modified the final plan MUST list each modified file."
    )
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


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Find the first parseable JSON object in a free-form LLM response."""
    import re

    candidates: List[str] = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    candidates.extend(
        text[idx:] for idx in (i for i, ch in enumerate(text) if ch == "{")
    )
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            obj, _ = decoder.raw_decode(candidate.lstrip())
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def _contains(container: Any, target: Dict[str, Any]) -> bool:
    """True when target dict occurs as a nested value inside container."""
    if container == target:
        return True
    if isinstance(container, dict):
        return any(_contains(v, target) for v in container.values())
    if isinstance(container, list):
        return any(_contains(v, target) for v in container)
    return False


def _extract_all_json_objects(text: str) -> List[Dict[str, Any]]:
    """Find every parseable top-level JSON object in a response, in order.

    The model often emits several one-per-line tool calls in a single turn;
    this collects all of them so the whole batch can be executed at once
    instead of wasting one iteration per call. Nested inner objects (e.g. an
    arguments dict also parseable on its own) are dropped — only the
    outermost objects are returned.
    """
    import re

    found: List[Dict[str, Any]] = []
    seen: set = set()
    candidates: List[str] = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    # One JSON object per line (the model's preferred batch style).
    candidates.extend(line.strip() for line in text.splitlines())
    # Fallback: every '{' position.
    candidates.extend(text[idx:] for idx, ch in enumerate(text) if ch == "{")
    decoder = json.JSONDecoder()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate.startswith("{"):
            continue
        try:
            obj, _ = decoder.raw_decode(candidate)
        except ValueError:
            continue
        if isinstance(obj, dict):
            key = json.dumps(obj, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                found.append(obj)
    # Drop objects nested inside another collected object.
    top_level = [
        obj
        for obj in found
        if not any(other is not obj and _contains(other, obj) for other in found)
    ]
    return top_level


def _as_tool_call(obj: Dict[str, Any]) -> Optional[tuple]:
    """Validate a dict as a tool call; return (tool_name, arguments) or None.

    A missing arguments object is treated as {} so no-arg tools (run_tests,
    inspect_diff) work when the model omits the key — execution errors are
    reported back as tool observations rather than burning an iteration.
    """
    name = obj.get("tool") or obj.get("tool_name")
    args = obj.get("arguments", obj.get("args", obj.get("input", {})))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return None
    if isinstance(name, str) and name in _KNOWN_TOOLS and isinstance(args, dict):
        return name, args
    return None


def _call_key(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Stable identity for a tool call, used for repeat detection."""
    try:
        return f"{tool_name}:{json.dumps(arguments, sort_keys=True, default=str)}"
    except (TypeError, ValueError):
        return f"{tool_name}:{str(arguments)}"


_KNOWN_TOOLS = (
    "list_files",
    "read_file",
    "search_code",
    "apply_patch",
    "inspect_diff",
    "write_file",
    "run_tests",
)
# Tools whose execution requires these arguments — a call without them
# would only produce a TypeError, so treat the mention as prose instead.
_TOOLS_REQUIRING_ARGS = {
    "read_file": "path",
    "search_code": "query",
    "write_file": "path",
    "apply_patch": "patch",
}


def _normalize_plan(items: Any) -> List[str]:
    plan: List[str] = []
    if isinstance(items, str):
        items = [items]
    if isinstance(items, list):
        for item in items:
            line = str(item).strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                plan.append(line)
    return plan


def _parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM's response to determine the next action.

    Returns a dict with keys:
    - type: "tool_call", "tool_calls" (batch), "final_analysis", "error", or "thinking"
    - Corresponding fields depend on the type.

    The agent prompt requires a single JSON object per turn
    ({"tool": name, "arguments": {...}} or {"final": {...}}), but the
    legacy plain-text markers are still accepted so either style works.
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

    # Batched tool calls first: the model may emit several one-per-line JSON
    # tool calls in a single turn. Execute the whole batch in one iteration
    # instead of running (and re-requesting) one call per iteration.
    batch: List[Dict[str, Any]] = []
    for candidate in _extract_all_json_objects(text):
        # A final answer takes precedence over any tool calls in the text.
        final = candidate.get("final")
        if isinstance(final, dict):
            return {
                "type": "final_analysis",
                "summary": str(final.get("summary") or "Analysis completed"),
                "plan": _normalize_plan(final.get("plan")),
            }
        if candidate.get("type") in ("final", "final_analysis"):
            return {
                "type": "final_analysis",
                "summary": str(candidate.get("summary") or "Analysis completed"),
                "plan": _normalize_plan(candidate.get("plan")),
            }
        parsed = _as_tool_call(candidate)
        if parsed is not None:
            entry = {"tool_name": parsed[0], "arguments": parsed[1]}
            if entry not in batch:
                batch.append(entry)
    if len(batch) >= 2:
        return {"type": "tool_calls", "calls": batch}

    # Preferred: structured JSON response — tool call or final answer
    obj = _extract_json_object(text)
    if obj is not None:
        final = obj.get("final")
        if isinstance(final, dict):
            return {
                "type": "final_analysis",
                "summary": str(final.get("summary") or "Analysis completed"),
                "plan": _normalize_plan(final.get("plan")),
            }
        if obj.get("type") in ("final", "final_analysis"):
            return {
                "type": "final_analysis",
                "summary": str(obj.get("summary") or "Analysis completed"),
                "plan": _normalize_plan(obj.get("plan")),
            }
        if isinstance(obj.get("error"), str):
            return {"type": "error", "error": obj["error"]}

        name = obj.get("tool") or obj.get("tool_name")
        args = obj.get("arguments", obj.get("args", obj.get("input")))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except ValueError:
                args = None
        if isinstance(name, str) and name in _KNOWN_TOOLS and isinstance(args, dict):
            return {"type": "tool_call", "tool_name": name, "arguments": args}

    # Legacy fallback: prose that mentions a known tool — only treat it as a
    # call when we can also recover its required arguments from JSON-ish text.
    lowered = text.lower()
    for tool_name in _KNOWN_TOOLS:
        if tool_name not in lowered:
            continue
        arguments: Dict[str, Any] = {}
        inner = _extract_json_object(text)
        if isinstance(inner, dict):
            inner_name = inner.get("tool") or inner.get("tool_name")
            inner_args = inner.get("arguments", inner.get("args"))
            if inner_name == tool_name and isinstance(inner_args, dict):
                arguments = inner_args
        required = _TOOLS_REQUIRING_ARGS.get(tool_name)
        if required and required not in arguments:
            import re

            match = re.search(rf'"{required}"\s*:\s*"([^"]+)"', text)
            if match:
                arguments[required] = match.group(1)
        if required and required not in arguments:
            continue  # prose mention without usable arguments
        return {"type": "tool_call", "tool_name": tool_name, "arguments": arguments}

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
    tool = registry.get(tool_name)
    if tool is not None:
        try:
            res = tool.execute(**arguments)
            if inspect.isawaitable(res):
                res = await res
            if isinstance(res, BaseToolResult):
                return ToolResult(
                    tool_name=tool_name,
                    success=res.success,
                    data=res.data,
                    error=res.error,
                )
            if isinstance(res, ToolResult):
                return res
            if isinstance(res, dict):
                return ToolResult(
                    tool_name=tool_name,
                    success=res.get("success", False),
                    data=res,
                    error=res.get("error"),
                )
            return ToolResult(tool_name=tool_name, success=True, data=res)
        except Exception as exc:
            return ToolResult(tool_name=tool_name, success=False, error=str(exc))

    # Fall back to direct tool execution
    if tool_name == "list_files":
        tool_inst = ListFilesTool(ws)
        return await tool_inst.execute(**arguments)
    elif tool_name == "read_file":
        tool_inst = ReadFileTool(ws)
        return await tool_inst.execute(**arguments)
    elif tool_name == "search_code":
        tool_inst = SearchCodeTool(ws)
        return await tool_inst.execute(**arguments)
    elif tool_name == "run_tests":
        tool_inst = RunTestsTool(ws.root)
        res = tool_inst.execute(**arguments)
        if inspect.isawaitable(res):
            res = await res
        if isinstance(res, BaseToolResult):
            return ToolResult(
                tool_name=tool_name,
                success=res.success,
                data=res.data,
                error=res.error,
            )
        if isinstance(res, dict):
            return ToolResult(tool_name=tool_name, success=res.get("success", False), data=res, error=res.get("error"))
        if isinstance(res, ToolResult):
            return res
        return ToolResult(tool_name=tool_name, success=True, data=res)
    else:
        return ToolResult(
            tool_name=tool_name,
            success=False,
            error=f"Unknown tool: {tool_name}",
        )