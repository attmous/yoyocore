"""Power public package entrypoint."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

from yoyopod.config.models import PowerConfig

if TYPE_CHECKING:
    from yoyopod.integrations.power.manager import PowerManager
    from yoyopod.integrations.power.models import PowerSnapshot


_LAZY_EXPORTS = {
    "PowerManager": "yoyopod.integrations.power.manager",
    "PowerSnapshot": "yoyopod.integrations.power.models",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(import_module(module_name), name)


__all__ = ["PowerManager", "PowerConfig", "PowerSnapshot"]
