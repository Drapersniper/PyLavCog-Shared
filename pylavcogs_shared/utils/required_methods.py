from __future__ import annotations

import asyncio
import contextlib
import inspect
import threading
from pathlib import Path
from types import MethodType

import asyncstdlib
import discord
from discord.ext.commands import CheckFailure
from red_commons.logging import getLogger
from redbot.core import commands
from redbot.core.data_manager import cog_data_path
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box
from tabulate import tabulate

from pylav.client import Client
from pylav.exceptions import NoNodeAvailable, NoNodeWithRequestFunctionalityAvailable
from pylav.types import BotT, CogT
from pylav.utils import PyLavContext
from pylav.utils.theme import EightBitANSI

from pylavcogs_shared import __VERSION__ as pylavcogs_shared_version
from pylavcogs_shared.errors import (
    IncompatibleException,
    MediaPlayerNotFoundError,
    NotDJError,
    UnauthorizedChannelError,
)

_ = Translator("PyLavShared", Path(__file__))
_LOCK = threading.Lock()
LOGGER = getLogger("red.3pt.PyLav-Shared.utils.overrides")

INCOMPATIBLE_COGS = {}


@commands.command(
    cls=commands.commands._AlwaysAvailableCommand,
    name="plcredits",
    aliases=["pltranslation"],
    i18n=_,
)
async def pylav_credits(context: PyLavContext) -> None:
    """Shows the credits and translation details for the PyLav cogs and shared code"""
    await context.send(
        embed=await context.lavalink.construct_embed(
            messageable=context,
            description=_(
                "PyLav was created by [Draper#6666](https://github.com/Drapersniper).\n\n"
                "PyLav can be located in https://github.com/Drapersniper/PyLav\n"
                "PyLavCog-Shared can be located in https://github.com/Drapersniper/PyLavCog-Shared\n"
                "PyLav-Cogs can be located in https://github.com/Drapersniper/PyLav-Cogs\n\n"
                "PyLav's support server can be found at https://discord.com/invite/Sjh2TSCYQB\n"
                "\n\n"
                "You can help translate PyLav by contributing to our Crowdin projects at:\n"
                "https://crowdin.com/project/pylav and "
                "https://crowdin.com/project/pylavcogs-shared and "
                "https://crowdin.com/project/pylavcogs\n\n\n"
                "Contributors:\n"
                "- https://github.com/Drapersniper/PyLav/graphs/contributors\n"
                "- https://github.com/Drapersniper/PyLavCog-Shared/graphs/contributors\n"
                "- https://github.com/Drapersniper/PyLav-Cogs/graphs/contributors\n"
                "If you wish to buy me a coffee for my work, you can do so at:\n"
                "https://www.buymeacoffee.com/draper or https://github.com/sponsors/Drapersniper"
            ),
        ),
        ephemeral=True,
    )


@commands.command(
    cls=commands.commands._AlwaysAvailableCommand,
    name="plversion",
    aliases=["pylavversion"],
    i18n=_,
)
async def pylav_version(context: PyLavContext) -> None:
    """Show the version of PyLav and PyLavCogs-Shared libraries"""
    if isinstance(context, discord.Interaction):
        context = await context.client.get_context(context)
    if context.interaction and not context.interaction.response.is_done():
        await context.defer(ephemeral=True)
    data = [
        (EightBitANSI.paint_white("PyLavCogs-Shared"), EightBitANSI.paint_blue(pylavcogs_shared_version)),
        (EightBitANSI.paint_white("PyLav"), EightBitANSI.paint_blue(context.lavalink.lib_version)),
    ]

    await context.send(
        embed=await context.lavalink.construct_embed(
            description=box(
                tabulate(
                    data,
                    headers=(
                        EightBitANSI.paint_yellow(_("Library"), bold=True, underline=True),
                        EightBitANSI.paint_yellow(_("Version"), bold=True, underline=True),
                    ),
                    tablefmt="fancy_grid",
                ),
                lang="ansi",
            ),
            messageable=context,
        ),
        ephemeral=True,
    )


