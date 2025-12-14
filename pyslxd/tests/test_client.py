"""Tests for pyslxd async TCP client.

TDD RED PHASE: These tests define the expected behavior of the client module.
Run these tests to see them fail, then implement client.py to make them pass.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyslxd.client import SlxdClient
from pyslxd.exceptions import SlxdConnectionError, SlxdTimeoutError
from pyslxd.models import SlxdDevice, SlxdChannel, AudioOutputLevel, LockStatus


class TestClientConnection:
    """Tests for client connection management."""

    @pytest.mark.asyncio
    async def test_connect_success(self) -> None:
        """Test successful connection to device."""
        # Arrange
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()

            # Act
            await client.connect("192.168.1.100", 2202)

            # Assert
            assert client.connected is True

    @pytest.mark.asyncio
    async def test_connect_default_port(self) -> None:
        """Test connection with default port."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ) as mock_open:
            client = SlxdClient()
            await client.connect("192.168.1.100")

            mock_open.assert_called_once_with("192.168.1.100", 2202)

    @pytest.mark.asyncio
    async def test_connect_timeout_raises_error(self) -> None:
        """Test that connection timeout raises SlxdConnectionError."""
        with patch(
            "asyncio.open_connection",
            side_effect=asyncio.TimeoutError(),
        ):
            client = SlxdClient()

            with pytest.raises(SlxdConnectionError):
                await client.connect("192.168.1.100", 2202)

    @pytest.mark.asyncio
    async def test_connect_refused_raises_error(self) -> None:
        """Test that connection refused raises SlxdConnectionError."""
        with patch(
            "asyncio.open_connection",
            side_effect=ConnectionRefusedError(),
        ):
            client = SlxdClient()

            with pytest.raises(SlxdConnectionError):
                await client.connect("192.168.1.100", 2202)

    @pytest.mark.asyncio
    async def test_connect_unreachable_raises_error(self) -> None:
        """Test that network unreachable raises SlxdConnectionError."""
        with patch(
            "asyncio.open_connection",
            side_effect=OSError("Network unreachable"),
        ):
            client = SlxdClient()

            with pytest.raises(SlxdConnectionError):
                await client.connect("192.168.1.100", 2202)

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnecting from device."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100", 2202)

            # Act
            await client.disconnect()

            # Assert
            assert client.connected is False
            mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        """Test disconnecting when not connected does not raise."""
        client = SlxdClient()
        await client.disconnect()  # Should not raise

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test client can be used as async context manager."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            async with SlxdClient("192.168.1.100") as client:
                assert client.connected is True

            assert client.connected is False


class TestClientCommands:
    """Tests for sending commands and receiving responses."""

    @pytest.mark.asyncio
    async def test_send_command_and_receive_response(self) -> None:
        """Test sending a command and receiving response."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP MODEL {SLXD4D                          } >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            # Act
            response = await client.send_command("< GET MODEL >")

            # Assert
            mock_writer.write.assert_called_with(b"< GET MODEL >\r\n")
            assert response.property_name == "MODEL"
            assert response.value == "SLXD4D"

    @pytest.mark.asyncio
    async def test_send_command_timeout(self) -> None:
        """Test that command timeout raises SlxdTimeoutError."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            with pytest.raises(SlxdTimeoutError):
                await client.send_command("< GET MODEL >")

    @pytest.mark.asyncio
    async def test_send_command_when_not_connected(self) -> None:
        """Test that sending command when not connected raises error."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError):
            await client.send_command("< GET MODEL >")


class TestClientDeviceInfo:
    """Tests for device information methods."""

    @pytest.mark.asyncio
    async def test_get_model(self) -> None:
        """Test getting device model."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP MODEL {SLXD4D                          } >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            model = await client.get_model()
            assert model == "SLXD4D"

    @pytest.mark.asyncio
    async def test_get_device_id(self) -> None:
        """Test getting device ID."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP DEVICE_ID {SLXD4D01} >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            device_id = await client.get_device_id()
            assert device_id == "SLXD4D01"

    @pytest.mark.asyncio
    async def test_get_firmware_version(self) -> None:
        """Test getting firmware version."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP FW_VER {2.0.15.2                } >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            fw_ver = await client.get_firmware_version()
            assert fw_ver == "2.0.15.2"


class TestClientChannelControl:
    """Tests for channel control methods."""

    @pytest.mark.asyncio
    async def test_get_audio_gain(self) -> None:
        """Test getting audio gain for a channel."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_GAIN 030 >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            # Act - should return converted value (30 - 18 = 12 dB)
            gain = await client.get_audio_gain(1)
            assert gain == 12

    @pytest.mark.asyncio
    async def test_set_audio_gain(self) -> None:
        """Test setting audio gain for a channel."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_GAIN 040 >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            # Act - set to 22 dB (raw = 22 + 18 = 40)
            await client.set_audio_gain(1, 22)

            # Assert the command sent had the correct raw value
            mock_writer.write.assert_called_with(b"< SET 1 AUDIO_GAIN 040 >\r\n")

    @pytest.mark.asyncio
    async def test_set_audio_gain_validates_range(self) -> None:
        """Test that invalid gain values raise ValueError."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            with pytest.raises(ValueError):
                await client.set_audio_gain(1, 50)  # Max is 42

            with pytest.raises(ValueError):
                await client.set_audio_gain(1, -20)  # Min is -18

    @pytest.mark.asyncio
    async def test_flash_device(self) -> None:
        """Test flashing device LEDs."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP FLASH ON >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            await client.flash_device()
            mock_writer.write.assert_called_with(b"< SET FLASH ON >\r\n")

    @pytest.mark.asyncio
    async def test_flash_channel(self) -> None:
        """Test flashing specific channel LED."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 FLASH ON >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            await client.flash_channel(1)
            mock_writer.write.assert_called_with(b"< SET 1 FLASH ON >\r\n")


class TestClientMetering:
    """Tests for metering/sampling methods."""

    @pytest.mark.asyncio
    async def test_start_metering(self) -> None:
        """Test starting metering for a channel."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 METER_RATE 01000 >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            await client.start_metering(1, rate_ms=1000)
            mock_writer.write.assert_called_with(b"< SET 1 METER_RATE 01000 >\r\n")

    @pytest.mark.asyncio
    async def test_stop_metering(self) -> None:
        """Test stopping metering for a channel."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 METER_RATE 00000 >\r\n"
        )
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            return_value=(mock_reader, mock_writer),
        ):
            client = SlxdClient()
            await client.connect("192.168.1.100")

            await client.stop_metering(1)
            mock_writer.write.assert_called_with(b"< SET 1 METER_RATE 00000 >\r\n")
