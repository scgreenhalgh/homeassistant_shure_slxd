"""Pytest configuration for mock server tests.

These tests require real socket access since they test TCP server functionality.
"""

import pytest


# Enable socket access for mock server tests
# Required because pytest-homeassistant-custom-component includes pytest-socket
@pytest.fixture(autouse=True)
def socket_enabled(socket_enabled):
    """Enable socket access for mock server tests."""
    return
