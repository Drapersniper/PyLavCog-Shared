from __future__ import annotations

from pathlib import Path

import discord
from redbot.core.i18n import Translator

from pylav import emojis
from pylav.types import CogT, InteractionT

_ = Translator("PyLavShared", Path(__file__))


class PreviousTrackButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.PREVIOUS,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_previous.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class StopTrackButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.STOP,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_stop.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class PauseTrackButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.PAUSE,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_pause.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class ResumeTrackButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.PLAY,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_resume.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class SkipTrackButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.NEXT,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_skip.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class IncreaseVolumeButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.VOLUMEUP,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_volume_change_by.callback(self.cog, interaction, change_by=5)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class DecreaseVolumeButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.VOLUMEDOWN,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_volume_change_by.callback(self.cog, interaction, change_by=-5)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class ToggleRepeatButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.LOOP,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        player = self.cog.lavalink.get_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    description="Not connected to a voice channel.", messageable=interaction
                ),
                ephemeral=True,
            )
        repeat_queue = bool(player.config.repeat_current)
        await self.cog.command_repeat.callback(self.cog, interaction, queue=repeat_queue)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class ToggleRepeatQueueButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.REPEAT,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        player = self.cog.lavalink.get_player(interaction.guild)
        if not player:
            return await interaction.response.send_message(
                embed=await self.cog.lavalink.construct_embed(
                    description="Not connected to a voice channel.", messageable=interaction
                ),
                ephemeral=True,
            )
        repeat_queue = bool(player.config.repeat_current)
        await self.cog.command_repeat.callback(self.cog, interaction, queue=repeat_queue)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class ShuffleButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.RANDOM,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_shuffle.callback(self.cog, interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class DisconnectButton(discord.ui.Button):
    def __init__(self, cog: CogT, style: discord.ButtonStyle, row: int = None):
        super().__init__(
            style=style,
            emoji=emojis.POWER,
            row=row,
        )
        self.cog = cog

    async def callback(self, interaction: InteractionT):
        await self.cog.command_disconnect.callback(self.cog, interaction)
        self.view.stop()
        await self.view.on_timeout()


class EnqueueButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        self.cog = cog
        super().__init__(
            style=style,
            emoji=emojis.PLUS,
            row=row,
        )

    async def callback(self, interaction: InteractionT):
        from pylavcogs_shared.ui.modals.queue import EnqueueModal

        modal = EnqueueModal(self.cog, _("What do you want to enqueue?"))
        await interaction.response.send_modal(modal)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class RemoveFromQueueButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        self.cog = cog
        super().__init__(
            style=style,
            emoji=emojis.MINUS,
            row=row,
        )

    async def callback(self, interaction: InteractionT):
        from pylavcogs_shared.ui.menus.queue import QueuePickerMenu
        from pylavcogs_shared.ui.sources.queue import QueuePickerSource

        picker = QueuePickerMenu(
            bot=self.cog.bot,
            cog=self.cog,
            source=QueuePickerSource(guild_id=interaction.guild.id, cog=self.cog),
            delete_after_timeout=True,
            starting_page=0,
            menu_type="remove",
            original_author=interaction.user,
        )
        await picker.start(interaction)
        await picker.wait()
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class PlayNowFromQueueButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        self.cog = cog
        super().__init__(
            style=style,
            emoji=emojis.MUSICALNOTE,
            row=row,
        )

    async def callback(self, interaction: InteractionT):
        from pylavcogs_shared.ui.menus.queue import QueuePickerMenu
        from pylavcogs_shared.ui.sources.queue import QueuePickerSource

        picker = QueuePickerMenu(
            bot=self.cog.bot,
            cog=self.cog,
            source=QueuePickerSource(guild_id=interaction.guild.id, cog=self.cog),
            delete_after_timeout=True,
            starting_page=0,
            menu_type="play",
            original_author=interaction.user,
        )
        await picker.start(interaction)
        await picker.wait()
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)


class EffectPickerButton(discord.ui.Button):
    def __init__(
        self,
        cog: CogT,
        style: discord.ButtonStyle,
        row: int = None,
    ):
        self.cog = cog
        super().__init__(
            style=style,
            emoji=emojis.SETTINGS,
            row=row,
        )

    async def callback(self, interaction: InteractionT):
        from pylavcogs_shared.ui.menus.queue import EffectPickerMenu
        from pylavcogs_shared.ui.sources.queue import EffectsPickerSource

        await EffectPickerMenu(
            cog=self.cog,
            bot=self.cog.bot,
            source=EffectsPickerSource(guild_id=interaction.guild.id, cog=self.cog),
            delete_after_timeout=True,
            clear_buttons_after=False,
            starting_page=0,
            menu_type="play",
            original_author=interaction.user,
        ).start(interaction)
        await self.view.prepare()
        kwargs = await self.view.get_page(self.view.current_page)
        await (await interaction.original_message()).edit(view=self.view, **kwargs)
