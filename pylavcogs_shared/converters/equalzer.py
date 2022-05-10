from __future__ import annotations

from typing import TYPE_CHECKING

from discord.app_commands import Choice, Transformer
from discord.ext import commands

from pylav.types import ContextT, InteractionT

if TYPE_CHECKING:
    BassBoostConverter = str
else:

    class BassBoostConverter(Transformer):
        @classmethod
        async def convert(cls, ctx: ContextT, arg: str) -> str:
            """Converts user input to a valid argument for the bassboost command."""
            from pylav import EntryNotFoundError

            try:
                match = next(
                    filter(
                        lambda x: x.lower().startswith(arg.lower()),
                        [
                            "Maximum",
                            "Insane",
                            "Extreme",
                            "High",
                            "Very High",
                            "Medium",
                            "Cut-off",
                            "Off",
                        ],
                    ),
                    None,
                )
                if not match:
                    raise EntryNotFoundError
                return match
            except EntryNotFoundError as e:
                raise commands.BadArgument(_("Bass boost with name `{arg}` not found.").format(arg=arg)) from e

        @classmethod
        async def transform(cls, interaction: InteractionT, argument: str) -> str:
            ctx = await interaction.client.get_context(interaction)
            return await cls.convert(ctx, argument)

        @classmethod
        async def autocomplete(cls, interaction: InteractionT, current: str) -> list[Choice]:
            return [
                Choice(name=t, value=p)
                for p, t in [
                    ("Maximum", _("Maximum")),
                    ("Insane", _("Insane")),
                    ("Extreme", _("Extreme")),
                    ("Very High", _("Very High")),
                    ("High", _("High")),
                    ("Medium", _("Medium")),
                    ("Cut-off", _("Cut-off")),
                    ("Off", _("Off")),
                    ("Maximum", _("Maximum")),
                    ("Maximum", _("Maximum")),
                    ("Maximum", _("Maximum")),
                ]
                if current.lower() in p.lower()
            ]
