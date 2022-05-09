from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, Union

from redbot.core.commands import commands
from redbot.core.i18n import Translator

from pylav.converters.ranges import RangeConverter as PLRangeConverter
from pylav.types import ContextT

_ = Translator("PyLavShared", Path(__file__))
if TYPE_CHECKING:

    RangeConverter = TypeVar("RangeConverter", bound=Union[int, float])
else:

    class RangeConverter(PLRangeConverter):
        @classmethod
        async def convert(cls, ctx: ContextT, arg: str) -> int:
            """Converts a node name or ID to a list of matching objects."""
            try:
                level = int(arg)
            except ValueError as e:
                raise commands.BadArgument("Invalid input, argument must be an integer i.e 1, 2, 3, 4, 5") from e

            if (cls.min_value() is not None and level < cls.min_value()) or (
                cls.max_value() is not None and level > cls.max_value()
            ):
                if cls.min_value() is not None and cls.max_value() is not None:
                    raise commands.BadArgument(
                        _("Argument must be between {min} and {max}.").format(min=cls.min_value(), max=cls.max_value())
                    )
                elif cls.min_value() is not None:
                    raise commands.BadArgument(_("Argument must be at least {min}.").format(min=cls.min_value()))
                else:
                    raise commands.BadArgument(_("Argument must be at most {max)}.").format(max=cls.max_value()))
            return level
