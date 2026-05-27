from ai_escape_mrc.models import ENVIRONMENT_DEFAULT_MODEL_LABEL, model_for_role, model_label


def test_model_for_role_uses_environment_default_for_all_roles():
    assert model_for_role("rc_audit") is None
    assert model_for_role("report_generation") is None
    assert model_for_role("keyword_extraction") is None
    assert model_for_role("unknown_role") is None


def test_model_label_names_environment_default():
    assert model_label(None) == ENVIRONMENT_DEFAULT_MODEL_LABEL
    assert model_label("explicit-model") == "explicit-model"
