"""Recipient resolution for AI Escape MRC delivery."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class DeliveryRecipients:
    """Resolved email delivery target."""

    to: str
    cc: tuple[str, ...] = ()
    source: str = "operator_fallback"

    def display(self) -> str:
        cc = f"; cc={';'.join(self.cc)}" if self.cc else ""
        return f"to={self.to}{cc}; source={self.source}"

    def as_gate_fields(self) -> dict:
        return {
            "recipient_to": self.to,
            "recipient_cc": list(self.cc),
            "recipient_source": self.source,
        }


def resolve_delivery_recipients(
    *,
    user_email: str | None = None,
    operator_email: str | None = None,
) -> DeliveryRecipients:
    """Resolve requester/operator delivery policy.

    User precedence:
      explicit argument -> CLAUDE_AI_ESCAPE_MRC_USER_EMAIL.

    Operator precedence:
      explicit argument -> ~/.claude/email.json recipient ->
      CLAUDE_AI_ESCAPE_MRC_OPERATOR_EMAIL -> CLAUDE_AI_ESCAPE_MRC_EMAIL.
    """
    user = _first_valid_email(
        user_email,
        os.environ.get("CLAUDE_AI_ESCAPE_MRC_USER_EMAIL"),
    )
    operator = _first_valid_email(
        operator_email,
        _email_json_recipient(),
        os.environ.get("CLAUDE_AI_ESCAPE_MRC_OPERATOR_EMAIL"),
        os.environ.get("CLAUDE_AI_ESCAPE_MRC_EMAIL"),
    )

    if user:
        cc = (operator,) if operator and operator.lower() != user.lower() else ()
        return DeliveryRecipients(to=user, cc=cc, source="user_payload")

    if operator:
        return DeliveryRecipients(to=operator, source="operator_fallback")

    return DeliveryRecipients(to="", source="missing")


def _first_valid_email(*candidates: str | None) -> str:
    for candidate in candidates:
        value = (candidate or "").strip()
        if value and _EMAIL_RE.match(value):
            return value
    return ""


def _email_json_recipient() -> str | None:
    cfg_path = Path.home() / ".claude" / "email.json"
    if not cfg_path.exists():
        return None
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data.get("recipient")
