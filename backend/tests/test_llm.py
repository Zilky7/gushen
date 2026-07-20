import pytest

from app.services.llm import ExplanationService, LlmSafetyError, validate_explanation


def test_explanation_rejects_price_not_provided_by_engine() -> None:
    with pytest.raises(LlmSafetyError, match="untraceable"):
        validate_explanation(
            {"reason": "Breakout", "risks": [], "triggers": [], "referenced_prices": [123.45]},
            allowed_prices={120.0, 125.0},
        )


def test_explanation_service_supports_compatibility_environment_names(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    assert ExplanationService().enabled() is True


def test_explanation_rejects_untraceable_numbers_inside_text() -> None:
    with pytest.raises(LlmSafetyError, match="untraceable"):
        validate_explanation(
            {"reason": "止盈 999", "risks": [], "triggers": [], "referenced_prices": []},
            allowed_prices={100.0},
        )
