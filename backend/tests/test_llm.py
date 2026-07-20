import pytest

from app.services.llm import LlmSafetyError, validate_explanation


def test_explanation_rejects_price_not_provided_by_engine() -> None:
    with pytest.raises(LlmSafetyError, match="untraceable"):
        validate_explanation(
            {"reason": "Breakout", "risks": [], "triggers": [], "referenced_prices": [123.45]},
            allowed_prices={120.0, 125.0},
        )
