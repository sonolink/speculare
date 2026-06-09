from collections.abc import Coroutine
from typing import Any

from .core.libraries.factory import DiscordBotFactory


class OptionalAwait:
    def __init__(self, func: Any) -> None:
        self.func = func

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        result = self.func(*args, **kwargs)
        if hasattr(result, "__await__"):
            return result
        return result


def actual_setup(bot: Any) -> None:
    from .features import EvalFeature

    EvalFeature().handle(bot)


async def async_setup(bot: DiscordBotFactory) -> None:
    actual_setup(bot)


def sync_setup(bot: DiscordBotFactory) -> None:
    actual_setup(bot)


def setup(bot: Any) -> Coroutine[Any, Any, None] | None:
    discord_bot = DiscordBotFactory(bot)

    if discord_bot.requires_async_setup:
        return async_setup(discord_bot)
    else:
        return sync_setup(discord_bot)
