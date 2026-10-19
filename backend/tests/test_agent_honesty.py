"""Honest-status regressions: stuck runs must fail, never report success.

Covers:
- repeat-guard stop: failed when tests never passed (was falsely "completed")
- to_response(): success only for status "completed" (iterations_exceeded
  used to count as success)
- unparseable replies: corrective feedback, then an honest failure after 3
"""

from __future__ import annotations

import tempfile
from types import SimpleNamespace
from typing import Any

import pytest

import backend.app.agent.agent as agent_mod
from backend.app.agent.agent import run_agent_task
from backend.app.agent.state import AgentState


def _ok_llm(text: str, model: str = "stub-model") -> SimpleNamespace:
    return SimpleNamespace(
        success=True,
        error=None,
        usage={"total_tokens": 10},
        model=model,
        response=text,
    )


def test_to_response_success_requires_completed() -> None:
    """iterations_exceeded must not count as a successful run."""
    state = AgentState(workspace_root=".", task="t")
    state.iteration = 1

    state.status.status = "iterations_exceeded"
    assert state.to_response().success is False

    state.status.status = "completed"
    assert state.to_response().success is True


@pytest.mark.asyncio
async def test_repeat_guard_stop_is_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stuck loop that never ran tests must report failed, not completed."""

    async def _stub(prompt: str, model: Any = None, **kwargs: Any) -> Any:
        return _ok_llm(
            '{"tool": "search_code", "arguments": {"query": "utils"}}',
            model=str(model),
        )

    monkeypatch.setattr(agent_mod, "_call_llm_with_prompt", _stub)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await run_agent_task(
            workspace_root=tmpdir,
            task="add a helper",
            model="Nemotron 3 Super",
        )

    assert result.status == "failed"
    assert result.success is False
    assert "repeated" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_unparseable_replies_stop_honestly(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prose-only replies get a corrective observation, then honest failure."""

    calls: list[str] = []

    async def _stub(prompt: str, model: Any = None, **kwargs: Any) -> Any:
        calls.append(prompt)
        return _ok_llm("I should look around the repository some more.")

    monkeypatch.setattr(agent_mod, "_call_llm_with_prompt", _stub)

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await run_agent_task(
            workspace_root=tmpdir,
            task="add a helper",
            model="Nemotron 3 Super",
        )

    assert result.status == "failed"
    assert result.success is False
    assert "not valid" in (result.error or "").lower()
    # 3 attempts max — must not burn the whole 10-iteration budget.
    assert result.iteration == 3
    # The corrective observation must appear in the follow-up prompt.
    assert any("Respond with ONLY" in c for c in calls[1:])
