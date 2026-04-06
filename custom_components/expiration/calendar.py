"""Calendar platform: single aggregated Expiration calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityDescription,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ENTRY_TYPE,
    CONF_SHOW_IN_CALENDAR,
    DOMAIN,
    ENTRY_TYPE_HUB,
    MODE_HOUR,
)
from .coordinator import ExpirationCoordinator
from .hub import ExpirationHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calendar (single entity for the whole integration)."""
    if entry.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_HUB:
        return
    if DOMAIN not in hass.data or "hub" not in hass.data[DOMAIN]:
        return
    if hass.data[DOMAIN].get("_expiration_calendar_entity_added"):
        return

    registry = er.async_get(hass)
    if registry.async_get_entity_id("calendar", DOMAIN, "expiration_aggregated_calendar"):
        hass.data[DOMAIN]["_expiration_calendar_entity_added"] = True
        return

    hub: ExpirationHub = hass.data[DOMAIN]["hub"]
    async_add_entities([ExpirationAggregatedCalendar(hass, hub)])
    hass.data[DOMAIN]["_expiration_calendar_entity_added"] = True


def _build_due_event(coordinator: ExpirationCoordinator) -> CalendarEvent | None:
    """Build the due event for one expiration item."""
    data = coordinator.data
    if not data:
        return None

    name = coordinator.item_name
    uid = f"{coordinator.entry_id}_due"

    if coordinator.mode == MODE_HOUR:
        exp = data.get("expiration_datetime")
        if not exp:
            return None
        start = dt_util.parse_datetime(exp)
        if start is None:
            return None
        start = dt_util.as_local(start)
        end = start + timedelta(hours=1)
        return CalendarEvent(
            summary=name,
            start=start,
            end=end,
            uid=uid,
        )

    exp_date = data.get("expiration_date")
    if not exp_date:
        return None
    d = date.fromisoformat(exp_date)
    return CalendarEvent(
        summary=name,
        start=d,
        end=d,
        uid=uid,
    )


def _event_overlaps(
    event: CalendarEvent, start: datetime, end: datetime
) -> bool:
    """Return True if event overlaps [start, end)."""
    es = event.start_datetime_local
    ee = event.end_datetime_local
    return es < end and ee > start


class ExpirationAggregatedCalendar(CalendarEntity):
    """One calendar listing due dates for all enabled expiration items."""

    def __init__(self, hass: HomeAssistant, hub: ExpirationHub) -> None:
        """Initialize aggregated calendar."""
        self.hass = hass
        self._hub = hub
        self.entity_description = CalendarEntityDescription(
            key="expiration_calendar",
            name="Shared calendar",
            initial_color="#4285F4",
        )
        self._attr_unique_id = "expiration_aggregated_calendar"
        self._attr_has_entity_name = False
        self._attr_translation_key = "expiration_calendar"
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "hub")},
            name="Expiration Calendar",
            translation_key="expiration_hub",
            manufacturer="Expiration",
            model="Expiration",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to updates from expiration items."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_calendar_update",
                self.async_write_ha_state,
            )
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming due event across all items."""
        now = dt_util.now()
        start = now - timedelta(days=365)
        end = now + timedelta(days=365 * 5)
        events = self._gather_events(start, end)
        for ev in sorted(events, key=lambda e: e.start_datetime_local):
            if ev.end_datetime_local > now:
                return ev
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return due events in the requested window."""
        return self._gather_events(start_date, end_date)

    def _gather_events(self, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Collect due events from coordinators."""
        if not self._hub.calendar_enabled:
            return []

        out: list[CalendarEvent] = []
        for entry_id, coord in self._hub.coordinators.items():
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            if not entry.options.get(CONF_SHOW_IN_CALENDAR, True):
                continue
            if not isinstance(coord, ExpirationCoordinator):
                continue

            ev = _build_due_event(coord)
            if ev is None:
                continue
            if _event_overlaps(ev, start_date, end_date):
                out.append(ev)
        return out
