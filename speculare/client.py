from __future__ import annotations

from typing import Any

from core.libraries.factory import DiscordBotFactory


class Speculare:
    def __init__(self, bot: Any, /) -> None:
        self._bot = DiscordBotFactory(bot)
