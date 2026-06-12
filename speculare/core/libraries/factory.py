from __future__ import annotations

import importlib.metadata
import logging
import os
import sys
from typing import Any, ClassVar, Literal, cast

from packaging.version import Version

from ...errors import FrameworkClientMismatch, FrameworkImportError
from ._base import DiscordBot

FrameworkLiteral = Literal["discord.py", "pycord", "disnake", "nextcord"]


_log = logging.getLogger(__name__)


class DiscordBotFactory:
    _available: dict[str, bool]

    _FRAMEWORK_DATA: ClassVar[dict[str, dict[str, str]]] = {
        "discord.py": {"pkg": "discord.py", "import_name": "discord", "min": "2.7"},
        "pycord": {"pkg": "py-cord", "import_name": "discord", "min": "2.8"},
        "disnake": {"pkg": "disnake", "import_name": "disnake", "min": "2.12"},
        "nextcord": {"pkg": "nextcord", "import_name": "nextcord", "min": "3.1.1"},
    }

    def __new__(cls, bot: Any) -> Any:
        self = super().__new__(cls)
        self._available = {}

        pkg_to_providers = dict(importlib.metadata.packages_distributions())
        known_pkgs = {self._normalize(d["pkg"]) for d in self._FRAMEWORK_DATA.values()}

        for name, data in self._FRAMEWORK_DATA.items():
            self._available[name] = self._check_available(
                data, pkg_to_providers, known_pkgs
            )
        return self.create(bot)

    def detect_framework(self) -> FrameworkLiteral:
        if env := os.environ.get("SONOLINK_FRAMEWORK"):
            return cast(FrameworkLiteral, env)

        available = [name for name, ok in self._available.items() if ok]

        if not available:
            raise RuntimeError(
                "No supported framework detected meeting the minimum version requirements.\n"
                "Ensure one of the following is installed: "
                "discord.py >= 2.7, py-cord >= 2.8, disnake >= 2.12 or nextcord >= 3.1.1"
            )

        if len(available) > 1:
            imported = [
                name
                for name in available
                if self._FRAMEWORK_DATA[name]["import_name"] in sys.modules
            ]
            if len(imported) == 1:
                return cast(FrameworkLiteral, imported[0])

            _log.warning(
                "Multiple frameworks detected: %s, using '%s'.\n"
                "Override this by passing 'framework' to sonolink.Client.",
                available,
                available[0],
            )

        return cast(FrameworkLiteral, available[0])

    @classmethod
    def _check_available(
        cls,
        data: dict[str, str],
        pkg_to_providers: dict[str, list[str]],
        known_pkgs: set[str],
    ) -> bool:
        pkg, import_name, min_ver = data["pkg"], data["import_name"], data["min"]

        try:
            installed = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            return False

        if Version(installed).release < Version(min_ver).release:
            _log.warning("Found %s v%s, but v%s+ is required.", pkg, installed, min_ver)
            return False

        providers = {cls._normalize(p) for p in pkg_to_providers.get(import_name, [])}
        return (providers & known_pkgs) == {cls._normalize(pkg)}

    @staticmethod
    def _normalize(name: str) -> str:
        return name.strip().casefold().replace("_", "-").replace(".", "-")

    def create(
        self,
        bot: Any,
    ) -> DiscordBot[Any]:
        framework = self.detect_framework()
        try:
            match framework:
                case "discord.py":
                    from .adapters._dpy import DpyBot as wrapper
                case "pycord":
                    from .adapters._pycord import PycordBot as wrapper
                case "disnake":
                    from .adapters._disnake import DisnakeBot as wrapper
                # case "nextcord":
                #    from .adapters._nextcord import NextcordBot as wrapper
                case _:  # pyright: ignore[reportUnnecessaryComparison]
                    raise ValueError(f"Unsupported framework: {framework}")

            expected_type = wrapper.cls
            if not isinstance(bot, expected_type):
                raise FrameworkClientMismatch(
                    expected_type=expected_type,
                    received_type=cast(type[Any], type(bot)),
                    framework=framework,
                )

            return wrapper(bot)
        except (ImportError, ModuleNotFoundError):
            raise FrameworkImportError(framework=framework) from None
