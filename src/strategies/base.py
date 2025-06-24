from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

import pandas as pd
from pydantic import BaseModel, ValidationError

from .signal import Signal


class Strategy(ABC):
    """Base class for all trading strategies.

    Subclasses should define an inner ``ParamModel`` (pydantic ``BaseModel``)
    describing their parameters. If absent, parameters are unchecked.
    """

    name: str = "BaseStrategy"
    description: str = ""

    # --- parameter schema -------------------------------------------------
    ParamModel: Optional[Type[BaseModel]] = None  # to be defined by subclasses

    # --- lifecyle ---------------------------------------------------------
    def __init__(self, parameters: Dict[str, Any] | None = None):
        self.parameters: Dict[str, Any] = parameters or {}
        self._param_obj: Optional[BaseModel] = None
        self.state: Dict[str, Any] = {}
        self.validate_parameters()

    # --------------------- main API ---------------------------------------
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Signal]:
        """Generate trading signals based on *data*.

        Returns:
            Dict mapping symbol -> ``Signal``
        """

    # --------------------- helpers ----------------------------------------
    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Merge *params* into existing and re-validate."""

        self.parameters.update(params)
        self.validate_parameters()

    def validate_parameters(self) -> bool:
        """Validate and coerce parameters using ``ParamModel`` if present."""

        if self.ParamModel is None:
            return True
        try:
            self._param_obj = self.ParamModel(**self.parameters)
        except ValidationError as exc:
            raise ValueError(f"Invalid parameters for {self.name}:\n{exc}") from exc
        # replace with parsed data
        self.parameters = self._param_obj.model_dump()
        return True

    # ---------------------------------------------------------------------
    def get_required_indicators(self) -> List[str]:  # noqa: D401
        """Return list of data columns needed. Default OHLCV."""

        return ["Open", "High", "Low", "Close", "Volume"]
