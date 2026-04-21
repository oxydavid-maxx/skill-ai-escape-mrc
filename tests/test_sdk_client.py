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
