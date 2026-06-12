from __future__ import annotations

import functools
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from enum import StrEnum
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Concatenate, Literal, Protocol, cast, overload

from .context import CommandContext

if TYPE_CHECKING:
    from .libraries._base import DiscordBot

log = logging.getLogger(__name__)

type AnyCoroutine[R] = Coroutine[Any, Any, R]
type _FeatureCallback[**P, R] = Callable[
    Concatenate[Any, CommandContext, P], AnyCoroutine[R]
]


class UserFeatureCallback[R](Protocol):
    def __call__(
        self,
        feature: Any,
        ctx: CommandContext,
        /,
        user: Any,
    ) -> AnyCoroutine[R]: ...


class MessageFeatureCallback[R](Protocol):
    def __call__(
        self,
        feature: Any,
        ctx: CommandContext,
        /,
        message: Any,
    ) -> AnyCoroutine[R]: ...


type FeatureCallback[**P, R] = (
    _FeatureCallback[P, R] | MessageFeatureCallback[R] | UserFeatureCallback[R]
)


class CommandType(StrEnum):
    SLASH = "slash"
    USER = "user"
    MESSAGE = "message"
    PREFIX = "prefix"
    HYBRID = "hybrid"


class FeatureCommand[**P, R]:
    def __init__(
        self,
        command_type: CommandType,
        *,
        name: str,
        callback: FeatureCallback[P, R],
        description: str | None = None,
        category: str | None = None,
    ) -> None:
        self.command_type = command_type
        self.name = name
        self.callback = callback
        self.description = description or ""
        self.category = category
        self._feature_instance: Any = None

    def _make_callback(self, bot: DiscordBot[Any]) -> Callable[..., AnyCoroutine[Any]]:
        @functools.wraps(cast(Callable[..., Any], self.callback))
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            log.debug(
                "Executing command %r | args=%s | kwargs=%s | types=%s",
                self.name,
                args,
                kwargs,
                {k: type(v).__name__ for k, v in kwargs.items()},
            )
            callback = cast(Callable[..., AnyCoroutine[Any]], self.callback)
            ctx, args, kwargs = bot.parse_args_and_kwargs(args, kwargs)
            return await callback(self._feature_instance, ctx, *args, **kwargs)

        return wrapper