@commands.command(
    cls=commands.commands._AlwaysAvailableCommand,
    name="plsynchslash",
    aliases=["plss"],
    i18n=_,
)
async def pylav_sync_slash(context: PyLavContext) -> None:
    """Sync the Bots slash commands"""
    if isinstance(context, discord.Interaction):
        context = await context.client.get_context(context)
    if context.interaction and not context.interaction.response.is_done():
        await context.defer(ephemeral=True)
    await context.bot.wait_until_ready()
    await context.bot.tree.sync()
    await context.send(
        embed=await context.lavalink.construct_embed(
            description=_("Synced the bots slash commands"),
            messageable=context,
        ),
        ephemeral=True,
    )


def _done_callback(task: asyncio.Task) -> None:
    with contextlib.suppress(asyncio.CancelledError):
        exc = task.exception()
        if exc is not None:
            LOGGER.error("Error in initialize task", exc_info=exc)


async def cog_command_error(self: CogT, context: PyLavContext, error: Exception) -> None:
    error = getattr(error, "original", error)
    unhandled = True
    if isinstance(error, MediaPlayerNotFoundError):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context, description=_("This command requires an existing player to be run")
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
                    "the backend services, please try again later"
                ),
                footer=_("No Lavalink node currently available") if await self.bot.is_owner(context.author) else None,
            ),
            ephemeral=True,
        )
    elif isinstance(error, NoNodeWithRequestFunctionalityAvailable):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context,
                description=_("MediaPlayer is currently unable to process tracks belonging to {feature}").format(
                    feature=error.feature
                ),
                footer=_("No Lavalink node currently available with feature {feature}").format(feature=error.feature)
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
    elif isinstance(error, NotDJError):
        unhandled = False
        await context.send(
            embed=await self.lavalink.construct_embed(
                messageable=context,
                description=_("This command requires you to be a DJ"),
            ),
            ephemeral=True,
            delete_after=10,
        )
    if unhandled:
        if (meth := getattr(self, "__pylav_original_cog_command_error", None)) and (
            func := self._get_overridden_method(meth)
        ):
            return await discord.utils.maybe_coroutine(func, context, error)
        else:
            return await self.bot.on_command_error(context, error, unhandled_by_cog=True)  # type: ignore


async def cog_unload(self: CogT) -> None:
    if self._init_task is not None:
        self._init_task.cancel()
    client = self.lavalink
    await client.unregister(cog=self)
    if client._shutting_down:
        self.bot.remove_command(pylav_credits.qualified_name)
        self.bot.remove_command(pylav_version.qualified_name)
    if meth := getattr(self, "__pylav_original_cog_unload", None):
        return await discord.utils.maybe_coroutine(meth)


async def cog_before_invoke(self: CogT, context: PyLavContext):
    try:
        await self.lavalink.wait_until_ready(timeout=30)
    except asyncio.TimeoutError as e:
        LOGGER.debug("Discarded command due to PyLav not being ready within 30 seconds")

        LOGGER.verbose(
            "Discarded command due to PyLav not being ready within 30 seconds - Guild: %s - Command: %s",
            context.guild,
            context.command.qualified_name,
        )

        raise CheckFailure(_("PyLav is not ready - Please try again shortly")) from e
    if meth := getattr(self, "__pylav_original_cog_before_invoke", None):
        return await discord.utils.maybe_coroutine(meth)


async def initialize(self: CogT, *args, **kwargs) -> None:
    if not self.init_called:
        await self.lavalink.register(self)
        await self.lavalink.initialize()
        self.init_called = True
    if meth := getattr(self, "__pylav_original_initialize", None):
        return await discord.utils.maybe_coroutine(meth, *args, **kwargs)


async def cog_check(self: CogT, context: PyLavContext) -> bool:

    # This cog mock discord objects and sends them on the listener
    #   Due to the potential risk for unexpected behaviour - disabled all commands if this cog is loaded.
    if await asyncstdlib.any(context.bot.get_cog(name) is not None for name in INCOMPATIBLE_COGS):
        return False
    if not (getattr(context.bot, "lavalink", None)):
        return False
    meth = getattr(self, "__pylav_original_cog_check", None)
    if not context.guild:
        return await discord.utils.maybe_coroutine(meth, context) if meth else True
    if getattr(context, "player", None):
        config = context.player.config
    else:
        config = context.bot.lavalink.player_config_manager.get_config(context.guild.id)

    if (channel_id := await config.fetch_text_channel_id()) != 0 and channel_id != context.channel.id:
        return False
    return await discord.utils.maybe_coroutine(meth, context) if meth else True


