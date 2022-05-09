from __future__ import annotations

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
        self.view.bot.dispatch("red_audio_audio_disconnect", player.guild)
        self.cog.update_player_lock(player, False)
        player.queue = []
        player.store("playing_song", None)
        player.store("autoplay_notified", False)
        channel_id = player.fetch("notify_channel")
        notify_channel = player.guild.get_channel_or_thread(channel_id)
        if player.equalizer.changed:
            async with self.cog.config.custom("EQUALIZER", player.guild.id).all() as eq_data:
                eq_data["eq_bands"] = player.equalizer.get()
                eq_data["name"] = player.equalizer.name
        await player.stop()
        await player.disconnect()
        if notify_channel:
            # TODO Use Text input to get a message from owner to send
            await self.cog.send_embed_msg(
                notify_channel, title=_("Bot Owner Action"), description=_("Player disconnected.")
            )
        self.cog._ll_guild_updates.discard(player.guild.id)  # noqa
        await self.cog.api_interface.persistent_queue_api.drop(player.guild.id)
        await self.cog.clean_up_guild_config(
            "last_known_vc_and_notify_channels",
            "last_known_track",
            "currently_auto_playing_in",
            guild_ids=[player.guild.id],
        )

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
        if player.equalizer.changed:
            async with self.cog.config.custom("EQUALIZER", player.guild.id).all() as eq_data:
                eq_data["eq_bands"] = player.equalizer.get()
                eq_data["name"] = player.equalizer.name
        player.queue = []
        player.store("playing_song", None)
        player.store("prev_requester", None)
        player.store("prev_song", None)
        player.store("requester", None)
        player.store("autoplay_notified", False)
        await player.stop()
        channel_id = player.fetch("notify_channel")
        if notify_channel := player.guild.get_channel_or_thread(channel_id):
            # TODO Use Text input to get a message from owner to send?
            await self.cog.send_embed_msg(notify_channel, title=_("Bot Owner Action"), description=_("Player stopped."))
        await self.cog.api_interface.persistent_queue_api.drop(player.guild.id)
        await self.cog.clean_up_guild_config(
            "last_known_vc_and_notify_channels",
            "last_known_track",
            "currently_auto_playing_in",
            guild_ids=[player.guild.id],
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
            self.view.bot.dispatch("red_audio_audio_disconnect", player.guild)
            self.cog.update_player_lock(player, False)
            player.queue = []
            channel_id = player.fetch("notify_channel")
            notify_channel = player.guild.get_channel_or_thread(channel_id)
            if player.equalizer.changed:
                async with self.cog.config.custom("EQUALIZER", player.guild.id).all() as eq_data:
                    eq_data["eq_bands"] = player.equalizer.get()
                    eq_data["name"] = player.equalizer.name
            await player.stop(requester=interaction.user)
            await player.disconnect(requester=interaction.user)
            if notify_channel:
                # TODO Use Text input to get a message from owner to send
                await self.cog.send_embed_msg(
                    notify_channel,
                    title=_("Bot Owner Action"),
                    description=_("Player disconnected."),
                )
            self.cog._ll_guild_updates.discard(player.guild.id)  # noqa
            await self.cog.api_interface.persistent_queue_api.drop(player.guild.id)
            await self.cog.clean_up_guild_config(
                "last_known_vc_and_notify_channels",
                "last_known_track",
                "currently_auto_playing_in",
                guild_ids=[player.guild.id],
            )
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)