class Feature:
    def __init_subclass__(
        cls,
        *,
        name: str,
        description: str,
        category: str | None = None,
    ) -> None:
        cls.name: str = name
        cls.description: str = description
        cls.category: str | None = category

    def __init__(self) -> None:
        # {category_name | None: {(command_name, command_type): feature_command_object}}
        self.__raw_commands__: dict[
            str | None, dict[tuple[str, CommandType], FeatureCommand[..., Any]]
        ] = defaultdict(dict)

        for _, value in getmembers(self):
            if not getattr(value, "__is_feature_command__", False):
                continue

            cmd: FeatureCommand[..., Any] = value.__command__
            self.__raw_commands__[cmd.category or self.category][
                (cmd.name, cmd.command_type)
            ] = cmd

        # {(category_name, command_type) | None: {(command_name, command_type): command_object}}
        self.__commands__: dict[
            tuple[str, CommandType] | None, dict[tuple[str, CommandType], Any]
        ] = defaultdict(dict)

        # {(category_name, command_type)}; stored separately since they may not be hashable
        self.__category_objects__: dict[tuple[str, CommandType], Any] = {}

    async def group_callback(
        self, ctx_interaction: Any, *args: Any, **kwargs: Any
    ) -> None:
        pass
        # placeholder callback for command groups, should never be called directly
        # raise NotImplementedError("This is a placeholder callback for command groups.")

    def handle(self, bot: DiscordBot[Any]) -> None:
        for category_name, commands in self.__raw_commands__.items():
            for (command_name, command_type), feature_cmd in commands.items():
                log.info(
                    "Handling command %r (type=%s, category=%r)",
                    command_name,
                    command_type,
                    category_name,
                )
                feature_cmd._feature_instance = self

                category_key: tuple[str, CommandType] | None = None
                category_object: Any = None

                if category_name is not None:
                    category_key = (category_name, command_type)
                    category_object = self._ensure_category_object(
                        bot, category_key, command_type
                    )

                command_object = self._register_command(
                    bot, feature_cmd, category_object
                )
                log.info("Registered command %r (type=%s)", command_name, command_type)

                self.__commands__[category_key][(command_name, command_type)] = (
                    command_object
                )

        log.debug("Final command registry: %s", dict(self.__commands__))

    def _ensure_category_object(
        self,
        bot: DiscordBot[Any],
        category_key: tuple[str, CommandType],
        command_type: CommandType,
    ) -> Any:
        if category_key in self.__commands__:
            return self.__category_objects__.get(category_key)

        category_name, _ = category_key
        category_object: Any = None

        if command_type is CommandType.PREFIX:
            category_object = bot.add_prefix_group(
                name=category_name,
                description=self.description,
                callback=self.group_callback,
                invoke_without_command=True,
            )
        elif command_type is CommandType.SLASH:
            category_object = bot.add_slash_group(
                name=category_name,
                description=self.description,
                callback=self.group_callback,
            )

        self.__category_objects__[category_key] = category_object
        self.__commands__[category_key] = {}
        return category_object

    def _register_command(
        self,
        bot: DiscordBot[Any],
        feature_cmd: FeatureCommand[..., Any],
        category_object: Any,
    ) -> Any:
        cb = feature_cmd._make_callback(bot)
        name = feature_cmd.name
        desc = feature_cmd.description

        match feature_cmd.command_type:
            case CommandType.PREFIX:
                return bot.add_prefix_command(
                    name=name, description=desc, callback=cb, parent=category_object
                )
            case CommandType.SLASH:
                return bot.add_slash_command(
                    name=name, description=desc, callback=cb, parent=category_object
                )
            case CommandType.USER:
                return bot.add_user_command(
                    name=name, description=desc, callback=cb, parent=category_object
                )
            case CommandType.MESSAGE:
                return bot.add_message_command(name=name, description=desc, callback=cb)
            case _:
                raise NotImplementedError(
                    f"Command type {feature_cmd.command_type!r} is not supported yet."
                )

    @overload
    @classmethod
    def command[**P, R](
        cls,
        command_type: Literal[
            CommandType.PREFIX, CommandType.HYBRID, CommandType.SLASH
        ],
        /,
        *,
        name: str | None = ...,
        description: str | None = ...,
        category: str | None = None,
    ) -> Callable[[_FeatureCallback[P, R]], _FeatureCallback[P, R]]: ...

    @overload
    @classmethod
    def command[R](
        cls,
        command_type: Literal[CommandType.MESSAGE],
        /,
        *,
        name: str | None = ...,
    ) -> Callable[[MessageFeatureCallback[R]], MessageFeatureCallback[R]]: ...

    @overload
    @classmethod
    def command[R](
        cls,
        command_type: Literal[CommandType.USER],
        /,
        *,
        name: str | None = ...,
    ) -> Callable[[UserFeatureCallback[R]], UserFeatureCallback[R]]: ...

    @overload
    @classmethod
    def command(
        cls,
        command_type: CommandType,
        /,
        *,
        name: str | None = ...,
        description: str | None = ...,
        category: str | None = None,
    ) -> Callable[[Any], Any]: ...

    @classmethod
    def command[**P, R](
        cls,
        command_type: CommandType,
        /,
        *,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
    ) -> Callable[[Any], Any]:
        def decorator(func: Any) -> Any:
            if getattr(func, "__is_feature_command__", False):
                raise ValueError("This function is already registered as a command.")

            func.__is_feature_command__ = True
            func.__command__ = FeatureCommand(
                command_type=command_type,
                name=name or getattr(func, "__name__", "") or "",
                callback=cast(FeatureCallback[..., Any], func),
                description=description or getattr(func, "__doc__", None),
                category=category,
            )
            return func

        return decorator
