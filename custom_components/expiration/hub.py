"""Shared hub state for the Expiration integration (calendar aggregation)."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HUB_STORE_KEY = f"{DOMAIN}_hub"
HUB_STORE_VERSION = 1


class ExpirationHub:
    """Holds coordinators and global calendar toggle (persisted)."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize hub."""
        self.hass = hass
        self.coordinators: dict[str, object] = {}
        self.calendar_enabled = True
        self._store: Store = Store(hass, HUB_STORE_VERSION, HUB_STORE_KEY)

    async def async_load(self) -> None:
        """Load persisted hub settings."""
        data = await self._store.async_load()
        if isinstance(data, dict):
            self.calendar_enabled = bool(data.get("calendar_enabled", True))

    async def async_save(self) -> None:
        """Persist hub settings."""
        await self._store.async_save({"calendar_enabled": self.calendar_enabled})

    def register_coordinator(self, entry_id: str, coordinator: object) -> None:
        """Register a coordinator for calendar aggregation."""
        self.coordinators[entry_id] = coordinator

    def unregister_coordinator(self, entry_id: str) -> None:
        """Unregister coordinator."""
        self.coordinators.pop(entry_id, None)
