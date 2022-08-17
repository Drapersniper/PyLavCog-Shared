from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import discord
from redbot.core.i18n import Translator

from pylav.types import BotT, CogT, InteractionT
from pylav.utils import PyLavContext

from pylavcogs_shared.ui.buttons.equalizer import EqualizerButton
from pylavcogs_shared.ui.buttons.generic import CloseButton, NavigateButton, RefreshButton
from pylavcogs_shared.ui.buttons.queue import (
    DecreaseVolumeButton,
    DisconnectButton,
    EmptyQueueButton,
    EnqueueButton,
    IncreaseVolumeButton,
    PauseTrackButton,
    PlayNowFromQueueButton,
    PreviousTrackButton,
    QueueHistoryButton,
    RemoveFromQueueButton,
    ResumeTrackButton,
    ShuffleButton,
    SkipTrackButton,
    StopTrackButton,
    ToggleRepeatButton,
    ToggleRepeatQueueButton,
)
from pylavcogs_shared.ui.menus.generic import BaseMenu
from pylavcogs_shared.ui.selectors.playlist import PlaylistSelectSelector
from pylavcogs_shared.ui.selectors.queue import EffectsSelector, QueueSelectTrack, SearchSelectTrack
from pylavcogs_shared.ui.sources.queue import EffectsPickerSource, QueuePickerSource, QueueSource, SearchPickerSource
from pylavcogs_shared.utils.decorators import is_dj_logic

_ = Translator("PyLavShared", Path(__file__))


