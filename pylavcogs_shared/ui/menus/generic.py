from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any

import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.vendored.discord.ext import menus

from pylav.types import BotT, ContextT
from pylav.utils import PyLavContext

from pylavcogs_shared.types import CogT, SourcesT
from pylavcogs_shared.ui.buttons.generic import CloseButton, NavigateButton, NoButton, RefreshButton, YesButton

LOGGER = getLogger("red.3pt.PyLav-Shared.ui.menu.generic")
_ = Translator("PyLavShared", Path(__file__))


class BaseMenu(discord.ui.View):
    def __init__(
        self,
        cog: CogT,
        bot: BotT,
        source: menus.ListPageSource,
        *,
        delete_after_timeout: bool = True,
        timeout: int = 120,
        message: discord.Message = None,
        starting_page: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            timeout=timeout,
        )
        self.author = None
        self.ctx = None
        self.cog = cog
        self.bot = bot
        self.message = message
        self._source = source
        self.delete_after_timeout = delete_after_timeout
        self.current_page = starting_page or kwargs.get("page_start", 0)
        self._running = True

    @property
    def source(self) -> menus.ListPageSource:
        return self._source

    async def on_timeout(self):
        self._running = False
        if self.message is None:
            return
        with contextlib.suppress(discord.HTTPException):
            if self.delete_after_timeout and not self.message.flags.ephemeral:
                await self.message.delete()
            else:
                await self.message.edit(view=None)

    async def get_page(self, page_num: int):
        try:
            if page_num >= self._source.get_max_pages():
                page_num = 0
                self.current_page = 0
            page = await self.source.get_page(page_num)
        except IndexError:
            self.current_page = 0
            page = await self.source.get_page(self.current_page)
        value = await self.source.format_page(self, page)  # type: ignore
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {"content": value, "embed": None}
        elif isinstance(value, discord.Embed):
            return {"embed": value, "content": None}

    async def send_initial_message(self, ctx: PyLavContext | discord.Interaction):
        self.ctx = ctx
        kwargs = await self.get_page(self.current_page)
        await self.prepare()
        self.message = await ctx.send(**kwargs, view=self, ephemeral=True)
        return self.message

    async def show_page(self, page_number, interaction: discord.Interaction):
        self.current_page = page_number
        kwargs = await self.get_page(self.current_page)
        await self.prepare()
        if not interaction.response.is_done():
            await interaction.response.edit_message(**kwargs, view=self)
        else:
            await interaction.followup.edit(**kwargs, view=self)

    async def show_checked_page(self, page_number: int, interaction: discord.Interaction) -> None:
        max_pages = self._source.get_max_pages()
        try:
            if max_pages is None:
                # If it doesn't give maximum pages, it cannot be checked
                await self.show_page(page_number, interaction)
            elif page_number >= max_pages:
                await self.show_page(0, interaction)
            elif page_number < 0:
                await self.show_page(max_pages - 1, interaction)
            elif max_pages > page_number >= 0:
                await self.show_page(page_number, interaction)
        except IndexError:
            # An error happened that can be handled, so ignore it.
            pass

    async def interaction_check(self, interaction: discord.Interaction):
        """Just extends the default reaction_check to use owner_ids"""
        if (not await self.bot.allowed_by_whitelist_blacklist(interaction.user, guild=interaction.guild)) or (
            self.author and (interaction.user.id != self.author.id)
        ):
            await interaction.response.send_message(
                content="You are not authorized to interact with this.", ephemeral=True
            )
            return False
        LOGGER.critical("Interaction check - %s (%s)", interaction.user, interaction.user.id)
        return True

    async def prepare(self):
        return

    async def on_error(self, error: Exception, item: discord.ui.Item[Any], interaction: discord.Interaction) -> None:
        LOGGER.info("Ignoring exception in view %s for item %s:", self, item, exc_info=error)


