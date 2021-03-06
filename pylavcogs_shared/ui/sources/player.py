from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from red_commons.logging import getLogger
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import humanize_number
from redbot.vendored.discord.ext import menus

from pylav import Player
from pylav.types import CogT
from pylav.utils import get_time_string

from pylavcogs_shared.utils import rgetattr

if TYPE_CHECKING:
    from pylavcogs_shared.ui.menus.generic import BaseMenu

LOGGER = getLogger("red.3pt.PyLav-Shared.ui.sources.player")
_ = Translator("PyLavShared", Path(__file__))


class PlayersSource(menus.ListPageSource):
    def __init__(self, cog: CogT):
        super().__init__([], per_page=1)
        self.cog = cog
        self.current_player = None

    @property
    def entries(self) -> list[Player]:
        return list(self.cog.lavalink.player_manager.players.values())

    @entries.setter
    def entries(self, players: list[Player]):
        pass

    def get_max_pages(self):
        players = self.cog.lavalink.player_manager.connected_players
        pages, left_over = divmod(len(list(players)), self.per_page)
        if left_over:
            pages += 1
        return pages or 1

    def get_starting_index_and_page_number(self, menu: BaseMenu) -> tuple[int, int]:
        page_num = menu.current_page
        start = page_num * self.per_page
        return start, page_num

    async def format_page(self, menu: BaseMenu, player: Player) -> discord.Embed:
        idx_start, page_num = self.get_starting_index_and_page_number(menu)
        connect_dur = (
            get_time_string(int((datetime.datetime.now(datetime.timezone.utc) - player.connected_at).total_seconds()))
            or "0s"
        )
        self.current_player = player
        guild_name = player.guild.name
        queue_len = len(player.queue)
        server_owner = f"{player.guild.owner} ({player.guild.owner.id})"
        current_track = (
            await player.current.get_track_display_name(max_length=50, with_url=True)
            if player.current
            else _("Nothing playing.")
        )

        listener_count = sum(True for m in rgetattr(player, "channel.members", []) if not m.bot)
        listeners = humanize_number(listener_count)
        current_track += "\n"

        field_values = "\n".join(
            f"**{i[0]}**: {i[1]}"
            for i in [
                (_("Server Owner"), server_owner),
                (_("Connected For"), connect_dur),
                (_("Users in VC"), listeners),
                (_("Queue Length"), f"{queue_len} tracks"),
            ]
        )
        current_track += field_values

        embed = await self.cog.lavalink.construct_embed(
            messageable=menu.ctx, title=guild_name, description=current_track
        )

        embed.set_footer(
            text=_("Page {page_num}/{total_pages}  | Playing in {playing} servers.").format(
                page_num=humanize_number(page_num + 1),
                total_pages=humanize_number(self.get_max_pages()),
                playing=humanize_number(len(self.cog.lavalink.player_manager.playing_players)),
            )
        )
        return embed
