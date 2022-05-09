from __future__ import annotations

import asyncio
from pathlib import Path

from redbot.core.i18n import Translator

from pylav.types import CogT
from pylav.utils import PyLavContext

from pylavcogs_shared.types import GenericT
from pylavcogs_shared.ui.menus.generic import EntryPickerMenu
from pylavcogs_shared.ui.selectors.generic import EntrySelectSelector
from pylavcogs_shared.ui.sources.generic import EntryPickerSource

_ = Translator("PyLavShared", Path(__file__))


async def maybe_prompt_for_entry(
    cog: CogT, context: PyLavContext, entries: list[GenericT], message_str: str, selector_text: str
) -> GenericT:
    if len(entries) > 1:
        entry_picker = EntryPickerMenu(
            cog=cog,
            bot=cog.bot,
            source=EntryPickerSource(
                guild_id=context.guild.id,
                cog=cog,
                pages=entries,
                message_str=message_str,
            ),
            selector_cls=EntrySelectSelector,
            delete_after_timeout=True,
            clear_buttons_after=True,
            starting_page=0,
            selector_text=selector_text,
            original_author=context.interaction.user if context.interaction else context.author,
        )

        await entry_picker.start(context)
        try:
            await entry_picker.wait_for_response()
            entry = entry_picker.result
        except asyncio.TimeoutError:
            entry = None
    else:
        entry = entries[0]
    return entry
