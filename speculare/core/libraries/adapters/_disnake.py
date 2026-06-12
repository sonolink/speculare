from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, cast

import disnake
from disnake.ext import commands

from .._base import DiscordBot

__all__ = ()


class DisnakeBot(DiscordBot[commands.Bot]):
    _bot: commands.Bot
    cls = commands.Bot

    def __init__(self, bot: commands.Bot, /) -> None:
        super().__init__(bot)
        self._cog: commands.Cog = commands.Cog.__new__(commands.Cog)
        self._cog.__cog_name__ = "speculare"

    def parse_args_and_kwargs(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> tuple[Any, tuple[Any, ...], dict[str, Any]]:
        for i, arg in enumerate(args):
            if isinstance(arg, (disnake.Interaction, commands.Context)):
                kwargs.pop("self", None)
                return cast(Any, arg), args[i + 1 :], kwargs
        raise ValueError("Expected at least one positional argument for context.")

    def _inject_fake_interaction(
        self, callback: Callable[..., Any]
    ) -> Callable[..., Any]:
        sig = inspect.signature(callback)
        parameters = list(sig.parameters.values())
        if not parameters:
            return callback

        async def wrapper(ctx: commands.Context[Any], *args: Any, **kwargs: Any) -> Any:
            return await callback(ctx, *args, **kwargs)

        parameters[1] = parameters[1].replace(
            annotation=disnake.ApplicationCommandInteraction,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        wrapper.__signature__ = sig.replace(parameters=parameters)  # pyright: ignore[reportFunctionMemberAccess]
        wrapper.__qualname__ = callback.__qualname__
        wrapper.__name__ = callback.__name__
        return wrapper

    def add_prefix_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.Group[Any, ..., Any]:
        group: commands.Group[Any, ..., Any] = commands.Group(
            callback,
            name=name,
            description=description,
            **extras,
        )
        group.cog = self._cog
        self._bot.add_command(group)  # type: ignore[arg-type]
        return group

    def add_prefix_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: commands.Group[Any, ..., Any] | None = None,
        **extras: Any,
    ) -> commands.Command[Any, Any, Any]:
        cmd = commands.Command(
            callback,
            name=name,
            description=description,
            **extras,
        )
        cmd.cog = self._cog
        (parent or self._bot).add_command(cmd)  # type: ignore[arg-type]
        return cmd

    def add_slash_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.InvokableSlashCommand:
        return self._bot.slash_command(
            name=name,
            description=description,
            **extras
        )(self._inject_fake_interaction(callback))

    def add_slash_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: commands.InvokableSlashCommand | None = None,
        **extras: Any,
    ) -> commands.InvokableSlashCommand | commands.SubCommand:
        callback = self._inject_fake_interaction(callback)
        if parent:
            return parent.sub_command(
                name=name,
                description=description,
                **extras,
            )(callback)
        return self._bot.slash_command(
            name=name,
            description=description,
            **extras
        )(callback)

    def add_user_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.InvokableUserCommand:
        cmd = commands.InvokableUserCommand(func=callback, name=name, **extras)
        self._bot.add_user_command(cmd)
        return cmd

    def add_message_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.InvokableMessageCommand:
        cmd = commands.InvokableMessageCommand(func=callback, name=name, **extras)
        self._bot.add_message_command(cmd)
        return cmd