class PaginatingMenu(BaseMenu):
    def __init__(
        self,
        cog: CogT,
        bot: BotT,
        source: SourcesT,
        original_author: discord.abc.User,
        *,
        clear_buttons_after: bool = True,
        delete_after_timeout: bool = False,
        timeout: int = 120,
        message: discord.Message = None,
        starting_page: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cog=cog,
            bot=bot,
            source=source,
            clear_buttons_after=clear_buttons_after,
            delete_after_timeout=delete_after_timeout,
            timeout=timeout,
            message=message,
            starting_page=starting_page,
            **kwargs,
        )
        self.author = original_author
        self.forward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=1,
            row=0,
            cog=cog,
        )
        self.backward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=-1,
            row=0,
            cog=cog,
        )
        self.first_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            direction=0,
            row=0,
            cog=cog,
        )
        self.last_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            direction=self.source.get_max_pages,
            row=0,
            cog=cog,
        )
        self.refresh_button = RefreshButton(
            style=discord.ButtonStyle.grey,
            row=0,
            cog=cog,
        )

        self.close_button = CloseButton(
            style=discord.ButtonStyle.red,
            row=0,
            cog=cog,
        )
        self.add_item(self.close_button)
        self.add_item(self.first_button)
        self.add_item(self.backward_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_button)

    async def start(self, ctx: PyLavContext | discord.Interaction):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)
        self.ctx = ctx
        await self.send_initial_message(ctx)

    async def prepare(self):
        max_pages = self.source.get_max_pages()
        self.forward_button.disabled = False
        self.backward_button.disabled = False
        self.first_button.disabled = False
        self.last_button.disabled = False
        if max_pages == 2:
            self.first_button.disabled = True
            self.last_button.disabled = True
        elif max_pages == 1:
            self.forward_button.disabled = True
            self.backward_button.disabled = True
            self.first_button.disabled = True
            self.last_button.disabled = True


class PromptYesOrNo(discord.ui.View):
    ctx: ContextT
    message: discord.Message
    author: discord.abc.User
    response: bool

    def __init__(self, cog: CogT, initial_message: str, *, timeout: int = 120) -> None:
        super().__init__(timeout=timeout)
        self.cog = cog
        self.initial_message_str = initial_message
        self.yes_button = YesButton(
            style=discord.ButtonStyle.green,
            row=0,
            cog=cog,
        )
        self.no_button = NoButton(
            style=discord.ButtonStyle.red,
            row=0,
            cog=cog,
        )
        self.add_item(self.yes_button)
        self.add_item(self.no_button)
        self._running = True
        self.message = None  # type: ignore
        self.ctx = None  # type: ignore
        self.author = None  # type: ignore
        self.response = None  # type: ignore

    async def on_timeout(self):
        self._running = False
        if self.message is None:
            return
        with contextlib.suppress(discord.HTTPException):
            if not self.message.flags.ephemeral:
                await self.message.delete()
            else:
                await self.message.edit(view=None)

    async def start(self, ctx: PyLavContext | discord.Interaction):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)
        self.ctx = ctx
        await self.send_initial_message(ctx)

    async def send_initial_message(self, ctx: PyLavContext | discord.Interaction):
        if isinstance(ctx, discord.Interaction):
            self.author = ctx.user
        else:
            self.author = ctx.author
        self.ctx = ctx
        self.message = await ctx.send(
            embed=await self.cog.lavalink.construct_embed(description=self.initial_message_str, messageable=ctx),
            view=self,
            ephemeral=True,
        )
        return self.message

    async def wait_for_yes_no(self, wait_for: float = None) -> bool:
        tasks = [asyncio.create_task(c) for c in [self.yes_button.responded.wait(), self.no_button.responded.wait()]]
        done, pending = await asyncio.wait(tasks, timeout=wait_for or self.timeout, return_when=asyncio.FIRST_COMPLETED)
        self.stop()
        for task in pending:
            task.cancel()
        if done:
            done.pop().result()
        if not self.message.flags.ephemeral:
            await self.message.delete()
        else:
            await self.message.edit(view=None)
        if self.yes_button.responded.is_set():
            self.response = True
        else:
            self.response = False
        return self.response

    def stop(self):
        super().stop()
        asyncio.ensure_future(self.on_timeout())