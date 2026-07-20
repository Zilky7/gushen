from datetime import date

import pytest
from pydantic import ValidationError

from app.domain.models import OhlcvBar


def test_ohlcv_bar_rejects_non_positive_prices() -> None:
    with pytest.raises(ValidationError):
        OhlcvBar(
            date=date(2026, 1, 2),
            open=100,
            high=101,
            low=99,
            close=0,
            volume=1_000,
        )
