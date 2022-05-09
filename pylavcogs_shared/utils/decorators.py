from __future__ import annotations

from pathlib import Path

from redbot.core import commands
from redbot.core.i18n import Translator

from pylav.utils import PyLavContext

from pylavcogs_shared import errors
from pylavcogs_shared.errors import UnauthorizedChannelError

_ = Translator("PyLavShared", Path(__file__))


def always_hidden():
    async def pred(__: PyLavContext):
        return False

    return commands.check(pred)


def requires_player():
    async def pred(context: PyLavContext):
        # TODO: Check room setting if present allow bot to connect to it instead of throwing error
        player = context.cog.lavalink.get_player(context.guild)  # type:ignore
        if not player:
            raise errors.MediaPlayerNotFoundError(
                context,
            )
        return True

    return commands.check(pred)


def can_run_command_in_channel():
    async def pred(context: PyLavContext):
        if not context.guild:
            return True
        if context.player:
            config = context.player.config
        else:
            config = await context.lavalink.player_config_manager.get_config(context.guild.id)
        if config.text_channel_id and config.text_channel_id != context.channel.id:
            raise UnauthorizedChannelError(channel=config.text_channel_id)
        return True

    return commands.check(pred)
