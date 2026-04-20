import json
import time
from unittest.mock import patch, MagicMock
import pytest

from eightd.models import (
    get_models,
    model_for_role,
    _latest_in_tier,
    _version_tuple,
    FALLBACK_MODELS,
)


def test_version_tuple_parses_basic():
    assert _version_tuple("claude-opus-4-6") == (4, 6, 0)
    assert _version_tuple("claude-opus-4-7") == (4, 7, 0)
    assert _version_tuple("claude-haiku-4-5-20251001") == (4, 5, 20251001)


def test_version_tuple_no_version_returns_zeros():
    assert _version_tuple("random-name") == (0, 0, 0)


def test_latest_in_tier_picks_highest():
    fake_models = [
        MagicMock(id="claude-opus-4-6"),
        MagicMock(id="claude-opus-4-7"),
        MagicMock(id="claude-sonnet-4-6"),
    ]
    assert _latest_in_tier(fake_models, "opus") == "claude-opus-4-7"


def test_latest_in_tier_fallback_when_empty():
    assert _latest_in_tier([], "opus") == FALLBACK_MODELS["opus"]


def test_model_for_role_dispatches_by_tier():
    with patch("eightd.models.get_models") as mock_get:
        mock_get.return_value = {
            "opus": "claude-opus-4-7",
            "sonnet": "claude-sonnet-4-7",
            "haiku": "claude-haiku-4-5",
        }
        assert model_for_role("rc_audit") == "claude-opus-4-7"
        assert model_for_role("report_generation") == "claude-sonnet-4-7"
        assert model_for_role("keyword_extraction") == "claude-haiku-4-5"


def test_model_for_role_unknown_defaults_sonnet():
    with patch("eightd.models.get_models") as mock_get:
        mock_get.return_value = {
            "opus": "a", "sonnet": "b", "haiku": "c",
        }
        assert model_for_role("unknown_role") == "b"


def test_get_models_uses_cache_when_fresh(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "timestamp": time.time() - 3600,
        "models": {"opus": "cached-opus", "sonnet": "cached-sonnet", "haiku": "cached-haiku"},
    }))
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    assert get_models()["opus"] == "cached-opus"


def test_get_models_refreshes_when_stale(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    cache.write_text(json.dumps({
        "timestamp": time.time() - 25 * 3600,
        "models": {"opus": "stale", "sonnet": "stale", "haiku": "stale"},
    }))
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    with patch("eightd.models.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_client.models.list.return_value.data = [
            MagicMock(id="claude-opus-4-8"),
            MagicMock(id="claude-sonnet-4-8"),
            MagicMock(id="claude-haiku-4-6"),
        ]
        mock_anthropic.return_value = mock_client
        result = get_models()
        assert result["opus"] == "claude-opus-4-8"


def test_get_models_falls_back_when_api_fails(tmp_path, monkeypatch):
    cache = tmp_path / "cache.json"
    monkeypatch.setattr("eightd.models.CACHE_PATH", cache)
    with patch("eightd.models.Anthropic") as mock_anthropic:
        mock_anthropic.side_effect = Exception("API down")
        assert get_models() == FALLBACK_MODELS
