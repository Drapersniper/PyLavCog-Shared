from __future__ import annotations

from pathlib import Path

import discord
from redbot.core.i18n import Translator

from pylav.constants import SUPPORTED_SOURCES
from pylav.sql.models import NodeModel

_ = Translator("PyLavShared", Path(__file__))


class SourceOption(discord.SelectOption):
    def __init__(self, name: str, description: str | None, value: str):
        super().__init__(
            label=name,
            description=description,
            value=value,
        )


SOURCE_OPTIONS = [SourceOption(name=source, description=None, value=source) for source in SUPPORTED_SOURCES]


class NodeOption(discord.SelectOption):
    @classmethod
    async def from_node(cls, node: NodeModel, index: int):
        return cls(
            label=f"{index + 1}. {node.name}",
            description=_("ID: {} || SSL: {} || Search-only: {}").format(node.id, node.ssl, node.search_only),
            value=f"{node.id}",
        )
