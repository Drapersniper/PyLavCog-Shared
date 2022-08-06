from __future__ import annotations

from pathlib import Path

from redbot.core import commands
from redbot.core.i18n import Translator

from pylav.utils import PyLavContext

from pylavcogs_shared import errors
from pylavcogs_shared.errors import NotDJError, UnauthorizedChannelError

_ = Translator("PyLavShared", Path(__file__))


def always_hidden():
    async def pred(__: PyLavContext):
        return False

    return commands.check(pred)


def requires_player():
    async def pred(context: PyLavContext):
        if not (getattr(context, "lavalink", None)):
            return False
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
        if not (getattr(context, "lavalink", None)):
            return False
        if not context.guild:
            return True
        if getattr(context, "player", None):
            config = context.player.config
        else:
            config = await context.lavalink.player_config_manager.get_config(context.guild.id)
        if config.text_channel_id and config.text_channel_id != context.channel.id:
            raise UnauthorizedChannelError(channel=config.text_channel_id)
        return True

    return commands.check(pred)


async def is_dj_logic(context: PyLavContext) -> bool | type[NotDJError]:
    if not (getattr(context, "lavalink", None) and context.guild):
        return False
    if await context.bot.allowed_by_whitelist_blacklist(who=context.author, guild=context.author.guild):
        return True
    is_dj = await context.lavalink.is_dj(
        user=context.author, guild=context.guild, additional_role_ids=None, additional_user_ids=None
    )
    if not is_dj:
        return errors.NotDJError
    return True


def invoker_is_dj():
    async def pred(context: PyLavContext):
        is_dj = await is_dj_logic(context)
        if isinstance(is_dj, bool):
            return is_dj
        raise is_dj(
            context,
        )

    return commands.check(pred)
