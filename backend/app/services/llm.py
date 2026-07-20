from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

load_dotenv()


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
    prose = [payload["reason"], *payload.get("risks", []), *payload.get("triggers", [])]
    if any(re.search(r"(?<![A-Za-z])\d+(?:\.\d+)?", item) for item in prose):
        raise LlmSafetyError("LLM response contains an untraceable numeric value in text")
    return Explanation(payload["reason"], payload.get("risks", []), payload.get("triggers", []), prices)


class ExplanationService:
    """Optional OpenAI-compatible explanation adapter; no price field is accepted as authority."""

    def enabled(self) -> bool:
        return bool(self._api_key() and self._model())

    @staticmethod
    def _api_key() -> str | None:
        return os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    @staticmethod
    def _model() -> str | None:
        return os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL")

    @staticmethod
    def _base_url() -> str | None:
        return os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")

    def explain(self, facts: dict[str, Any], allowed_prices: set[float]) -> Explanation | None:
        if not self.enabled():
            return None
        from openai import OpenAI

        client = OpenAI(api_key=self._api_key(), base_url=self._base_url())
        completion = client.chat.completions.create(
            model=self._model(),
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
