# CodeForge AI Agent Prompts

from __future__ import annotations

from .models import SYSTEM_PROMPT, AGENT_INSTRUCTIONS


def get_system_prompt() -> str:
    """Return the system prompt for the CodeForge AI agent."""
    return SYSTEM_PROMPT


def get_agent_instructions(task: str) -> str:
    """Return the agent instructions formatted for the current task.

    Args:
        task: The coding task the agent is analyzing.
    """
    return AGENT_INSTRUCTIONS.format(task=task)


def get_events_model() -> type:
    """Return the AgentEvent Pydantic model class."""
    return AgentEvent


def get_event_types() -> List[str]:
    """Return the list of valid agent event types."""
    return [
        "agent_started",
        "thinking",
        "tool_requested",
        "tool_completed",
        "analysis_updated",
        "agent_completed",
        "agent_failed",
    ]