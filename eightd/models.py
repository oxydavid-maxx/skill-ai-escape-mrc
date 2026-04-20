"""Runtime model selection with tier dispatch and 24h cache."""
import json
import re
import time
from pathlib import Path
from anthropic import Anthropic

CACHE_PATH = Path(__file__).parent.parent / ".anthropic-models-cache.json"
CACHE_TTL_SECONDS = 24 * 3600

FALLBACK_MODELS = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

TIER_ROLES = {
    "opus": [
        "why_analysis", "rc_audit", "prevention_audit", "closure_audit",
        "corrective_action", "prevention_action", "proof_of_action",
    ],
    "sonnet": [
        "meta_categorization", "report_generation", "is_isnt_extraction",
    ],
    "haiku": [
        "keyword_extraction", "simple_classification",
    ],
}


def get_models() -> dict[str, str]:
    """Return {tier: model_id} dict. Uses 24h cache, falls back on API failure."""
    if CACHE_PATH.exists():
        try:
            cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            if time.time() - cache["timestamp"] < CACHE_TTL_SECONDS:
                return cache["models"]
        except Exception:
            pass

    try:
        client = Anthropic()
        all_models = list(client.models.list(limit=100).data)
        selected = {
            tier: _latest_in_tier(all_models, tier)
            for tier in ["opus", "sonnet", "haiku"]
        }
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps({"timestamp": time.time(), "models": selected}),
            encoding="utf-8",
        )
        return selected
    except Exception as e:
        print(f"[WARN] model discovery failed ({e}); using fallback", flush=True)
        return FALLBACK_MODELS


def _latest_in_tier(models: list, tier: str) -> str:
    candidates = [m.id for m in models if tier in m.id.lower()]
    return max(candidates, key=_version_tuple) if candidates else FALLBACK_MODELS[tier]


def _version_tuple(model_id: str) -> tuple:
    m = re.search(r"(\d+)-(\d+)(?:-(\d+))?", model_id)
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    return (0, 0, 0)


def model_for_role(role: str) -> str:
    models = get_models()
    for tier, roles in TIER_ROLES.items():
        if role in roles:
            return models[tier]
    return models["sonnet"]
