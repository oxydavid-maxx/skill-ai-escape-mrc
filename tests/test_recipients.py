import json
from pathlib import Path

from ai_escape_mrc.delivery.recipients import resolve_delivery_recipients


def test_user_email_gets_operator_cc(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg = tmp_path / ".claude" / "email.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"recipient": "operator@example.com"}), encoding="utf-8")

    resolved = resolve_delivery_recipients(user_email="user@example.com")

    assert resolved.to == "user@example.com"
    assert resolved.cc == ("operator@example.com",)
    assert resolved.source == "user_payload"


def test_missing_user_falls_back_to_operator(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    cfg = tmp_path / ".claude" / "email.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps({"recipient": "operator@example.com"}), encoding="utf-8")

    resolved = resolve_delivery_recipients()

    assert resolved.to == "operator@example.com"
    assert resolved.cc == ()
    assert resolved.source == "operator_fallback"


def test_env_user_precedence(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_USER_EMAIL", "env-user@example.com")
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_OPERATOR_EMAIL", "env-operator@example.com")

    resolved = resolve_delivery_recipients()

    assert resolved.to == "env-user@example.com"
    assert resolved.cc == ("env-operator@example.com",)
    assert resolved.source == "user_payload"
