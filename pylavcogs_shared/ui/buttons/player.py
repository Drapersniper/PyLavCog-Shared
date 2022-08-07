from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Literal

import discord
from redbot.core.i18n import Translator

from pylav import emojis
from pylav.types import CogT, InteractionT
from pylav.utils import AsyncIter

_ = Translator("PyLavShared", Path(__file__))


class DisconnectButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        super().__init__(
            style=style,
            emoji=emojis.POWER,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        if not await self.view.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, title=_("You are not authorized to perform this action.")
                ),
                ephemeral=True,
            )
            return
        player = self.view.source.current_player
        if not player:
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, title=_("No Player Available For Action - Try Refreshing.")
                ),
                ephemeral=True,
            )
            return
        if notify_channel := player.notify_channel:
            with contextlib.suppress(discord.HTTPException):
                await notify_channel.send(
                    embed=await self.cog.lavalink.construct_embed(
                        title=_("Bot Owner Action"), description=_("Player disconnected")
                    )
                )
        await player.disconnect(requester=interaction.user)

        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class StopTrackButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        super().__init__(
            style=style,
            emoji=emojis.STOP,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        if not await self.view.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, description=_("You are not authorized to perform this action.")
                ),
                ephemeral=True,
            )
            return
        player = self.view.source.current_player
        if not player:
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, description=_("No Player Available For Action - Try Refreshing.")
                ),
                ephemeral=True,
            )
            return

        await player.stop()
        if notify_channel := player.notify_channel:
            with contextlib.suppress(discord.HTTPException):
                await notify_channel.send(
                    embed=await self.cog.lavalink.construct_embed(
                        title=_("Bot Owner Action"), description=_("Player stopped.")
                    )
                )

        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class DisconnectAllButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        disconnect_type: Literal["all", "inactive"],
        style: discord.ButtonStyle,
        row: int = None,
    ):
        super().__init__(
            style=style,
            emoji=emojis.POWER,
            row=row,
        )

        self.disconnect_type = disconnect_type
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        if not await self.view.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, description=_("You are not authorized to perform this action.")
                ),
                ephemeral=True,
            )
            return

        players = (
            self.cog.lavalink.player_manager.connected_players
            if self.disconnect_type == "all"
            else self.cog.lavalink.player_manager.not_playing_players
        )
        if not players:
            await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    messageable=interaction, description=_("No Players Available For Action - Try Refreshing.")
                ),
                ephemeral=True,
            )
            return
        async for player in AsyncIter(players):
            if notify_channel := player.notify_channel:
                with contextlib.suppress(discord.HTTPException):
                    await notify_channel.send(
                        embed=await self.cog.lavalink.construct_embed(
                            title=_("Bot Owner Action"), description=_("Player disconnected")
                        )
                    )
            await player.disconnect(requester=interaction.user)

        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)
