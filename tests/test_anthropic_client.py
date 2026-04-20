import json
from unittest.mock import patch, MagicMock
import pytest

from eightd.anthropic_client import _extract_json, call_claude, websearch


def test_extract_json_plain():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_from_fenced_code_block():
    text = 'Some preamble\n```json\n{"x": 2}\n```\nafter'
    assert _extract_json(text) == {"x": 2}


def test_extract_json_from_fenced_array():
    text = '```json\n[1, 2, 3]\n```'
    assert _extract_json(text) == [1, 2, 3]


def test_extract_json_no_fence_language():
    text = '```\n{"y": 3}\n```'
    assert _extract_json(text) == {"y": 3}


def test_extract_json_embedded_in_prose():
    text = 'Here is the result:\n{"a": 1, "b": [2, 3]}\nThanks!'
    assert _extract_json(text) == {"a": 1, "b": [2, 3]}


def test_extract_json_array_embedded_in_prose():
    text = 'The categories are:\n["workflow-orchestration", "state-machines"]\nas you requested.'
    assert _extract_json(text) == ["workflow-orchestration", "state-machines"]


def test_extract_json_nested_with_quoted_braces():
    text = '{"message": "She said \\"hi {world}\\"", "count": 2}'
    assert _extract_json(text) == {"message": 'She said "hi {world}"', "count": 2}


def test_extract_json_preamble_and_postamble():
    text = 'Sure! Here is the JSON:\n\n```json\n{"categories": ["a", "b", "c"], "domains": ["x", "y", "z"]}\n```\n\nLet me know if you need anything else.'
    got = _extract_json(text)
    assert got["categories"] == ["a", "b", "c"]
    assert got["domains"] == ["x", "y", "z"]


def test_extract_json_empty_raises():
    import json as _json
    import pytest as _pytest
    with _pytest.raises(_json.JSONDecodeError):
        _extract_json("")


def test_extract_json_no_json_raises():
    import json as _json
    import pytest as _pytest
    with _pytest.raises(_json.JSONDecodeError):
        _extract_json("just some prose with no json at all")


def test_call_claude_returns_text():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="hello")]
        mock_client.messages.create.return_value = mock_resp
        assert call_claude("m", "sys", "usr") == "hello"


def test_call_claude_parses_json():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text='{"z": 4}')]
        mock_client.messages.create.return_value = mock_resp
        assert call_claude("m", "sys", "usr", parse_json=True) == {"z": 4}


def test_websearch_returns_structured_result():
    with patch("eightd.anthropic_client._client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="finding 1")]
        mock_client.messages.create.return_value = mock_resp
        result = websearch("test query")
        assert result["query"] == "test query"
        assert "results" in result
        assert "timestamp" in result
