from __future__ import annotations

from collections.abc import Callable
from typing import Any

import discord
from discord.ext import commands

from .._base import DiscordBot


class PseudoCog(commands.Cog):
    pass


class PycordBot(DiscordBot[commands.Bot]):
    cls = commands.Bot
    _bot: commands.Bot

    def __init__(self, bot: commands.Bot, /) -> None:
        super().__init__(bot)
        self._cog = PseudoCog(bot)

    def add_prefix_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> commands.Group[Any, Any, Any]:
        group: commands.Group[Any, Any, Any] = commands.Group(
            func=callback, name=name, description=description, **extras
        )
        group.cog = self._cog
        self._bot.add_command(group)  # pyright: ignore[reportUnknownMemberType]
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
        _parent = parent or self._bot  # pyright: ignore[reportAssignmentType]

        cmd = commands.Command(callback, name=name, description=description, **extras)
        cmd.cog = self._cog
        _parent.add_command(  # pyright: ignore[reportUnknownMemberType]
            cmd
        )
        return cmd

    def _inject_fake_ctx(self, callback: Callable[..., Any]) -> Callable[..., Any]:
        import inspect

        from discord import ApplicationContext

        from ...context import CommandContext

        sig = inspect.signature(callback)
        params = sig.parameters
        if not params:
            return callback

        new_parameters: list[inspect.Parameter] = []
        for value in params.values():
            if value.annotation is CommandContext:
                value = value.replace(annotation=ApplicationContext)

            new_parameters.append(value)

        callback.__signature__ = sig.replace(parameters=new_parameters)  # pyright: ignore[reportFunctionMemberAccess]
        return callback

    def add_slash_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> discord.SlashCommandGroup:
        group = discord.SlashCommandGroup(name=name, description=description)
        group.cog = self._cog
        self._bot.add_application_command(group)  # pyright: ignore[reportUnknownMemberType]
        return group

    def add_slash_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: discord.SlashCommandGroup | None = None,
        **extras: Any,
    ) -> discord.SlashCommand:
        callback = self._inject_fake_ctx(callback)
        cmd = discord.SlashCommand(
            func=callback, name=name, description=description, **extras
        )
        cmd.cog = self._cog
        if parent is not None:
            parent.add_command(cmd)
        else:
            self._bot.add_application_command(cmd)  # pyright: ignore[reportUnknownMemberType]

        return cmd

    def add_user_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> discord.UserCommand:
        cmd = discord.UserCommand(
            func=callback, name=name, description=description, **extras
        )
        cmd.cog = self._cog
        self._bot.add_application_command(cmd)  # pyright: ignore[reportUnknownMemberType]
        return cmd

    def add_message_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> discord.MessageCommand:
        cmd = discord.MessageCommand(
            func=callback, name=name, description=description, **extras
        )
        cmd.cog = self._cog
        self._bot.add_application_command(cmd)  # pyright: ignore[reportUnknownMemberType]
        return cmd
