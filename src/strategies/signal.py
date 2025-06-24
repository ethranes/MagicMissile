from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(slots=True)
class Signal:
    """Trading signal with confidence and optional metadata."""

    type: SignalType
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # pragma: no cover
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0,1]")