class QueueMenu(BaseMenu):
    _source: QueueSource

    def __init__(
        self,
        cog: CogT,
        bot: BotT,
        source: QueueSource,
        original_author: discord.abc.User,
        *,
        delete_after_timeout: bool = True,
        timeout: int = 600,
        message: discord.Message = None,
        starting_page: int = 0,
        history: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cog=cog,
            bot=bot,
            source=source,
            delete_after_timeout=delete_after_timeout,
            timeout=timeout,
            message=message,
            starting_page=starting_page,
            **kwargs,
        )
        self.author = original_author
        self.is_history = history
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

        self.queue_disconnect = DisconnectButton(
            style=discord.ButtonStyle.red,
            row=1,
            cog=cog,
        )
        self.repeat_queue_button_on = ToggleRepeatQueueButton(
            style=discord.ButtonStyle.blurple,
            row=1,
            cog=cog,
        )
        self.repeat_button_on = ToggleRepeatButton(
            style=discord.ButtonStyle.blurple,
            row=1,
            cog=cog,
        )
        self.repeat_button_off = ToggleRepeatButton(
            style=discord.ButtonStyle.grey,
            row=1,
            cog=cog,
        )
        self.show_history_button = QueueHistoryButton(
            style=discord.ButtonStyle.grey,
            row=1,
            cog=cog,
        )

        self.close_button = CloseButton(
            style=discord.ButtonStyle.red,
            row=1,
            cog=cog,
        )
        self.clear_queue_button = EmptyQueueButton(style=discord.ButtonStyle.red, row=1, cog=cog)

        self.previous_track_button = PreviousTrackButton(
            style=discord.ButtonStyle.grey,
            row=2,
            cog=cog,
        )
        self.stop_button = StopTrackButton(
            style=discord.ButtonStyle.grey,
            row=2,
            cog=cog,
        )
        self.paused_button = PauseTrackButton(
            style=discord.ButtonStyle.blurple,
            row=2,
            cog=cog,
        )
        self.resume_button = ResumeTrackButton(
            style=discord.ButtonStyle.blurple,
            row=2,
            cog=cog,
        )
        self.skip_button = SkipTrackButton(
            style=discord.ButtonStyle.grey,
            row=2,
            cog=cog,
        )
        self.shuffle_button = ShuffleButton(
            style=discord.ButtonStyle.grey,
            row=2,
            cog=cog,
        )

        self.decrease_volume_button = DecreaseVolumeButton(
            style=discord.ButtonStyle.grey,
            row=3,
            cog=cog,
        )
        self.increase_volume_button = IncreaseVolumeButton(
            style=discord.ButtonStyle.grey,
            row=3,
            cog=cog,
        )
        self.equalize_button = EqualizerButton(
            style=discord.ButtonStyle.grey,
            row=3,
            cog=cog,
        )

        self.enqueue_button = EnqueueButton(
            cog=cog,
            style=discord.ButtonStyle.green,
            row=3,
        )
        self.remove_from_queue_button = RemoveFromQueueButton(
            cog=cog,
            style=discord.ButtonStyle.red,
            row=3,
        )
        self.play_now_button = PlayNowFromQueueButton(
            cog=cog,
            style=discord.ButtonStyle.blurple,
            row=4,
        )

    async def prepare(self):
        self.clear_items()
        max_pages = self.source.get_max_pages()
        is_dj = await is_dj_logic(self.ctx)
        if not self.is_history:
            self.add_item(self.close_button)
            self.add_item(self.queue_disconnect)
            self.add_item(self.clear_queue_button)

        self.add_item(self.first_button)
        self.add_item(self.backward_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_button)
        self.add_item(self.refresh_button)

        if not self.is_history:
            self.repeat_button_on.disabled = False
            self.repeat_button_off.disabled = False
            self.repeat_queue_button_on.disabled = False
            self.clear_queue_button.disabled = False
            self.show_history_button.disabled = False

        self.forward_button.disabled = False
        self.backward_button.disabled = False
        self.first_button.disabled = False
        self.last_button.disabled = False
        self.refresh_button.disabled = False

        if max_pages == 2:
            self.first_button.disabled = True
            self.last_button.disabled = True
        elif max_pages == 1:
            self.forward_button.disabled = True
            self.backward_button.disabled = True
            self.first_button.disabled = True
            self.last_button.disabled = True
        if self.is_history:
            return

        self.previous_track_button.disabled = False
        self.paused_button.disabled = False
        self.resume_button.disabled = False
        self.stop_button.disabled = False
        self.skip_button.disabled = False
        self.shuffle_button.disabled = False

        self.decrease_volume_button.disabled = False
        self.increase_volume_button.disabled = False
        self.equalize_button.disabled = False
        self.enqueue_button.disabled = False
        self.remove_from_queue_button.disabled = False
        self.play_now_button.disabled = False

        self.add_item(self.previous_track_button)
        self.add_item(self.stop_button)

        if (player := self.cog.lavalink.get_player(self.source.guild_id)) and is_dj is not False:
            await player.config.update()
            if player.paused:
                self.add_item(self.resume_button)
            else:
                self.add_item(self.paused_button)
            if player.queue.empty():
                self.shuffle_button.disabled = True
                self.remove_from_queue_button.disabled = True
                self.play_now_button.disabled = True
                self.clear_queue_button.disabled = True
            if not player.current:
                self.equalize_button.disabled = True
                self.stop_button.disabled = True
                self.shuffle_button.disabled = True
                self.previous_track_button.disabled = True
                self.decrease_volume_button.disabled = True
                self.increase_volume_button.disabled = True
            if player.history.empty():
                self.previous_track_button.disabled = True
                self.show_history_button.disabled = True
            else:
                self.add_item(self.show_history_button)
            if player.config.repeat_current:
                self.add_item(self.repeat_button_on)
            elif player.config.repeat_queue:
                self.add_item(self.repeat_queue_button_on)
            else:
                self.add_item(self.repeat_button_off)

        else:
            self.forward_button.disabled = True
            self.backward_button.disabled = True
            self.first_button.disabled = True
            self.last_button.disabled = True
            self.stop_button.disabled = True
            self.skip_button.disabled = True
            self.previous_track_button.disabled = True
            self.repeat_button_off.disabled = True
            self.show_history_button.disabled = True
            self.shuffle_button.disabled = True
            self.decrease_volume_button.disabled = True
            self.increase_volume_button.disabled = True
            self.resume_button.disabled = True
            self.repeat_button_on.disabled = True
            self.equalize_button.disabled = True
            self.enqueue_button.disabled = True
            self.remove_from_queue_button.disabled = True
            self.play_now_button.disabled = True
            self.repeat_queue_button_on.disabled = True
            self.clear_queue_button.disabled = True

            self.add_item(self.resume_button)
            self.add_item(self.repeat_button_off)
        self.add_item(self.skip_button)
        self.add_item(self.shuffle_button)
        self.add_item(self.decrease_volume_button)
        self.add_item(self.increase_volume_button)
        self.add_item(self.equalize_button)
        self.add_item(self.enqueue_button)
        self.add_item(self.remove_from_queue_button)
        self.add_item(self.play_now_button)
        self.equalize_button.disabled = True
        if is_dj is False:
            self.queue_disconnect.disabled = True

    @property
    def source(self) -> QueueSource:
        return self._source

    async def start(self, ctx: PyLavContext | InteractionT):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)

        self.ctx = ctx
        await self.send_initial_message(ctx)


