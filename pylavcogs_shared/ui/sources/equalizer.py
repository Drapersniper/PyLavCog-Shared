from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box
from redbot.vendored.discord.ext import menus
from tabulate import tabulate

from pylavcogs_shared.types import CogT

if TYPE_CHECKING:
    from pylavcogs_shared.ui.menus.generic import BaseMenu

LOGGER = getLogger("red.3pt.PyLav-Shared.ui.sources.equalizer")
_ = Translator("PyLavShared", Path(__file__))


class EQPresetsSource(menus.ListPageSource):
    def __init__(self, cog: CogT, pages: list[tuple[str, dict]], per_page: int = 10):
        pages.sort()
        super().__init__(pages, per_page=per_page)
        self.cog = cog

    def get_starting_index_and_page_number(self, menu: BaseMenu) -> tuple[int, int]:
        page_num = menu.current_page
        start = page_num * self.per_page
        return start, page_num

    async def format_page(self, menu: BaseMenu, page: list[tuple[str, dict]]) -> discord.Embed:
        header_name = _("Preset Name")
        header_author = _("Author")
        data = []
        for preset_name, preset_data in page:
            try:
                author = self.cog.bot.get_user(preset_data["author"])
            except TypeError:
                author = "Build-in"
            data.append(
                {
                    header_name: preset_name,
                    header_author: f"{author}",
                }
            )
        embed = await self.cog.lavalink.construct_embed(
            messageable=menu.ctx, description=box(tabulate(data, headers="keys"))
        )
        return embed

    def get_max_pages(self):
        """:class:`int`: The maximum number of pages required to paginate this sequence."""
        return self._max_pages or 1
