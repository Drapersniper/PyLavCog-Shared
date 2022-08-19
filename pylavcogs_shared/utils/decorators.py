from __future__ import annotations

from pathlib import Path

import discord
from redbot.core import commands
from redbot.core.i18n import Translator

from pylav.types import InteractionT
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
        if not (getattr(context.bot, "lavalink", None)):
            return False
        # TODO: Check room setting if present allow bot to connect to it instead of throwing error
        player = context.bot.lavalink.get_player(context.guild)  # type:ignore
        if not player:
            raise errors.MediaPlayerNotFoundError(
                context,
            )
        return True

    return commands.check(pred)


def can_run_command_in_channel():
    async def pred(context: PyLavContext):
        if not (getattr(context.bot, "lavalink", None)):
            return False
        if not context.guild:
            return True
        if getattr(context, "player", None):
            config = context.player.config
            await config.update()
        else:
            config = await context.bot.lavalink.player_config_manager.get_config(context.guild.id)
        if config.text_channel_id and config.text_channel_id != context.channel.id:
            raise UnauthorizedChannelError(channel=config.text_channel_id)
        return True

    return commands.check(pred)


async def is_dj_logic(context: PyLavContext | InteractionT) -> bool | None:
    guild = context.guild
    if isinstance(context, discord.Interaction):
        bot = context.client
        author = context.user
    else:
        bot = context.bot
        author = context.author

    if not (getattr(bot, "lavalink", None) and guild):
        return False
    is_dj = await bot.lavalink.is_dj(
        user=author, guild=guild, additional_role_ids=None, additional_user_ids={*bot.owner_ids, guild.owner_id}, bot=bot  # type: ignore
    )
    return is_dj


def invoker_is_dj():
    async def pred(context: PyLavContext):
        is_dj = await is_dj_logic(context)
        if is_dj is False:
            raise NotDJError(
                context,
            )
        return True

    return commands.check(pred)
