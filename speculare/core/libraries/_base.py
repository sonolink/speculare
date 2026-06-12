from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class DiscordBot[ClientT: Any](ABC):
    cls: type[ClientT]
    requires_async_setup: bool = False

    __slots__ = ("_bot",)

    def __init__(self, bot: ClientT, /) -> None:
        self._bot: ClientT = bot

    def parse_args_and_kwargs(
        self, *args: Any, **kwargs: Any
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        return args, kwargs

    @abstractmethod
    def add_prefix_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> Any: ...

    @abstractmethod
    def add_prefix_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: Any | None = None,
        **extras: Any,
    ) -> Any: ...

    @abstractmethod
    def add_slash_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> Any: ...

    @abstractmethod
    def add_slash_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: Any | None = None,
        **extras: Any,
    ) -> Any: ...

    @abstractmethod
    def add_user_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> Any: ...

    @abstractmethod
    def add_message_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> Any: ...
