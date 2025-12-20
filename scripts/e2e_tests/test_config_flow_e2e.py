"""End-to-end tests for config flow.

These tests verify the config flow works correctly in a real
Home Assistant environment with the mock SLX-D server.
"""

from __future__ import annotations

import asyncio

import pytest

from conftest import HAClient, INTEGRATION_DOMAIN


class TestConfigFlowE2E:
    """E2E tests for the config flow."""

    @pytest.mark.asyncio
    async def test_setup_integration_success(
        self, ha_client: HAClient, clean_integration: None, mock_host: str, mock_port: int
    ) -> None:
        """Test successful integration setup via config flow."""
        # Start config flow
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        assert "flow_id" in flow
        assert flow.get("type") == "form"
        assert flow.get("step_id") == "user"

        flow_id = flow["flow_id"]

        # Submit valid configuration
        result = await ha_client.submit_config_flow(
            flow_id, {"host": mock_host, "port": mock_port}
        )

        # Should create entry
        assert result.get("type") == "create_entry"
        assert "SLXD" in result.get("title", "")
        assert result.get("result", {}).get("domain") == INTEGRATION_DOMAIN

    @pytest.mark.asyncio
    async def test_setup_with_invalid_host(
        self, ha_client: HAClient, clean_integration: None
    ) -> None:
        """Test config flow with unreachable host."""
        # Start config flow
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        flow_id = flow["flow_id"]

        # Submit invalid host
        result = await ha_client.submit_config_flow(
            flow_id, {"host": "192.0.2.1", "port": 2202}  # TEST-NET, unreachable
        )

        # Should show error form, not create entry
        assert result.get("type") == "form"
        assert "cannot_connect" in result.get("errors", {}).values()

    @pytest.mark.asyncio
    async def test_duplicate_device_rejected(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that duplicate devices are rejected."""
        # Integration already configured via fixture

        # Try to configure again
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        flow_id = flow["flow_id"]

        result = await ha_client.submit_config_flow(
            flow_id, {"host": "mock_slxd", "port": 2202}
        )

        # Should abort with already_configured
        assert result.get("type") == "abort"
        assert result.get("reason") == "already_configured"

    @pytest.mark.asyncio
    async def test_config_entry_created_with_correct_data(
        self, ha_client: HAClient, configured_integration: dict
    ) -> None:
        """Test that config entry contains correct data."""
        entries = await ha_client.get_config_entries()

        slxd_entries = [e for e in entries if e.get("domain") == INTEGRATION_DOMAIN]
        assert len(slxd_entries) == 1

        entry = slxd_entries[0]
        assert entry.get("state") == "loaded"
        assert "SLXD" in entry.get("title", "")

    @pytest.mark.asyncio
    async def test_integration_can_be_removed(
        self, ha_client: HAClient, clean_integration: None, mock_host: str, mock_port: int
    ) -> None:
        """Test that integration can be removed."""
        # Set up integration
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        result = await ha_client.submit_config_flow(
            flow["flow_id"], {"host": mock_host, "port": mock_port}
        )
        assert result.get("type") == "create_entry"

        # Wait for setup
        await asyncio.sleep(3)

        # Get entry ID
        entries = await ha_client.get_config_entries()
        slxd_entries = [e for e in entries if e.get("domain") == INTEGRATION_DOMAIN]
        assert len(slxd_entries) == 1
        entry_id = slxd_entries[0]["entry_id"]

        # Remove integration
        await ha_client.delete_config_entry(entry_id)
        await asyncio.sleep(2)

        # Verify removed
        entries = await ha_client.get_config_entries()
        slxd_entries = [e for e in entries if e.get("domain") == INTEGRATION_DOMAIN]
        assert len(slxd_entries) == 0


class TestConfigFlowValidation:
    """E2E tests for config flow input validation."""

    @pytest.mark.asyncio
    async def test_empty_host_rejected(
        self, ha_client: HAClient, clean_integration: None
    ) -> None:
        """Test that empty host is rejected."""
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        flow_id = flow["flow_id"]

        # Submit empty host - should fail validation
        result = await ha_client.submit_config_flow(
            flow_id, {"host": "", "port": 2202}
        )

        # Should remain on form with error
        assert result.get("type") == "form"

    @pytest.mark.asyncio
    async def test_invalid_port_rejected(
        self, ha_client: HAClient, clean_integration: None
    ) -> None:
        """Test that invalid port values are handled."""
        flow = await ha_client.start_config_flow(INTEGRATION_DOMAIN)
        flow_id = flow["flow_id"]

        # Submit invalid port
        result = await ha_client.submit_config_flow(
            flow_id, {"host": "mock_slxd", "port": 99999}
        )

        # Should fail - either validation or connection error
        assert result.get("type") in ("form", "abort")
