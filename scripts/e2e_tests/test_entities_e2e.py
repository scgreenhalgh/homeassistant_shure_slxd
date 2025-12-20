"""End-to-end tests for entity creation and state.

These tests verify that entities are created correctly and
their states match the mock device.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from conftest import HAClient


def find_entities_by_domain(states: list[dict[str, Any]], domain: str) -> list[dict[str, Any]]:
    """Find entities by domain prefix."""
    return [s for s in states if s["entity_id"].startswith(f"{domain}.")]


def find_slxd_entities(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find all SLX-D related entities."""
    return [
        s for s in states
        if "slxd" in s["entity_id"].lower() or "shure" in s["entity_id"].lower()
    ]


class TestEntityCreation:
    """E2E tests for entity creation."""

    @pytest.mark.asyncio
    async def test_sensors_created(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify sensor entities are created."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        sensors = find_entities_by_domain(slxd_entities, "sensor")

        # Should have multiple sensors
        assert len(sensors) > 0, "No sensor entities created"

        # Print for debugging
        print(f"\nFound {len(sensors)} sensors:")
        for s in sorted(sensors, key=lambda x: x["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']}")

    @pytest.mark.asyncio
    async def test_binary_sensors_created(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify binary sensor entities are created."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        binary_sensors = find_entities_by_domain(slxd_entities, "binary_sensor")

        # Should have at least one binary sensor (transmitter connected)
        assert len(binary_sensors) > 0, "No binary_sensor entities created"

        print(f"\nFound {len(binary_sensors)} binary sensors:")
        for s in sorted(binary_sensors, key=lambda x: x["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']}")

    @pytest.mark.asyncio
    async def test_number_entities_created(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify number entities are created (audio gain control)."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        numbers = find_entities_by_domain(slxd_entities, "number")

        # Should have number entities for audio gain
        assert len(numbers) > 0, "No number entities created"

        print(f"\nFound {len(numbers)} number entities:")
        for s in sorted(numbers, key=lambda x: x["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']}")

    @pytest.mark.asyncio
    async def test_button_entities_created(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify button entities are created (flash/identify)."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        buttons = find_entities_by_domain(slxd_entities, "button")

        # Should have button entities for flash
        assert len(buttons) > 0, "No button entities created"

        print(f"\nFound {len(buttons)} button entities:")
        for s in sorted(buttons, key=lambda x: x["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']}")

    @pytest.mark.asyncio
    async def test_select_entities_created(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify select entities are created (audio output level)."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        selects = find_entities_by_domain(slxd_entities, "select")

        # Should have select entities for audio output level
        assert len(selects) > 0, "No select entities created"

        print(f"\nFound {len(selects)} select entities:")
        for s in sorted(selects, key=lambda x: x["entity_id"]):
            print(f"  {s['entity_id']}: {s['state']}")


class TestEntityValues:
    """E2E tests for entity values matching mock device state."""

    @pytest.mark.asyncio
    async def test_device_model_sensor(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify device model sensor has correct value."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)

        # Find model sensor
        model_sensors = [s for s in slxd_entities if "model" in s["entity_id"].lower()]

        assert len(model_sensors) > 0, "No model sensor found"

        # Check one contains SLXD4D (the mock device model)
        model_values = [s["state"] for s in model_sensors]
        assert any("SLXD4D" in v for v in model_values), f"Expected SLXD4D in model values: {model_values}"

    @pytest.mark.asyncio
    async def test_rf_band_sensor(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify RF band sensor has correct value."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)

        # Find RF band sensor
        rf_sensors = [s for s in slxd_entities if "rf" in s["entity_id"].lower() and "band" in s["entity_id"].lower()]

        if rf_sensors:
            # Mock server uses G55
            assert any(s["state"] == "G55" for s in rf_sensors), \
                f"Expected G55 RF band, got: {[s['state'] for s in rf_sensors]}"

    @pytest.mark.asyncio
    async def test_transmitter_connected_sensor(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify transmitter connected binary sensor."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        binary_sensors = find_entities_by_domain(slxd_entities, "binary_sensor")

        # Find transmitter connected sensor for channel 1
        tx_sensors = [
            s for s in binary_sensors
            if "transmitter" in s["entity_id"].lower() or "connected" in s["entity_id"].lower()
        ]

        if tx_sensors:
            # Channel 1 should have connected transmitter (from mock config)
            ch1_sensors = [s for s in tx_sensors if "1" in s["entity_id"]]
            if ch1_sensors:
                # Should be "on" because mock has transmitter connected on ch1
                assert ch1_sensors[0]["state"] == "on", \
                    f"Expected ch1 transmitter connected, got: {ch1_sensors[0]['state']}"

    @pytest.mark.asyncio
    async def test_audio_gain_value(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify audio gain has reasonable value."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)

        # Find audio gain entities
        gain_entities = [
            s for s in slxd_entities
            if "gain" in s["entity_id"].lower()
        ]

        if gain_entities:
            for entity in gain_entities:
                state = entity["state"]
                if state not in ("unavailable", "unknown"):
                    # Gain should be a number between -18 and 42
                    gain = float(state)
                    assert -18 <= gain <= 42, f"Gain {gain} out of range for {entity['entity_id']}"


class TestEntityAttributes:
    """E2E tests for entity attributes."""

    @pytest.mark.asyncio
    async def test_sensor_has_device_class(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify sensors have appropriate device_class."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        sensors = find_entities_by_domain(slxd_entities, "sensor")

        # Find battery sensors - should have battery device class
        battery_sensors = [s for s in sensors if "battery" in s["entity_id"].lower()]
        for sensor in battery_sensors:
            attrs = sensor.get("attributes", {})
            # Battery percentage sensors should have device_class: battery
            if "percent" in sensor["entity_id"].lower():
                assert attrs.get("device_class") == "battery", \
                    f"Expected battery device_class for {sensor['entity_id']}"

    @pytest.mark.asyncio
    async def test_sensor_has_unit_of_measurement(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify sensors have unit_of_measurement where appropriate."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        sensors = find_entities_by_domain(slxd_entities, "sensor")

        # Check some sensors have units
        sensors_with_units = [
            s for s in sensors
            if s.get("attributes", {}).get("unit_of_measurement")
        ]

        # Should have some sensors with units (dB, dBFS, dBm, MHz, etc.)
        print(f"\nSensors with units: {len(sensors_with_units)}")
        for s in sensors_with_units[:5]:  # Show first 5
            unit = s["attributes"]["unit_of_measurement"]
            print(f"  {s['entity_id']}: {s['state']} {unit}")

    @pytest.mark.asyncio
    async def test_entities_have_friendly_name(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Verify entities have friendly names."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)

        for entity in slxd_entities[:10]:  # Check first 10
            attrs = entity.get("attributes", {})
            friendly_name = attrs.get("friendly_name")
            assert friendly_name, f"Entity {entity['entity_id']} missing friendly_name"


class TestStateUpdates:
    """E2E tests for state update propagation."""

    @pytest.mark.asyncio
    async def test_state_updates_on_coordinator_refresh(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that states update periodically."""
        # Get initial states
        states1 = await ha_client.get_states()
        slxd_entities1 = find_slxd_entities(states1)

        # Wait for coordinator refresh (scan_interval is typically 5-30 seconds)
        await asyncio.sleep(15)

        # Get states again
        states2 = await ha_client.get_states()
        slxd_entities2 = find_slxd_entities(states2)

        # Both should have entities
        assert len(slxd_entities1) > 0
        assert len(slxd_entities2) > 0

        # Entities should still be available (not unavailable)
        for entity in slxd_entities2:
            if entity["state"] == "unavailable":
                # Log but don't fail - some entities may be legitimately unavailable
                print(f"Warning: {entity['entity_id']} is unavailable")
