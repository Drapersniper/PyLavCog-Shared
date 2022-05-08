from __future__ import annotations

import functools
from typing import Any, MutableMapping

__all__ = ("decorators", "rgetattr", "rsetattr")


def rsetattr(obj: object, attr: str, val: Any) -> None:
    pre, _, post = attr.rpartition(".")
    setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj: object, attr: str, *args: Any) -> Any:
    def _getattr(obj2, attr2):
        return getattr(obj2, attr2, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


def recursive_merge(d1: dict, d2: dict) -> dict:
    """
    Update two dicts of dicts recursively,
    if either mapping has leaves that are non-dicts,
    the second's leaf overwrites the first's.
    """
    for k, v in d1.items():
        if k in d2 and all(isinstance(e, MutableMapping) for e in (v, d2[k])):
            d2[k] = recursive_merge(v, d2[k])
    return d1 | d2
