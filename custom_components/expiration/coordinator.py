"""Data coordinator for the Expiration integration."""

from __future__ import annotations

from datetime import date, datetime, timedelta, time
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, MODE_DAY, MODE_HOUR, STORAGE_VERSION, STORAGE_KEY_PREFIX

_LOGGER = logging.getLogger(__name__)


class ExpirationCoordinator(DataUpdateCoordinator):
    """Manages storage and state for a single expiration item."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        mode: str,
        days_max: int,
        alert_threshold: int,
        hours_max: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{name}",
        )
        self.entry_id = entry_id
        self.item_name = name
        self.mode = mode
        self.days_max = days_max
        self.alert_threshold = alert_threshold
        self.hours_max = hours_max

        storage_key = f"{STORAGE_KEY_PREFIX}.{entry_id}"
        self._store: Store = Store(hass, STORAGE_VERSION, storage_key)
        self.last_reset_dt: datetime | None = None

    async def async_setup(self) -> None:
        """Load persisted data from storage."""
        data = await self._store.async_load()
        if data and data.get("last_reset_dt"):
            try:
                self.last_reset_dt = datetime.fromisoformat(data["last_reset_dt"])
                if self.last_reset_dt.tzinfo is None:
                    self.last_reset_dt = dt_util.as_local(self.last_reset_dt)
            except ValueError:
                _LOGGER.warning("Invalid last_reset_dt in storage, resetting.")
                self.last_reset_dt = dt_util.now()
        elif data and data.get("last_reset"):
            try:
                d = date.fromisoformat(data["last_reset"])
                self.last_reset_dt = dt_util.start_of_local_day(
                    datetime.combine(d, time.min)
                )
            except ValueError:
                self.last_reset_dt = dt_util.now()
        else:
            self.last_reset_dt = dt_util.now()

        await self._save()
        await self.async_refresh()

    async def _async_update_data(self) -> dict:
        """Calculate current expiration state."""
        now = dt_util.now()
        last_reset = self.last_reset_dt or now
        last_reset = dt_util.as_local(last_reset)

        if self.mode == MODE_HOUR:
            return self._update_hour_mode(now, last_reset)

        return self._update_day_mode(now, last_reset)

    def _update_day_mode(self, now: datetime, last_reset: datetime) -> dict:
        """Day-based countdown (original behaviour)."""
        last_reset_date = last_reset.date()
        today = now.date()

        elapsed_days = (today - last_reset_date).days
        days_remaining = self.days_max - elapsed_days
        percentage_elapsed = min(100, round((elapsed_days / self.days_max) * 100))
        remaining_days_pos = max(0, days_remaining)
        percentage_remaining = max(
            0, min(100, round((remaining_days_pos / self.days_max) * 100))
        )
        expiration_date = last_reset_date + timedelta(days=self.days_max)

        is_expired = days_remaining < 0
        result = {
            "days_remaining": days_remaining,
            "percentage_elapsed": percentage_elapsed,
            "percentage_remaining": percentage_remaining,
            "expiration_date": expiration_date.isoformat(),
            "last_reset": last_reset_date.isoformat(),
            "last_reset_datetime": last_reset.isoformat(),
            "expiration_datetime": None,
            "hours_remaining": None,
            "is_expired": is_expired,
            "is_warning": (0 <= days_remaining <= self.alert_threshold) and not is_expired,
        }
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        return result

    def _update_hour_mode(self, now: datetime, last_reset: datetime) -> dict:
        """Hour-based countdown."""
        elapsed_hours = (now - last_reset).total_seconds() / 3600.0
        hours_remaining = round(float(self.hours_max) - elapsed_hours, 1)
        percentage_elapsed = min(
            100, round((elapsed_hours / float(self.hours_max)) * 100)
        )
        remaining_hours_pos = max(0.0, float(hours_remaining))
        percentage_remaining = max(
            0,
            min(
                100,
                round((remaining_hours_pos / float(self.hours_max)) * 100),
            ),
        )
        due = last_reset + timedelta(hours=float(self.hours_max))
        due = dt_util.as_local(due)
        expiration_date = due.date()

        is_expired = hours_remaining < 0
        is_warning = (0 <= hours_remaining <= float(self.alert_threshold)) and not is_expired

        result = {
            "days_remaining": None,
            "percentage_elapsed": percentage_elapsed,
            "percentage_remaining": percentage_remaining,
            "expiration_date": expiration_date.isoformat(),
            "last_reset": last_reset.date().isoformat(),
            "last_reset_datetime": last_reset.isoformat(),
            "expiration_datetime": due.isoformat(),
            "hours_remaining": hours_remaining,
            "is_expired": is_expired,
            "is_warning": is_warning,
        }
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        return result

    async def async_reset(self) -> None:
        """Reset the timer to now."""
        self.last_reset_dt = dt_util.now()
        await self._save()
        await self.async_refresh()

    async def _save(self) -> None:
        """Persist data to storage."""
        if self.last_reset_dt is None:
            self.last_reset_dt = dt_util.now()
        await self._store.async_save(
            {
                "last_reset_dt": dt_util.as_local(self.last_reset_dt).isoformat(),
                "last_reset": dt_util.as_local(self.last_reset_dt).date().isoformat(),
            }
        )
