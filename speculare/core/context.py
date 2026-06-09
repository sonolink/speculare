from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class _HasSend(Protocol):
    async def send(self, *args: Any, **kwargs: Any) -> Any: ...


class _Response(Protocol):
    def is_done(self) -> bool: ...
    async def send_message(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class _HasClient(Protocol):
    @property
    def client(self) -> Any: ...


@runtime_checkable
class _HasResponse(Protocol):
    @property
    def response(self) -> _Response: ...
    @property
    def followup(self) -> _HasSend: ...


class CommandContext:
    def __init__(self, original: Any) -> None:
        self.original = original

    @property
    def bot(self) -> Any:
        if isinstance(self.original, _HasClient):
            return self.original.client
        return self.original.bot

    async def send(self, *args: Any, **kwargs: Any) -> Any:
        if isinstance(self.original, _HasResponse):
            response = self.original.response
            if response.is_done():
                return await self.original.followup.send(*args, **kwargs)
            return await response.send_message(*args, **kwargs)
        return await self.original.send(*args, **kwargs)

    def __getattr__(self, item: str) -> Any:
        return getattr(self.original, item)
