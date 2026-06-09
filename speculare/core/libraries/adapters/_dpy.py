from __future__ import annotations

from collections.abc import Callable
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from .._base import DiscordBot


class DpyBot(DiscordBot[commands.Bot]):
    _bot: commands.Bot
    cls = commands.Bot
    requires_async_setup = True

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

    def add_slash_group(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> app_commands.Group:
        group = app_commands.Group(name=name, description=description, **extras)
        self._bot.tree.add_command(group)
        return group

    def add_slash_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        parent: app_commands.Group | None = None,
        **extras: Any,
    ) -> app_commands.Command[Any, ..., Any]:
        cmd = app_commands.Command(
            callback=callback, name=name, description=description, **extras
        )
        (parent or self._bot.tree).add_command(cmd)
        return cmd

    def add_user_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> app_commands.ContextMenu:
        cmd = app_commands.ContextMenu(
            callback=callback,
            name=name,
            type=discord.AppCommandType.user,
            **extras,
        )
        self._bot.tree.add_command(cmd)
        return cmd

    def add_message_command(
        self,
        *,
        name: str,
        description: str,
        callback: Callable[..., Any],
        **extras: Any,
    ) -> app_commands.ContextMenu:
        cmd = app_commands.ContextMenu(
            callback=callback,
            name=name,
            type=discord.AppCommandType.message,
            **extras,
        )
        self._bot.tree.add_command(cmd)
        return cmd
