from __future__ import annotations

import asyncio
import contextlib
import inspect
from pathlib import Path

import discord
from red_commons.logging import getLogger
from redbot.core import commands
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator

from pylav import Client, NoNodeAvailable
from pylav.exceptions import NoNodeWithRequestFunctionalityAvailable
from pylav.types import BotT, CogT
from pylav.utils import PyLavContext

from pylavcogs_shared.errors import MediaPlayerNotFoundError, UnauthorizedChannelError

_ = Translator("PyLavShared", Path(__file__))

LOGGER = getLogger("red.3pt.PyLav-Shared.utils.overrides")


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


def class_factory(
    bot: BotT,
    cls: type[CogT],
    cogargs: tuple[object],
    cogkwargs: dict[str, object],
) -> CogT:  # sourcery no-metrics
    """
    Creates a new class which inherits from the given class and overrides the following methods:
    - __init__
    - cog_check
    - cog_unload
    - initialize
    - cog_command_error
    """

    class PyLavCog(cls, commands.Cog):
        def __init__(self, bot: BotT, *args, **kwargs):
            super_cls = super()

            self.__name__ = cls.__name__
            self.__module__ = cls.__module__
            self.__doc__ = cls.__doc__
            self.__init_subclass__ = cls.__init_subclass__
            self.__qualname__ = cls.__qualname__
            self.__repr__ = cls.__repr__
            self.__str__ = cls.__str__

            self.__cog_name__ = super_cls.__cog_name__
            self.__cog_description__ = super_cls.__cog_description__
            self.__cog_group_name__ = super_cls.__cog_group_name__
            self.__cog_group_description__ = super_cls.__cog_group_description__
            self.__cog_settings__ = super_cls.__cog_settings__
            self.__cog_commands__ = super_cls.__cog_commands__
            self.__cog_app_commands__ = super_cls.__cog_app_commands__
            self.__cog_listeners__ = super_cls.__cog_listeners__
            if hasattr(super_cls, "__cog_app_commands_group__"):
                self.__cog_app_commands_group__ = super_cls.__cog_app_commands_group__
            if hasattr(super_cls, "__cog_is_app_commands_group__"):
                self.__cog_is_app_commands_group__ = super_cls.__cog_is_app_commands_group__
            self.bot = bot
            self.init_called = False
            self._init_task = None
            self.lavalink = Client(bot=bot, cog=self, config_folder=cog_data_path(raw_name="PyLav"))
            argspec = inspect.getfullargspec(super().__init__)
            new_args = args
            new_kwargs = {arg: kwargs[arg] for arg in argspec.args if arg in kwargs}
            for arg in argspec.kwonlyargs:
                if arg in kwargs:
                    new_kwargs[arg] = kwargs[arg]
            if "bot" in argspec.args or "bot" in argspec.kwonlyargs:
                new_kwargs["bot"] = bot
            if hasattr(super_cls, "__translator__"):
                self.__translator__ = super_cls.__translator__
            super_cls.__init__(*new_args, **new_kwargs)

        async def cog_command_error(self, context: PyLavContext, error: Exception) -> None:
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
                        footer=_("No Lavalink node currently available.")
                        if await self.bot.is_owner(context.author)
                        else None,
                    ),
                    ephemeral=True,
                )
            elif isinstance(error, NoNodeWithRequestFunctionalityAvailable):
                unhandled = False
                await context.send(
                    embed=await self.lavalink.construct_embed(
                        messageable=context,
                        description=_(
                            "MediaPlayer is currently unable to process tracks belonging to {feature}."
                        ).format(feature=error.feature),
                        footer=_("No Lavalink node currently available with feature {feature}.").format(
                            feature=error.feature
                        )
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
                            channel=channel.mention
                            if (channel := context.guild.get_channel_or_thread(error.channel))
                            else None
                        ),
                    ),
                    ephemeral=True,
                    delete_after=10,
                )
            if unhandled:
                if func := super()._get_overridden_method(super().cog_command_error):
                    return await discord.utils.maybe_coroutine(func, context, error)
                else:
                    return await self.bot.on_command_error(context, error, unhandled_by_cog=True)  # type: ignore

        async def cog_unload(self) -> None:
            if self._init_task is not None:
                self._init_task.cancel()
            await self.bot.lavalink.unregister(cog=self)
            return await discord.utils.maybe_coroutine(super().cog_unload)

        async def initialize(self, *args, **kwargs) -> None:
            if not self.init_called:
                await self.lavalink.register(self)
                await self.lavalink.initialize()
                self.init_called = True
            if hasattr(super(), "initialize"):
                return await discord.utils.maybe_coroutine(super().initialize, *args, **kwargs)

        async def cog_check(self, ctx: PyLavContext) -> bool:
            if not ctx.guild:
                return await discord.utils.maybe_coroutine(super().cog_check, ctx)
            if ctx.player:
                config = ctx.player.config
            else:
                config = await self.lavalink.player_config_manager.get_config(ctx.guild.id)
            if config.text_channel_id and config.text_channel_id != ctx.channel.id:
                raise UnauthorizedChannelError(channel=config.text_channel_id)
            return await discord.utils.maybe_coroutine(super().cog_check, ctx)

    if "bot" not in cogkwargs:
        cogkwargs["bot"] = bot
    return PyLavCog(*cogargs, **cogkwargs)


async def pylav_auto_setup(
    bot: BotT,
    cog_cls: type[CogT],
    cogargs: tuple[object, ...] = None,
    cogkwargs: dict[str, object] = None,
    initargs: tuple[object, ...] = None,
    initkwargs: dict[str, object] = None,
) -> CogT:
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


    Args:
        bot (BotT): The bot instance to load the cog instance to.
        cog_cls (type[CogT]): The cog class load.
        cogargs (tuple[object]): The arguments to pass to the cog class.
        cogkwargs (dict[str, object]): The keyword arguments to pass to the cog class.
        initargs (tuple[object]): The arguments to pass to the initialize method.
        initkwargs (dict[str, object]): The keyword arguments to pass to the initialize method.

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
        ...     await pylav_auto_setup(bot, MyCogClass, cogargs=(), cogkwargs=dict(special_arg=42), initargs=(), initkwargs=dict())

    """
    if cogargs is None:
        cogargs = ()
    if cogkwargs is None:
        cogkwargs = {}
    if initargs is None:
        initargs = ()
    if initkwargs is None:
        initkwargs = {}
    cog_instance = class_factory(bot, cog_cls, cogargs, cogkwargs)
    await bot.add_cog(cog_instance)
    cog_instance._init_task = asyncio.create_task(cog_instance.initialize(*initargs, **initkwargs))
    cog_instance._init_task.add_done_callback(_done_callback)
    return cog_instance
