from __future__ import annotations

import inspect
import importlib
import pkgutil
import time
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional, Type

from .base import Strategy

_EXCLUDE_MODULES = {"base", "signal", "registry", "__init__"}


class StrategyRegistry:
    """Registry for discovering, validating, and instantiating strategies."""

    def __init__(self) -> None:
        self._classes: Dict[str, Type[Strategy]] = {}
        # performance stats keyed by strategy name
        self._perf: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"calls": 0, "errors": 0, "total_time": 0.0})

    # ------------------------------------------------------------------
    def register(self, cls: Type[Strategy]) -> None:
        """Register a *Strategy* subclass after validation."""

        if not inspect.isclass(cls) or not issubclass(cls, Strategy):
            raise TypeError("Only Strategy subclasses can be registered")
        if cls is Strategy:
            return  # skip base
        name = cls.name
        if name in self._classes:
            raise ValueError(f"Strategy with name '{name}' already registered")
        # trigger parameter validation on empty params to catch obvious issues
        cls()
        self._classes[name] = cls

    # ------------------------------------------------------------------
    def discover(self, package: Optional[ModuleType] = None) -> None:
        """Auto-discover strategy classes within the strategies package."""

        if package is None:
            package = importlib.import_module(__package__)  # type: ignore[arg-type]
        pkg_path = Path(package.__file__).parent
        for _, mod_name, is_pkg in pkgutil.iter_modules([str(pkg_path)]):
            if is_pkg or mod_name in _EXCLUDE_MODULES or mod_name.startswith("_"):
                continue
            full_name = f"{package.__name__}.{mod_name}"
            module = importlib.import_module(full_name)
            self._discover_module(module)

    def _discover_module(self, module: ModuleType) -> None:
        for obj in vars(module).values():
            if inspect.isclass(obj) and issubclass(obj, Strategy):
                self.register(obj)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    def factory(self, name: str, parameters: Optional[Dict[str, Any]] = None) -> Strategy:
        """Instantiate strategy *name* with *parameters*."""

        if name not in self._classes:
            raise KeyError(f"Strategy '{name}' not registered")
        cls = self._classes[name]
        return cls(parameters)

    # ------------------------------------------------------------------
    def run_and_track(self, strategy: Strategy, data) -> Dict[str, Any]:  # pragma: no cover
        """Helper to execute *strategy.generate_signals* and track performance."""

        start = time.perf_counter()
        try:
            result = strategy.generate_signals(data)
            self._perf[strategy.name]["calls"] += 1
            return result
        except Exception:  # noqa: BLE001
            self._perf[strategy.name]["errors"] += 1
            raise
        finally:
            self._perf[strategy.name]["total_time"] += time.perf_counter() - start

    # ------------------------------------------------------------------
    @property
    def registry(self) -> Dict[str, Type[Strategy]]:
        return dict(self._classes)

    @property
    def performance(self) -> Dict[str, Dict[str, Any]]:
        return self._perf


# Global singleton
registry = StrategyRegistry()
# Discover built-ins on import
registry.discover()
