from ai_escape_mrc.models import ENVIRONMENT_DEFAULT_MODEL_LABEL, model_for_role, model_label


def test_model_for_role_uses_environment_default_for_all_roles():
    assert model_for_role("rc_audit") is None
    assert model_for_role("report_generation") is None
    assert model_for_role("keyword_extraction") is None
    assert model_for_role("unknown_role") is None


def test_fast_model_routes_non_audit_roles_when_env_set(monkeypatch):
    monkeypatch.setenv("CLAUDE_AI_ESCAPE_MRC_FAST_MODEL", "claude-sonnet-4-6")
    # Quality-bearing roles stay on the strong default model.
    assert model_for_role("rc_audit") is None
    assert model_for_role("prevention_audit") is None
    assert model_for_role("report_generation") is None
    # Everything else routes to the fast model.
    for role in ("keyword_extraction", "meta_categorization", "is_isnt_extraction",
                 "why_q1_trc_nc", "corrective_q1", "proof_of_action", "phase_9_write_plan"):
        assert model_for_role(role) == "claude-sonnet-4-6"


def test_fast_model_unset_keeps_all_default(monkeypatch):
    monkeypatch.delenv("CLAUDE_AI_ESCAPE_MRC_FAST_MODEL", raising=False)
    assert model_for_role("keyword_extraction") is None
    assert model_for_role("rc_audit") is None


def test_model_label_names_environment_default():
    assert model_label(None) == ENVIRONMENT_DEFAULT_MODEL_LABEL
    assert model_label("explicit-model") == "explicit-model"