class QueuePickerMenu(BaseMenu):
    _source: QueuePickerSource

    def __init__(
        self,
        cog: CogT,
        bot: BotT,
        source: QueuePickerSource,
        original_author: discord.abc.User,
        *,
        delete_after_timeout: bool = True,
        timeout: int = 120,
        message: discord.Message = None,
        starting_page: int = 0,
        menu_type: Literal["remove", "play"],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cog=cog,
            bot=bot,
            source=source,
            delete_after_timeout=delete_after_timeout,
            timeout=timeout,
            message=message,
            starting_page=starting_page,
            **kwargs,
        )
        self.author = original_author
        self.menu_type = menu_type
        self.forward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=1,
            row=4,
            cog=cog,
        )
        self.backward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=-1,
            row=4,
            cog=cog,
        )
        self.first_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            direction=0,
            row=4,
            cog=cog,
        )
        self.last_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            direction=self.source.get_max_pages,
            row=4,
            cog=cog,
        )
        self.close_button = CloseButton(
            style=discord.ButtonStyle.red,
            row=4,
            cog=cog,
        )
        self.refresh_button = RefreshButton(
            style=discord.ButtonStyle.grey,
            row=4,
            cog=cog,
        )
        self.select_view: QueueSelectTrack | None = None
        self.add_item(self.first_button)
        self.add_item(self.backward_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_button)

    @property
    def source(self) -> QueuePickerSource:
        return self._source

    async def start(self, ctx: PyLavContext | InteractionT):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)
        self.ctx = ctx
        await self.send_initial_message(ctx)

    async def send_initial_message(self, ctx: PyLavContext | InteractionT):
        await self._source.get_page(0)
        self.ctx = ctx
        embed = await self.source.format_page(self, [])
        await self.prepare()
        self.message = await ctx.send(embed=embed, view=self, ephemeral=True)
        return self.message

    async def show_page(self, page_number: int, interaction: InteractionT):
        await self._source.get_page(page_number)
        await self.prepare()
        self.current_page = page_number
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self)
        elif self.message is not None:
            await self.message.edit(view=self)

    async def prepare(self):
        self.clear_items()
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
        self.add_item(self.close_button)
        self.add_item(self.first_button)
        self.add_item(self.backward_button)
        self.add_item(self.forward_button)
        self.add_item(self.last_button)
        if self.source.select_options:
            from pylavcogs_shared.ui.selectors.queue import QueueSelectTrack

            options = self.source.select_options
            if self.menu_type == "remove":
                title = _("Select Track To Remove")
            else:
                title = _("Select Track To Play Now")
            self.remove_item(self.select_view)
            self.select_view = QueueSelectTrack(
                options=options,
                cog=self.cog,
                placeholder=title,
                interaction_type=self.menu_type,
                mapping=self.source.select_mapping,
            )
            self.add_item(self.select_view)
        if self.select_view and not self.source.select_options:
            self.remove_item(self.select_view)
            self.select_view = None


