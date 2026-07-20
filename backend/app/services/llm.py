from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


class LlmSafetyError(ValueError):
    pass


@dataclass(frozen=True)
class Explanation:
    reason: str
    risks: list[str]
    triggers: list[str]
    referenced_prices: list[float]


def validate_explanation(payload: dict[str, Any], allowed_prices: set[float]) -> Explanation:
    prices = [float(price) for price in payload.get("referenced_prices", [])]
    if any(not any(abs(price - allowed) < 0.0001 for allowed in allowed_prices) for price in prices):
        raise LlmSafetyError("LLM response contains an untraceable price")
    if not isinstance(payload.get("reason", ""), str):
        raise LlmSafetyError("LLM reason must be text")
    for name in ("risks", "triggers"):
        if not isinstance(payload.get(name, []), list) or not all(isinstance(item, str) for item in payload.get(name, [])):
            raise LlmSafetyError(f"LLM {name} must be a list of text")
    return Explanation(payload["reason"], payload.get("risks", []), payload.get("triggers", []), prices)


class ExplanationService:
    """Optional OpenAI-compatible explanation adapter; no price field is accepted as authority."""

    def enabled(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"))

    def explain(self, facts: dict[str, Any], allowed_prices: set[float]) -> Explanation | None:
        if not self.enabled():
            return None
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], base_url=os.getenv("OPENAI_BASE_URL"))
        completion = client.chat.completions.create(
            model=os.environ["OPENAI_MODEL"],
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Explain supplied strategy facts. Never create or change prices. Return JSON with reason, risks, triggers, referenced_prices."},
                {"role": "user", "content": str(facts)},
            ],
        )
        import json

        content = completion.choices[0].message.content or "{}"
        return validate_explanation(json.loads(content), allowed_prices)
