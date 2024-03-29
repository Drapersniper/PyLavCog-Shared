from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import asyncstdlib
import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.vendored.discord.ext import menus

from pylav.tracks import Track
from pylav.types import CogT

from pylavcogs_shared.ui.selectors.options.queue import QueueTrackOption, SearchTrackOption

if TYPE_CHECKING:
    from pylavcogs_shared.ui.menus.queue import QueueMenu, QueuePickerMenu

LOGGER = getLogger("red.3pt.PyLav-Shared.ui.sources.queue")

_ = Translator("PyLavShared", Path(__file__))


class SearchPickerSource(menus.ListPageSource):
    entries: list[Track]

    def __init__(self, entries: list[Track], cog: CogT, per_page: int = 10):
        super().__init__(entries=entries, per_page=per_page)
        self.per_page = 25
        self.select_options: list[SearchTrackOption] = []
        self.cog = cog
        self.select_mapping: dict[str, Track] = {}

    async def get_page(self, page_number):
        if page_number > self.get_max_pages():
            page_number = 0
        base = page_number * self.per_page
        self.select_options.clear()
        self.select_mapping.clear()
        async for i, track in asyncstdlib.enumerate(
            asyncstdlib.iter(self.entries[base : base + self.per_page]), start=base
        ):  # noqa: E203
            self.select_options.append(await SearchTrackOption.from_track(track=track, index=i))
            self.select_mapping[track.id] = track
        return []

    async def format_page(self, menu: QueueMenu, entries: list[Track]) -> str:
        return ""

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence"""
        return self._max_pages or 1


class QueueSource(menus.ListPageSource):
    def __init__(self, guild_id: int, cog: CogT, history: bool = False):  # noqa
        self.cog = cog
        self.per_page = 10
        self.guild_id = guild_id
        self.history = history

    @property
    def entries(self) -> Iterable[Track]:
        if player := self.cog.lavalink.get_player(self.guild_id):
            return player.history.raw_queue if self.history else player.queue.raw_queue
        else:
            return []

    def is_paginating(self) -> bool:
        return True

    async def get_page(self, page_number: int) -> list[Track]:
        base = page_number * self.per_page
        return await asyncstdlib.list(asyncstdlib.islice(self.entries, base, base + self.per_page))

    def get_max_pages(self) -> int:
        player = self.cog.lavalink.get_player(self.guild_id)
        if not player:
            return 1
        pages, left_over = divmod(player.history.size() if self.history else player.queue.size(), self.per_page)

        if left_over:
            pages += 1
        return pages or 1

    def get_starting_index_and_page_number(self, menu: QueueMenu) -> tuple[int, int]:
        page_num = menu.current_page
        start = page_num * self.per_page
        return start, page_num

    async def format_page(self, menu: QueueMenu, tracks: list[Track]) -> discord.Embed:
        if player := self.cog.lavalink.get_player(menu.ctx.guild.id):
            return (
                await player.get_queue_page(
                    page_index=menu.current_page,
                    per_page=self.per_page,
                    total_pages=self.get_max_pages(),
                    embed=True,
                    messageable=menu.ctx,
                    history=self.history,
                )
                if player.current and (player.history.size() if self.history else True)
                else await self.cog.lavalink.construct_embed(
                    description=_("There's nothing in recently played")
                    if self.history
                    else _("There's nothing currently being played"),
                    messageable=menu.ctx,
                )
            )
        else:
            return await self.cog.lavalink.construct_embed(
                description=_("No active player found in server"), messageable=menu.ctx
            )


class QueuePickerSource(QueueSource):
    def __init__(self, guild_id: int, cog: CogT):
        super().__init__(guild_id, cog=cog)
        self.per_page = 25
        self.select_options: list[QueueTrackOption] = []
        self.select_mapping: dict[str, Track] = {}
        self.cog = cog

    async def get_page(self, page_number):
        if page_number > self.get_max_pages():
            page_number = 0
        base = page_number * self.per_page
        self.select_options.clear()
        self.select_mapping.clear()
        async for i, track in asyncstdlib.enumerate(
            asyncstdlib.islice(self.entries, base, base + self.per_page), start=base
        ):
            self.select_options.append(await QueueTrackOption.from_track(track=track, index=i))
            self.select_mapping[track.id] = track
        return []

    async def format_page(self, menu: QueuePickerMenu, tracks: list[Track]) -> discord.Embed:
        if player := self.cog.lavalink.get_player(menu.ctx.guild.id):
            return (
                await player.get_queue_page(
                    page_index=menu.current_page,
                    per_page=self.per_page,
                    total_pages=self.get_max_pages(),
                    embed=True,
                    messageable=menu.ctx,
                )
                if player.current
                else await self.cog.lavalink.construct_embed(
                    description=_("There's nothing currently being played"),
                    messageable=menu.ctx,
                )
            )
        else:
            return await self.cog.lavalink.construct_embed(
                description=_("No active player found in server"), messageable=menu.ctx
            )
