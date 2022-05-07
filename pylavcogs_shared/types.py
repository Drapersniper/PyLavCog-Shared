from __future__ import annotations

from typing import TypeVar

from pylav.types import CogT as PyLavCogT

T = TypeVar("T")


CogT = PyLavCogT
SourcesT = TypeVar("SourcesT", bound="Union[menus.ListPageSource]")
