from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterable

import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus

from pylav.types import CogT

if TYPE_CHECKING:
    from pylavcogs_shared.ui.menus.generic import BaseMenu

LOGGER = getLogger("red.3pt.PyLav-Shared.ui.sources.generic")

_ = Translator("PyLavShared", Path(__file__))


class PreformattedSource(menus.ListPageSource):
    def __init__(self, pages: Iterable[str | discord.Embed]):
        super().__init__(pages, per_page=1)

    async def format_page(self, menu: BaseMenu, page: str | discord.Embed) -> discord.Embed | str:
        return page

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages or 1


class ListSource(menus.ListPageSource):
    def __init__(self, cog: CogT, title: str, pages: list[str], per_page: int = 10):
        pages.sort()
        super().__init__(pages, per_page=per_page)
        self.title = title
        self.cog = cog

    def get_starting_index_and_page_number(self, menu: BaseMenu) -> tuple[int, int]:
        page_num = menu.current_page
        start = page_num * self.per_page
        return start, page_num

    async def format_page(self, menu: BaseMenu, page: list[str]) -> discord.Embed:
        idx_start, page_num = self.get_starting_index_and_page_number(menu)
        text = "".join(f"{i}. [{entry}]" for i, entry in enumerate(page, idx_start + 1))

        output = box(text, lang="ini")
        embed = await self.cog.lavalink.construct_embed(messageable=menu.ctx, title=self.title, description=output)
        return embed

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages or 1
