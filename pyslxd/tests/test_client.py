"""Tests for pyslxd async TCP client.

TDD RED PHASE: These tests define the expected behavior of the client module.
Run these tests to see them fail, then implement client.py to make them pass.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyslxd.client import SlxdClient, MAX_RESPONSE_SIZE
from pyslxd.exceptions import SlxdConnectionError, SlxdProtocolError, SlxdTimeoutError
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


class TestClientChannelValidation:
    """Tests for channel number validation."""

    @pytest.mark.asyncio
    async def test_get_audio_gain_validates_channel_too_low(self) -> None:
        """Test that channel 0 raises ValueError."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.get_audio_gain(0)

    @pytest.mark.asyncio
    async def test_get_audio_gain_validates_channel_too_high(self) -> None:
        """Test that channel 5 raises ValueError."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.get_audio_gain(5)

    @pytest.mark.asyncio
    async def test_set_audio_gain_validates_channel(self) -> None:
        """Test that set_audio_gain validates channel."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.set_audio_gain(0, 10)

    @pytest.mark.asyncio
    async def test_flash_channel_validates_channel(self) -> None:
        """Test that flash_channel validates channel."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.flash_channel(99)

    @pytest.mark.asyncio
    async def test_start_metering_validates_channel(self) -> None:
        """Test that start_metering validates channel."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.start_metering(-1)

    @pytest.mark.asyncio
    async def test_stop_metering_validates_channel(self) -> None:
        """Test that stop_metering validates channel."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.stop_metering(100)


class TestClientResponseValidation:
    """Tests for response size and timeout validation."""

    @pytest.mark.asyncio
    async def test_send_command_rejects_oversized_response(self) -> None:
        """Test that oversized responses raise SlxdProtocolError."""
        mock_reader = AsyncMock()
        # Create a response larger than MAX_RESPONSE_SIZE
        oversized_response = b"< REP MODEL " + b"X" * (MAX_RESPONSE_SIZE + 100) + b" >\r\n"
        mock_reader.readline = AsyncMock(return_value=oversized_response)
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

            with pytest.raises(SlxdProtocolError, match="Response too large"):
                await client.send_command("< GET MODEL >")


class TestClientChannelInfo:
    """Tests for additional channel information methods."""

    @pytest.mark.asyncio
    async def test_get_frequency(self) -> None:
        """Test getting channel frequency in kHz."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 FREQUENCY 0578350 >\r\n"
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

            freq = await client.get_frequency(1)
            assert freq == 578350
            mock_writer.write.assert_called_with(b"< GET 1 FREQUENCY >\r\n")

    @pytest.mark.asyncio
    async def test_get_channel_name(self) -> None:
        """Test getting channel name."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 CHAN_NAME {Lead Vox                       } >\r\n"
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

            name = await client.get_channel_name(1)
            assert name == "Lead Vox"

    @pytest.mark.asyncio
    async def test_get_audio_level_peak(self) -> None:
        """Test getting peak audio level in dBFS."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_LEVEL_PEAK 102 >\r\n"
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

            # Raw 102, offset 120 = -18 dBFS
            level = await client.get_audio_level_peak(1)
            assert level == -18

    @pytest.mark.asyncio
    async def test_get_audio_level_rms(self) -> None:
        """Test getting RMS audio level in dBFS."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_LEVEL_RMS 090 >\r\n"
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

            # Raw 90, offset 120 = -30 dBFS
            level = await client.get_audio_level_rms(1)
            assert level == -30

    @pytest.mark.asyncio
    async def test_get_rssi_antenna_1(self) -> None:
        """Test getting RSSI for antenna 1 in dBm."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 RSSI 1 083 >\r\n"
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

            # Raw 83, offset 120 = -37 dBm
            rssi = await client.get_rssi(1, antenna=1)
            assert rssi == -37
            mock_writer.write.assert_called_with(b"< GET 1 RSSI 1 >\r\n")

    @pytest.mark.asyncio
    async def test_get_rssi_antenna_2(self) -> None:
        """Test getting RSSI for antenna 2 in dBm."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 RSSI 2 064 >\r\n"
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

            # Raw 64, offset 120 = -56 dBm
            rssi = await client.get_rssi(1, antenna=2)
            assert rssi == -56


class TestClientTransmitterInfo:
    """Tests for transmitter information methods."""

    @pytest.mark.asyncio
    async def test_get_tx_model(self) -> None:
        """Test getting transmitter model."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 TX_MODEL SLXD2 >\r\n"
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

            model = await client.get_tx_model(1)
            assert model == "SLXD2"

    @pytest.mark.asyncio
    async def test_get_tx_batt_bars(self) -> None:
        """Test getting transmitter battery bars."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 TX_BATT_BARS 004 >\r\n"
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

            bars = await client.get_tx_batt_bars(1)
            assert bars == 4

    @pytest.mark.asyncio
    async def test_get_tx_batt_bars_unknown(self) -> None:
        """Test getting transmitter battery bars when unknown."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 TX_BATT_BARS 255 >\r\n"
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

            bars = await client.get_tx_batt_bars(1)
            assert bars is None

    @pytest.mark.asyncio
    async def test_get_tx_batt_mins(self) -> None:
        """Test getting transmitter battery minutes."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 TX_BATT_MINS 00125 >\r\n"
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

            mins = await client.get_tx_batt_mins(1)
            assert mins == 125

    @pytest.mark.asyncio
    async def test_get_tx_batt_mins_calculating(self) -> None:
        """Test getting transmitter battery minutes when calculating."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 TX_BATT_MINS 65534 >\r\n"
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

            mins = await client.get_tx_batt_mins(1)
            assert mins is None