class EffectPickerMenu(BaseMenu):
    source: EffectsPickerSource

    def __init__(
        self,
        cog: CogT,
        bot: BotT,
        source: EffectsPickerSource,
        original_author: discord.abc.User,
        *,
        clear_buttons_after: bool = False,
        delete_after_timeout: bool = True,
        timeout: int = 120,
        message: discord.Message = None,
        starting_page: int = 0,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cog,
            bot,
            source,
            clear_buttons_after=clear_buttons_after,
            delete_after_timeout=delete_after_timeout,
            timeout=timeout,
            message=message,
            starting_page=starting_page,
            **kwargs,
        )
        self.forward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=1,
            row=4,
            cog=cog,
        )
        self.backward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=-1,
            row=4,
            cog=cog,
        )
        self.first_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            direction=0,
            row=4,
            cog=cog,
        )
        self.last_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            direction=self.source.get_max_pages,
            row=4,
            cog=cog,
        )
        self.refresh_button = RefreshButton(
            style=discord.ButtonStyle.grey,
            row=4,
            cog=cog,
        )
        self.close_button = CloseButton(
            style=discord.ButtonStyle.red,
            row=4,
            cog=cog,
        )
        self.select_view: PlaylistSelectSelector | None = None
        self.author = original_author

    async def prepare(self):
        self.clear_items()
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
        options = self.source.select_options
        self.remove_item(self.select_view)
        self.select_view = EffectsSelector(
            options, self.cog, _("Pick An Effect Preset To Apply"), mapping=self.source.select_mapping
        )
        self.add_item(self.select_view)

    async def start(self, ctx: PyLavContext | InteractionT):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)
        self.ctx = ctx
        await self.send_initial_message(ctx)

    async def show_page(self, page_number: int, interaction: InteractionT):
        await self.prepare()
        self.current_page = page_number
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self)
        elif self.message is not None:
            await self.message.edit(view=self)


class SearchPickerMenu(BaseMenu):
    source: SearchPickerSource

    def __init__(
        self,
        cog: CogT,
        source: SearchPickerSource,
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
            bot=cog.bot,
            source=source,
            clear_buttons_after=clear_buttons_after,
            delete_after_timeout=delete_after_timeout,
            timeout=timeout,
            message=message,
            starting_page=starting_page,
            **kwargs,
        )
        self.cog = cog
        self.bot = cog.bot
        self.author = original_author
        self.forward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=1,
            row=4,
            cog=cog,
        )
        self.backward_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING TRIANGLE}\N{VARIATION SELECTOR-16}",
            direction=-1,
            row=4,
            cog=cog,
        )
        self.first_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}",
            direction=0,
            row=4,
            cog=cog,
        )
        self.last_button = NavigateButton(
            style=discord.ButtonStyle.grey,
            emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}",
            direction=self.source.get_max_pages,
            row=4,
            cog=cog,
        )
        self.close_button = CloseButton(
            style=discord.ButtonStyle.red,
            row=4,
            cog=cog,
        )
        self.select_view: SearchSelectTrack | None = None
        self.name = None
        self.url = None
        self.scope = None
        self.add_tracks = set()
        self.remove_tracks = set()

        self.clear = None
        self.delete = None
        self.cancelled = True
        self.done = False
        self.update = False
        self.queue = None
        self.dedupe = None

        self.add_item(self.done_button)
        self.add_item(self.close_button)
        self.add_item(self.delete_button)
        self.add_item(self.clear_button)
        self.add_item(self.update_button)
        self.add_item(self.name_button)
        self.add_item(self.url_button)
        self.add_item(self.add_button)
        self.add_item(self.remove_button)
        self.add_item(self.download_button)

        self.add_item(self.playlist_enqueue_button)
        self.add_item(self.playlist_info_button)
        self.add_item(self.queue_button)
        self.add_item(self.dedupe_button)

    async def start(self, ctx: PyLavContext | InteractionT):
        if isinstance(ctx, discord.Interaction):
            ctx = await self.cog.bot.get_context(ctx)
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=True)
        self.ctx = ctx
        await self.send_initial_message(ctx)

    async def show_page(self, page_number: int, interaction: InteractionT):
        self.current_page = page_number
        kwargs = await self.get_page(self.current_page)
        await self.prepare()
        if not interaction.response.is_done():
            await interaction.response.edit_message(**kwargs, view=self)
        else:
            await interaction.followup.edit(**kwargs, view=self)

    async def prepare(self):
        self.clear_items()
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
        if self.source.select_options:
            options = self.source.select_options
            title = _("Select Track To Enqueue")
            self.remove_item(self.select_view)
            self.select_view = SearchSelectTrack(options, self.cog, title, self.source.select_mapping)
            self.add_item(self.select_view)
        if self.select_view and not self.source.select_options:
            self.remove_item(self.select_view)
            self.select_view = None

        self.add_item(self.close_button)