def class_factory(
    bot: BotT,
    cls: type[CogT],
    cogargs: tuple[object],
    cogkwargs: dict[str, object],
) -> CogT:  # sourcery no-metrics
    """
    Creates a new class which inherits from the given class and overrides the following methods:
    - cog_check
    - cog_unload
    - cog_before_invoke
    - initialize
    - cog_command_error
    """
    if not bot.get_command(pylav_credits.qualified_name):
        bot.add_command(pylav_credits)
    if not bot.get_command(pylav_version.qualified_name):
        bot.add_command(pylav_version)
    if not bot.get_command(pylav_sync_slash.qualified_name):
        bot.add_command(pylav_sync_slash)
    argspec = inspect.getfullargspec(cls.__init__)
    if ("bot" in argspec.args or "bot" in argspec.kwonlyargs) and bot not in cogargs:
        cogkwargs["bot"] = bot

    cog_instance = cls(*cogargs, **cogkwargs)
    if not hasattr(cog_instance, "__version__"):
        cog_instance.__version__ = "0.0.0"
    cog_instance.lavalink = Client(bot=bot, cog=cog_instance, config_folder=cog_data_path(raw_name="PyLav"))
    cog_instance.bot = bot
    cog_instance.init_called = False
    cog_instance._init_task = cls.cog_check
    cog_instance.pylav = cog_instance.lavalink
    old_cog_on_command_error = cog_instance._get_overridden_method(cog_instance.cog_command_error)
    old_cog_unload = cog_instance._get_overridden_method(cog_instance.cog_unload)
    old_cog_before_invoke = cog_instance._get_overridden_method(cog_instance.cog_before_invoke)
    old_cog_check = cog_instance._get_overridden_method(cog_instance.cog_check)
    old_cog_initialize = getattr(cog_instance, "initialize", None)
    if old_cog_on_command_error:
        cog_instance.__pylav_original_cog_command_error = old_cog_on_command_error
    if old_cog_unload:
        cog_instance.__pylav_original_cog_unload = old_cog_unload
    if old_cog_before_invoke:
        cog_instance.__pylav_original_cog_before_invoke = old_cog_before_invoke
    if old_cog_check:
        cog_instance.__pylav_original_cog_check = old_cog_check
    if old_cog_initialize:
        cog_instance.__pylav_original_initialize = old_cog_initialize

    cog_instance.cog_command_error = MethodType(cog_command_error, cog_instance)
    cog_instance.cog_unload = MethodType(cog_unload, cog_instance)
    cog_instance.cog_before_invoke = MethodType(cog_before_invoke, cog_instance)
    cog_instance.initialize = MethodType(initialize, cog_instance)
    cog_instance.cog_check = MethodType(cog_check, cog_instance)

    return cog_instance


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
    Overwrites cog_before_invoke
        To force commands to wait for PyLav to be ready
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
    if await asyncstdlib.any(bot.get_cog(name) is not None for name in INCOMPATIBLE_COGS if (_name := name)):
        raise IncompatibleException(
            f"{_name} is loaded, this cog is incompatible with PyLav - PyLav will not work as long as this cog is loaded"
        )
    if cogargs is None:
        cogargs = ()
    if cogkwargs is None:
        cogkwargs = {}
    if initargs is None:
        initargs = ()
    if initkwargs is None:
        initkwargs = {}
    with _LOCK:
        cog_instance = class_factory(bot, cog_cls, cogargs, cogkwargs)
        await bot.add_cog(cog_instance)
    cog_instance._init_task = asyncio.create_task(cog_instance.initialize(*initargs, **initkwargs))
    cog_instance._init_task.add_done_callback(_done_callback)
    return cog_instance