class TestClientAudioOutputLevel:
    """Tests for audio output level methods."""

    @pytest.mark.asyncio
    async def test_get_audio_out_level(self) -> None:
        """Test getting audio output level."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_OUT_LVL MIC >\r\n"
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

            level = await client.get_audio_out_level(1)
            assert level == "MIC"
            mock_writer.write.assert_called_with(b"< GET 1 AUDIO_OUT_LVL >\r\n")

    @pytest.mark.asyncio
    async def test_set_audio_out_level(self) -> None:
        """Test setting audio output level."""
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(
            return_value=b"< REP 1 AUDIO_OUT_LVL LINE >\r\n"
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

            await client.set_audio_out_level(1, "LINE")
            mock_writer.write.assert_called_with(b"< SET 1 AUDIO_OUT_LVL LINE >\r\n")

    @pytest.mark.asyncio
    async def test_set_audio_out_level_validates_value(self) -> None:
        """Test that invalid audio output level raises ValueError."""
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

            with pytest.raises(ValueError, match="Level must be 'MIC' or 'LINE'"):
                await client.set_audio_out_level(1, "INVALID")

    @pytest.mark.asyncio
    async def test_set_audio_out_level_validates_channel(self) -> None:
        """Test that invalid channel raises ValueError."""
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

            with pytest.raises(ValueError, match="Channel must be 1-4"):
                await client.set_audio_out_level(0, "MIC")


class TestClientRSSIValidation:
    """Tests for RSSI antenna validation."""

    @pytest.mark.asyncio
    async def test_get_rssi_invalid_antenna(self) -> None:
        """Test that invalid antenna raises ValueError."""
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

            with pytest.raises(ValueError, match="Antenna must be 1 or 2"):
                await client.get_rssi(1, antenna=3)


class TestClientConnectionErrors:
    """Tests for connection edge cases."""

    @pytest.mark.asyncio
    async def test_connect_without_host_raises_error(self) -> None:
        """Test that connecting without host raises SlxdConnectionError."""
        client = SlxdClient()

        with pytest.raises(SlxdConnectionError, match="No host specified"):
            await client.connect()
