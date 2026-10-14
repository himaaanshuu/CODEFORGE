"""Tests for batched tool-call parsing and the repeat-guard helpers."""

from __future__ import annotations

from backend.app.agent.agent import (
    _as_tool_call,
    _call_key,
    _extract_all_json_objects,
    _parse_llm_response,
)

BATCH_RESPONSE = """{"tool": "list_files", "arguments": {"path": "backend"}}
{"tool": "list_files", "arguments": {"path": "frontend"}}
{"tool": "list_files", "arguments": {"path": "frontend/src"}}
"""


def test_extract_all_json_objects_batch() -> None:
    objs = _extract_all_json_objects(BATCH_RESPONSE)
    assert len(objs) == 3
    assert objs[0]["arguments"]["path"] == "backend"
    assert objs[2]["arguments"]["path"] == "frontend/src"


def test_extract_all_json_objects_dedupes() -> None:
    text = '{"tool": "read_file", "arguments": {"path": "a.txt"}}\n' * 2
    objs = _extract_all_json_objects(text)
    assert len(objs) == 1


def test_parse_batch_returns_tool_calls() -> None:
    action = _parse_llm_response(BATCH_RESPONSE)
    assert action["type"] == "tool_calls"
    assert len(action["calls"]) == 3
    assert action["calls"][1] == {
        "tool_name": "list_files",
        "arguments": {"path": "frontend"},
    }


def test_parse_single_still_tool_call() -> None:
    action = _parse_llm_response('{"tool": "read_file", "arguments": {"path": "x.py"}}')
    assert action["type"] == "tool_call"
    assert action["tool_name"] == "read_file"


def test_parse_final_unaffected_by_batch_logic() -> None:
    action = _parse_llm_response(
        '{"final": {"summary": "done", "plan": ["step one"]}}'
    )
    assert action["type"] == "final_analysis"
    assert action["plan"] == ["step one"]


def test_batch_with_trailing_prose() -> None:
    text = BATCH_RESPONSE + "\nI'll explore these directories next.\n"
    action = _parse_llm_response(text)
    assert action["type"] == "tool_calls"
    assert len(action["calls"]) == 3


def test_batch_skips_unknown_tools() -> None:
    text = (
        '{"tool": "list_files", "arguments": {"path": "."}}\n'
        '{"tool": "hack_the_planet", "arguments": {}}\n'
        '{"tool": "read_file", "arguments": {"path": "README.md"}}\n'
    )
    action = _parse_llm_response(text)
    assert action["type"] == "tool_calls"
    assert [c["tool_name"] for c in action["calls"]] == ["list_files", "read_file"]


def test_as_tool_call_missing_args_defaults() -> None:
    assert _as_tool_call({"tool": "run_tests"}) == ("run_tests", {})
    assert _as_tool_call({"tool": "inspect_diff"}) == ("inspect_diff", {})


def test_as_tool_call_rejects_unknown() -> None:
    assert _as_tool_call({"tool": "nope", "arguments": {}}) is None
    assert _as_tool_call({"nonsense": True}) is None


def test_call_key_stable() -> None:
    a = _call_key("read_file", {"path": "x.py"})
    b = _call_key("read_file", {"path": "x.py"})
    c = _call_key("read_file", {"path": "y.py"})
    assert a == b
    assert a != c
