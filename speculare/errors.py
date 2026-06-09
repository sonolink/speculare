"""
MIT License

Copyright (c) 2026-present SonoLink Development Team.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.libraries.factory import FrameworkLiteral


__all__ = (
    "FrameworkClientMismatch",
    "FrameworkImportError",
)


class SpeculareException(Exception):
    """Base exception for all Speculare-related errors."""


class FrameworkClientMismatch(SpeculareException):
    """
    Exception raised when trying to initialize a Sonolink Client with a
    client that does not match the detected framework. This likely means the
    client is from a different framework or the framework detection is incorrect.
    """

    expected_type: type
    """The expected framework type."""
    received_type: type
    """The actual framework type."""
    framework: FrameworkLiteral
    """The detected framework."""

    def __init__(
        self, *, expected_type: type, received_type: type, framework: FrameworkLiteral
    ) -> None:
        self.expected_type = expected_type
        self.received_type = received_type
        self.framework = framework
        msg = (
            f"Expected client of type {self.expected_type!r} for detected framework '{framework}', "
            f"but got {self.received_type!r}. Either the client is from a different framework or the framework detection is incorrect."
        )
        super().__init__(msg)


class FrameworkImportError(SpeculareException):
    """Exception raised when trying to initialize a Sonolink Client with a framework's
    client, but the framework cannot be imported. This likely means the framework
    is not installed, there is an issue with the installation or the framework detection is incorrect.
    """

    framework: FrameworkLiteral
    """The detected framework."""

    def __init__(self, *, framework: FrameworkLiteral) -> None:
        self.framework = framework

        msg = f"Could not import detected framework '{framework}'. Make sure the framework is installed and up to date."
        super().__init__(msg)
