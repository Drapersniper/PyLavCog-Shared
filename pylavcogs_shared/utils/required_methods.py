from __future__ import annotations

import asyncio
import contextlib
import inspect
from copy import copy
from pathlib import Path
from types import MethodType

from red_commons.logging import getLogger
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator

from pylav import Client, NoNodeAvailable
from pylav.exceptions import NoNodeWithRequestFunctionalityAvailable
from pylav.types import BotT, CogT
from pylav.utils import PyLavContext

from pylavcogs_shared.errors import MediaPlayerNotFoundError, UnauthorizedChannelError

_ = Translator("PyLavShared", Path(__file__))

LOGGER = getLogger("red.3pt.PyLav-Shared.utils.overrides")


async def generic_cog_command_error(self, context: PyLavContext, error: Exception) -> None:
    error = getattr(error, "original", error)
    unhandled = True
    if isinstance(error, MediaPlayerNotFoundError):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context, description=_("This command requires an existing player to be run.")
            ),
            ephemeral=True,
        )
    elif isinstance(error, NoNodeAvailable):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context,
                description=_(
                    "MediaPlayer cog is currently temporarily unavailable due to an outage with "
                    "the backend services, please try again later."
                ),
                footer=_("No Lavalink node currently available.") if await self.bot.is_owner(context.author) else None,
            ),
            ephemeral=True,
        )
    elif isinstance(error, NoNodeWithRequestFunctionalityAvailable):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context,
                description=_("MediaPlayer is currently unable to process tracks belonging to {feature}.").format(
                    feature=error.feature
                ),
                footer=_("No Lavalink node currently available with feature {feature}.").format(feature=error.feature)
                if await self.bot.is_owner(context.author)
                else None,
            ),
            ephemeral=True,
        )
    elif isinstance(error, UnauthorizedChannelError):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context,
                description=_("This command is not available in this channel. Please use {channel}").format(
                    channel=channel.mention if (channel := context.guild.get_channel_or_thread(error.channel)) else None
                ),
            ),
            ephemeral=True,
            delete_after=10,
        )
    if unhandled:
        if hasattr(self, "_pylav_cog_command_error"):
            return await self._pylav_cog_command_error(context, error)
        else:
            return await self.bot.on_command_error(context, error, unhandled_by_cog=True)  # type: ignore


async def generic_cog_unload(self) -> None:
    if self._init_task is not None:
        self._init_task.cancel()
    await self.bot.lavalink.unregister(cog=self)
    if hasattr(self, "_pylav_original_cog_unload"):
        return await self._pylav_original_cog_unload()


async def generic_initialize(self, *args, **kwargs) -> None:
    await self.lavalink.register(self)
    await self.lavalink.initialize()
    if hasattr(self, "_pylav_original_initialize"):
        return await self._pylav_original_initialize()


async def generic_cog_check(self, ctx: PyLavContext) -> bool:
    method = self._pylav_original_cog_check if hasattr(self, "_pylav_original_cog_check") else None
    if not ctx.guild:
        return (await self.method(ctx)) if method else True
    if ctx.player:
        config = ctx.player.config
    else:
        config = await self.lavalink.player_config_manager.get_config(ctx.guild.id)
    if config.text_channel_id and config.text_channel_id != ctx.channel.id:
        raise UnauthorizedChannelError(channel=config.text_channel_id)
    return (await self.method(self, ctx)) if method else True


async def generic_setup(bot: BotT, cog_cls: type[CogT]) -> None:
    """Simple setup call which adds the cog instance to the bot and call the cogs Initialize method."""
    cog_instance = cog_cls(bot)
    await bot.add_cog(cog_instance)
    cog_instance._init_task = asyncio.create_task(cog_instance.initialize())


def _done_callback(task: asyncio.Task) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        exc = task.exception()
        if exc is not None:
            LOGGER.error("Error in initialize task", exc_info=exc)


async def pylav_auto_setup(bot: BotT, cog_cls: type[CogT], *args: object, **kwargs: object) -> CogT:
    """Injects all the methods and attributes to respect PyLav Settings and keep the user experience consistent.

    Adds `.bot` attribute to the cog instance.
    Adds `.lavalink` attribute to the cog instance and starts up PyLav
    Overwrites cog_unload method to unregister the cog from Lavalink,
        calling the original cog_unload method once the PyLav unregister code is run.
    Overwrites cog_check method to check if the cog is allowed to run in the current context,
        If called within a Guild then we check if we can run as per the PyLav Command channel lock,
        if this check passes then the original cog_check method is called.
    Overwrites cog_command_error method to handle PyLav errors raised by the cog,
        if the cog defines their own cog_command_error method,
        this will still be called after the built-in PyLav error handling if the error raised was unhandled.
    Overwrites initialize method to handle PyLav startup,
        calling the original initialize method once the PyLav initialization code is run, if such method exists. code is run.

    :warning: If your Cog defines their own initialize method, the signature of the method must be:
        `async def initialize(self) -> None`

        If you need to pass arguments to the initialize method, use a different named method instead.
        async def initialize(self) -> None:
            await self.my_custom_initialize_method(*args, **kwargs)

        async def my_custom_initialize_method(self, *args, **kwargs) -> object | None:
            ...

    Args:
        bot (BotT): The bot instance to load the cog instance to.
        cog_cls (type[CogT]): The cog class load.
        *args: The arguments to pass to the cog instance init.
        **kwargs: The keyword arguments to pass to the cog instance init.

    Returns:
        CogT: The cog instance loaded to the bot.

    Example:
        >>> from pylavcogs_shared.utils.required_methods import pylav_auto_setup
        >>> from discord.ext.commands import Cog
        >>> class MyCogClass(Cog):
        ...     def __init__(self, bot: BotT, special_arg: object):
        ...         self.bot = bot
        ...         self.special_arg = special_arg


        >>> async def setup(bot: BotT) -> None:
        ...     await pylav_auto_setup(bot, MyCogClass, special_arg=42)

    """
    argspec = inspect.getfullargspec(cog_cls.__init__)
    if "bot" in argspec.args or "bot" in argspec.kwonlyargs:
        kwargs["bot"] = bot
    cog_instance = cog_cls(*args, **kwargs)
    cog_instance.bot = bot
    cog_instance.lavalink = Client(bot=bot, cog=cog_instance, config_folder=cog_data_path(raw_name="PyLav"))
    if meth := cog_cls._get_overridden_method(cog_instance.cog_command_error):
        cog_instance._pylav_original_cog_command_error = copy(meth)
    cog_instance.cog_command_error = MethodType(generic_cog_command_error, cog_instance)
    if meth := cog_cls._get_overridden_method(cog_instance.cog_unload):
        cog_instance._pylav_original_cog_unload = copy(meth)
    cog_instance.cog_unload = MethodType(generic_cog_unload, cog_instance)
    if meth := cog_cls._get_overridden_method(cog_instance.cog_check):
        cog_instance._pylav_original_cog_check = copy(meth)
    cog_instance.cog_check = MethodType(generic_cog_check, cog_instance)
    if init_meth := getattr(cog_instance, "initialize", None):
        cog_instance._pylav_original_initialize = copy(init_meth)
    cog_instance.initialize = MethodType(generic_initialize, cog_instance)
    await bot.add_cog(cog_instance)
    cog_instance._init_task = asyncio.create_task(cog_instance.initialize())
    cog_instance._init_task.add_done_callback(_done_callback)
    return cog_instance
