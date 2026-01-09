"""Exceptions for pyslxd library.

Stub file for TDD - will be implemented after tests are written.
"""


class SlxdError(Exception):
    """Base exception for pyslxd."""


class SlxdConnectionError(SlxdError):
    """Connection to device failed."""


class SlxdTimeoutError(SlxdError):
    """Command timed out."""


class SlxdProtocolError(SlxdError):
    """Invalid protocol response."""
