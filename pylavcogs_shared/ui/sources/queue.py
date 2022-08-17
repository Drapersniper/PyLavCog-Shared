from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import asyncstdlib
import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.vendored.discord.ext import menus

from pylav import Track
from pylav.sql.models import PlaylistModel
from pylav.types import CogT

from pylavcogs_shared.ui.selectors.options.queue import EffectsOption, QueueTrackOption, SearchTrackOption

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
        for i, track in enumerate(self.entries[base : base + self.per_page], start=base):  # noqa: E203
            self.select_options.append(await SearchTrackOption.from_track(track=track, index=i))
            self.select_mapping[track.id] = track
        return []

    async def format_page(self, menu: QueueMenu, entries: list[Track]) -> str:
        return ""

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages or 1


class EffectsPickerSource(menus.ListPageSource):
    def __init__(self, guild_id: int, cog: CogT):
        super().__init__(
            entries=[
                "reset",
                "nightcore",
                "vaporwave",
                "synth",
                "bassboost",
                "metal",
                "piano",
                "default",
            ],
            per_page=25,
        )
        self.guild_id = guild_id
        self.select_options: list[EffectsOption] = []
        self.select_mapping: dict[str, str] = {}
        self.cog = cog

    def get_starting_index_and_page_number(self, menu: QueueMenu) -> tuple[int, int]:
        page_num = menu.current_page
        start = page_num * self.per_page
        return start, page_num

    async def format_page(self, menu: QueueMenu, playlists: list[PlaylistModel]) -> str:
        return ""

    async def get_page(self, page_number):
        if page_number > self.get_max_pages():
            page_number = 0
        base = page_number * self.per_page
        self.select_options.clear()
        self.select_mapping.clear()
        for i, effect in enumerate(self.entries[base : base + self.per_page], start=base):  # noqa: E203
            self.select_mapping[f"{effect}"] = effect
            if effect in ["reset", "default"]:
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Reset the effects to default."),
                        index=i,
                    )
                )
            elif effect == "nightcore":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Nightcore effect."),
                        index=i,
                    )
                )
            elif effect == "vaporwave":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Vaporwave effect."),
                        index=i,
                    )
                )
            elif effect == "synth":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Synth effect."),
                        index=i,
                    )
                )
            elif effect == "bassboost":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Bassboost equalizer preset."),
                        index=i,
                    )
                )
            elif effect == "metal":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Metal equalizer preset."),
                        index=i,
                    )
                )
            elif effect == "piano":
                self.select_options.append(
                    EffectsOption(
                        label=effect.title(),
                        value=effect,
                        description=_("Apply the Piano equalizer preset."),
                        index=i,
                    )
                )
        return self.entries[base : base + self.per_page]  # noqa: E203

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages or 1


class QueueSource(menus.ListPageSource):
    def __init__(self, guild_id: int, cog: CogT, history: bool = False):  # noqa
        self.cog = cog
        self.per_page = 10
        self.guild_id = guild_id
        self.history = history

    @property
    def entries(self) -> Iterable[Track]:
        player = self.cog.lavalink.get_player(self.guild_id)
        if not player:
            return []
        return player.history.raw_queue if self.history else player.queue.raw_queue

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
        player = self.cog.lavalink.get_player(menu.ctx.guild.id)
        if not player:
            return await self.cog.lavalink.construct_embed(
                description="No active player found in server.", messageable=menu.ctx
            )
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
                description="There's nothing in recently played."
                if self.history
                else "There's nothing currently being played.",
                messageable=menu.ctx,
            )
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
        for i, track in enumerate(
            await asyncstdlib.list(asyncstdlib.islice(self.entries, base, base + self.per_page)), start=base
        ):
            self.select_options.append(await QueueTrackOption.from_track(track=track, index=i))
            self.select_mapping[track.id] = track
        return []

    async def format_page(self, menu: QueuePickerMenu, tracks: list[Track]) -> discord.Embed:
        player = self.cog.lavalink.get_player(menu.ctx.guild.id)
        if not player:
            return await self.cog.lavalink.construct_embed(
                description="No active player found in server.", messageable=menu.ctx
            )
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
                description="There's nothing currently being played.",
                messageable=menu.ctx,
            )
        )
