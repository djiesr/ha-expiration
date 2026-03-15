"""Data coordinator for the Expiration integration."""

from __future__ import annotations

from datetime import datetime, date
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, STORAGE_VERSION, STORAGE_KEY_PREFIX

_LOGGER = logging.getLogger(__name__)


class ExpirationCoordinator(DataUpdateCoordinator):
    """Manages storage and state for a single expiration item."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        days_max: int,
        alert_threshold: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
        )
        self.entry_id = entry_id
        self.item_name = name
        self.days_max = days_max
        self.alert_threshold = alert_threshold

        storage_key = f"{STORAGE_KEY_PREFIX}.{entry_id}"
        self._store: Store = Store(hass, STORAGE_VERSION, storage_key)
        self.last_reset: date | None = None

    async def async_setup(self) -> None:
        """Load persisted data from storage."""
        data = await self._store.async_load()
        if data and "last_reset" in data:
            try:
                self.last_reset = date.fromisoformat(data["last_reset"])
            except ValueError:
                _LOGGER.warning("Invalid last_reset date in storage, resetting.")
                self.last_reset = date.today()
        else:
            self.last_reset = date.today()
            await self._save()

        await self.async_refresh()

    async def _async_update_data(self) -> dict:
        """Calculate current expiration state."""
        today = date.today()
        last_reset = self.last_reset or today

        elapsed_days = (today - last_reset).days
        days_remaining = max(0, self.days_max - elapsed_days)
        percentage_elapsed = min(100, round((elapsed_days / self.days_max) * 100, 1))
        expiration_date = last_reset.replace(day=last_reset.day)
        from datetime import timedelta

        expiration_date = last_reset + timedelta(days=self.days_max)

        return {
            "days_remaining": days_remaining,
            "percentage_elapsed": percentage_elapsed,
            "expiration_date": expiration_date.isoformat(),
            "last_reset": last_reset.isoformat(),
            "is_expired": days_remaining == 0,
            "is_warning": days_remaining <= self.alert_threshold and days_remaining > 0,
        }

    async def async_reset(self) -> None:
        """Reset the timer to today."""
        self.last_reset = date.today()
        await self._save()
        await self.async_refresh()

    async def _save(self) -> None:
        """Persist data to storage."""
        await self._store.async_save(
            {"last_reset": self.last_reset.isoformat() if self.last_reset else None}
        )
