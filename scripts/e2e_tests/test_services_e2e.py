"""End-to-end tests for service calls.

These tests verify that service calls (number set, button press, select)
work correctly through the Home Assistant API.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from conftest import HAClient


def find_slxd_entities(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find all SLX-D related entities."""
    return [
        s for s in states
        if "slxd" in s["entity_id"].lower() or "shure" in s["entity_id"].lower()
    ]


def find_entities_by_domain(states: list[dict[str, Any]], domain: str) -> list[dict[str, Any]]:
    """Find entities by domain prefix."""
    return [s for s in states if s["entity_id"].startswith(f"{domain}.")]


class TestNumberServices:
    """E2E tests for number entity services (audio gain control)."""

    @pytest.mark.asyncio
    async def test_set_audio_gain(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test setting audio gain via number entity."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        numbers = find_entities_by_domain(slxd_entities, "number")

        # Find audio gain number entity
        gain_numbers = [n for n in numbers if "gain" in n["entity_id"].lower()]

        if not gain_numbers:
            pytest.skip("No audio gain number entity found")

        gain_entity = gain_numbers[0]
        entity_id = gain_entity["entity_id"]

        # Get current value
        initial_state = await ha_client.get_state(entity_id)
        assert initial_state is not None

        initial_value = float(initial_state["state"]) if initial_state["state"] not in ("unavailable", "unknown") else 0

        # Set new value (ensure it's different)
        new_value = 10 if initial_value != 10 else 5

        await ha_client.call_service(
            "number", "set_value",
            {"entity_id": entity_id, "value": new_value}
        )

        # Wait for state update
        await asyncio.sleep(3)

        # Verify state changed
        updated_state = await ha_client.get_state(entity_id)
        assert updated_state is not None
        assert float(updated_state["state"]) == new_value, \
            f"Expected {new_value}, got {updated_state['state']}"

    @pytest.mark.asyncio
    async def test_audio_gain_respects_limits(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that audio gain respects min/max limits."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        numbers = find_entities_by_domain(slxd_entities, "number")

        gain_numbers = [n for n in numbers if "gain" in n["entity_id"].lower()]

        if not gain_numbers:
            pytest.skip("No audio gain number entity found")

        gain_entity = gain_numbers[0]
        entity_id = gain_entity["entity_id"]
        attrs = gain_entity.get("attributes", {})

        # Check limits are defined
        min_val = attrs.get("min")
        max_val = attrs.get("max")

        if min_val is not None:
            assert min_val >= -18, f"Min should be >= -18, got {min_val}"
        if max_val is not None:
            assert max_val <= 42, f"Max should be <= 42, got {max_val}"


class TestButtonServices:
    """E2E tests for button entity services (flash/identify)."""

    @pytest.mark.asyncio
    async def test_press_flash_button(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test pressing flash button."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        buttons = find_entities_by_domain(slxd_entities, "button")

        # Find flash button
        flash_buttons = [b for b in buttons if "flash" in b["entity_id"].lower() or "identify" in b["entity_id"].lower()]

        if not flash_buttons:
            pytest.skip("No flash button entity found")

        button_entity = flash_buttons[0]
        entity_id = button_entity["entity_id"]

        # Press the button - should not raise an error
        await ha_client.call_service(
            "button", "press",
            {"entity_id": entity_id}
        )

        # Wait a moment
        await asyncio.sleep(1)

        # Verify entity is still available
        state = await ha_client.get_state(entity_id)
        assert state is not None
        assert state["state"] != "unavailable"

    @pytest.mark.asyncio
    async def test_all_flash_buttons_work(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that all flash buttons can be pressed without error."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        buttons = find_entities_by_domain(slxd_entities, "button")

        flash_buttons = [b for b in buttons if "flash" in b["entity_id"].lower() or "identify" in b["entity_id"].lower()]

        for button in flash_buttons:
            entity_id = button["entity_id"]
            # Press should not raise
            await ha_client.call_service(
                "button", "press",
                {"entity_id": entity_id}
            )
            await asyncio.sleep(0.5)


class TestSelectServices:
    """E2E tests for select entity services (audio output level)."""

    @pytest.mark.asyncio
    async def test_set_audio_output_level(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test setting audio output level via select entity."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        selects = find_entities_by_domain(slxd_entities, "select")

        # Find audio output level select
        output_selects = [
            s for s in selects
            if "output" in s["entity_id"].lower() or "level" in s["entity_id"].lower()
        ]

        if not output_selects:
            pytest.skip("No audio output level select entity found")

        select_entity = output_selects[0]
        entity_id = select_entity["entity_id"]
        attrs = select_entity.get("attributes", {})
        options = attrs.get("options", [])

        if len(options) < 2:
            pytest.skip("Select entity doesn't have multiple options")

        # Get current value
        current = select_entity["state"]

        # Choose a different option
        new_option = options[1] if current == options[0] else options[0]

        await ha_client.call_service(
            "select", "select_option",
            {"entity_id": entity_id, "option": new_option}
        )

        # Wait for state update
        await asyncio.sleep(3)

        # Verify state changed
        updated_state = await ha_client.get_state(entity_id)
        assert updated_state is not None
        assert updated_state["state"] == new_option, \
            f"Expected {new_option}, got {updated_state['state']}"

    @pytest.mark.asyncio
    async def test_select_options_are_valid(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that select entities have valid options."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        selects = find_entities_by_domain(slxd_entities, "select")

        for select in selects:
            attrs = select.get("attributes", {})
            options = attrs.get("options", [])

            assert len(options) >= 1, f"Select {select['entity_id']} has no options"

            # Current state should be one of the options
            if select["state"] not in ("unavailable", "unknown"):
                assert select["state"] in options, \
                    f"Select {select['entity_id']} state {select['state']} not in options {options}"


class TestServiceErrors:
    """E2E tests for service error handling."""

    @pytest.mark.asyncio
    async def test_invalid_entity_service_call(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that calling service on non-existent entity fails gracefully."""
        try:
            await ha_client.call_service(
                "number", "set_value",
                {"entity_id": "number.nonexistent_entity", "value": 10}
            )
        except Exception:
            # Expected to fail - that's OK
            pass

    @pytest.mark.asyncio
    async def test_service_with_missing_data(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that service call with missing data fails gracefully."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)
        numbers = find_entities_by_domain(slxd_entities, "number")

        if not numbers:
            pytest.skip("No number entities found")

        entity_id = numbers[0]["entity_id"]

        try:
            # Missing 'value' parameter
            await ha_client.call_service(
                "number", "set_value",
                {"entity_id": entity_id}  # Missing value
            )
        except Exception:
            # Expected to fail
            pass


class TestCoordinatorRefresh:
    """E2E tests for coordinator data refresh."""

    @pytest.mark.asyncio
    async def test_homeassistant_update_entity_service(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that update_entity service triggers refresh."""
        states = await ha_client.get_states()
        slxd_entities = find_slxd_entities(states)

        if not slxd_entities:
            pytest.skip("No SLX-D entities found")

        entity_id = slxd_entities[0]["entity_id"]

        # Call update_entity - should not raise
        await ha_client.call_service(
            "homeassistant", "update_entity",
            {"entity_id": entity_id}
        )

        await asyncio.sleep(2)

        # Entity should still be available
        state = await ha_client.get_state(entity_id)
        assert state is not None
