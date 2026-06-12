from __future__ import annotations

from collections.abc import Callable
from typing import Any

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

    def _register_prefix(self, cmd: commands.Command[Any, Any, Any]) -> None:
        cmd.cog = self._cog

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
        self._bot.add_command(group)
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
        cmd = commands.Command(callback, name=name, description=description, **extras)
        cmd.cog = self._cog
        (parent or self._bot).add_command(cmd)
        return cmd

    def _inject_fake_interaction(
        self, callback: Callable[..., Any]
    ) -> Callable[..., Any]:
        from disnake import ApplicationCommandInteraction

        async def wrapper(
            ctx,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            return await callback(ctx, *args, **kwargs)

        import inspect

        sig = inspect.signature(callback)
        params = sig.parameters
        if not params:
            return callback

        # [self, ctx: CommandContext, ...]
        new_parameters: list[inspect.Parameter] = list(params.values())
        # ctx: CommandContext -> ctx: ApplicationCommandInteraction
        new_parameters[1] = new_parameters[1].replace(
            annotation=ApplicationCommandInteraction,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
        )
        wrapper.__signature__ = sig.replace(parameters=new_parameters)  # pyright: ignore[reportFunctionMemberAccess]
        wrapper.__qualname__ = callback.__qualname__
        wrapper.__name__ = callback.__name__
        return wrapper

    def parse_args_and_kwargs(
        self, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        print("parse_args_and_kwargs called with args", args, "and kwargs", kwargs)
        if not args:
            raise ValueError("Expected at least one positional argument for context.")

        ctx_interaction_arg: Any = None
        remaining_args: tuple[Any, ...] = ()
        for i, arg in enumerate(args):
            if isinstance(arg, (disnake.Interaction, commands.Context)):
                ctx_interaction_arg = arg  # type: ignore
                remaining_args = args[i + 1 :]
                break

        if ctx_interaction_arg is None:
            raise ValueError("Expected at least one positional argument for context.")

        # ???????????????????????????????
        if "self" in kwargs:
            kwargs.pop("self")

        print(
            "parse_args_and_kwargs returning ctx_interaction_arg",
            ctx_interaction_arg,
            "remaining_args",
            remaining_args,
            "kwargs",
            kwargs,
        )
        return ctx_interaction_arg, remaining_args, kwargs

    def add_slash_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.InvokableSlashCommand:
        callback = self._inject_fake_interaction(callback)
        group = self._bot.slash_command(name=name, description=description, **extras)(
            callback
        )
        return group

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
            return parent.sub_command(name=name, description=description, **extras)(
                callback
            )
        else:
            return self._bot.slash_command(
                name=name, description=description, **extras
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
