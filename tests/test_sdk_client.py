"""Tests for eightd.sdk_client — the Claude Agent SDK transport."""
import asyncio
from unittest.mock import patch
import pytest


class FakeTextBlock:
    def __init__(self, text):
        self.text = text


class FakeToolUseBlock:
    def __init__(self, name, input_dict):
        self.name = name
        self.input = input_dict
        # no .text — intentionally absent to mimic the real SDK shape


class FakeAssistantMessage:
    def __init__(self, content):
        self.content = content


class FakeResultMessage:
    def __init__(self, is_error=False, usage=None):
        self.is_error = is_error
        self.usage = usage or {}
        self.structured_output = None


async def _async_iter(items):
    for x in items:
        yield x


def test_collect_messages_extracts_text():
    from eightd.sdk_client import _collect_messages
    msgs = [FakeAssistantMessage([FakeTextBlock("hello")]), FakeResultMessage()]
    result = asyncio.run(_collect_messages(_async_iter(msgs)))
    assert result["text"] == "hello"
    assert result["structured"] is None
    assert result["is_error"] is False


def test_collect_messages_extracts_structured_output():
    from eightd.sdk_client import _collect_messages
    msgs = [
        FakeAssistantMessage([FakeToolUseBlock("StructuredOutput", {"key": "value"})]),
        FakeResultMessage(),
    ]
    result = asyncio.run(_collect_messages(_async_iter(msgs)))
    assert result["structured"] == {"key": "value"}
    assert result["text"] == ""


def test_collect_messages_concatenates_multiple_text_blocks():
    from eightd.sdk_client import _collect_messages
    msgs = [
        FakeAssistantMessage([FakeTextBlock("part1"), FakeTextBlock("part2")]),
        FakeResultMessage(),
    ]
    result = asyncio.run(_collect_messages(_async_iter(msgs)))
    assert result["text"] == "part1\npart2"


def test_collect_messages_surfaces_is_error():
    from eightd.sdk_client import _collect_messages
    msgs = [FakeResultMessage(is_error=True)]
    result = asyncio.run(_collect_messages(_async_iter(msgs)))
    assert result["is_error"] is True


def test_sdk_query_plain_text():
    """_sdk_query returns dict with text when no schema."""
    from eightd import sdk_client
    msgs = [FakeAssistantMessage([FakeTextBlock("OK")]), FakeResultMessage()]

    def fake_query(*, prompt, options=None, **_):
        return _async_iter(msgs)

    with patch("eightd.sdk_client.query", side_effect=fake_query):
        result = asyncio.run(sdk_client._sdk_query(
            prompt="say OK", system_prompt="be brief", schema=None, timeout_sec=10, max_turns=3,
        ))
    assert result["text"] == "OK"


def test_sdk_query_passes_env_and_schema():
    """_sdk_query must construct ClaudeAgentOptions with SDK env + schema."""
    from eightd import sdk_client
    captured = {}

    def fake_query(*, prompt, options=None, **_):
        captured["prompt"] = prompt
        captured["options"] = options
        return _async_iter([FakeResultMessage()])

    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    with patch("eightd.sdk_client.query", side_effect=fake_query):
        asyncio.run(sdk_client._sdk_query(
            prompt="hi", system_prompt="s", schema=schema, timeout_sec=10, max_turns=3,
        ))
    opts = captured["options"]
    assert opts.env == {"CLAUDECODE": "", "CLAUDE_SDK_CALL": "1"}
    assert opts.setting_sources is None
    assert opts.output_format == {"type": "json_schema", "schema": schema}
    assert opts.system_prompt == "s"
    assert opts.max_turns == 3


def test_sdk_query_times_out():
    """_sdk_query raises TimeoutError when query exceeds timeout_sec."""
    from eightd import sdk_client

    async def slow_iter():
        await asyncio.sleep(2.0)
        yield FakeResultMessage()

    def fake_query(**kw):
        return slow_iter()

    with patch("eightd.sdk_client.query", side_effect=fake_query):
        with pytest.raises(asyncio.TimeoutError):
            asyncio.run(sdk_client._sdk_query(
                prompt="p", system_prompt="s", schema=None, timeout_sec=0.1, max_turns=3,
            ))
