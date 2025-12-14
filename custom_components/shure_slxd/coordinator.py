"""DataUpdateCoordinator for Shure SLX-D integration.

TDD RED phase - tests are written, implementation pending.
"""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class SlxdDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for SLX-D device data updates - stub for TDD."""

    async def _async_update_data(self):
        """Fetch data from device."""
        raise NotImplementedError("TDD RED phase")
