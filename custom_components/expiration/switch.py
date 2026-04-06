"""Switch platform: global calendar visibility + per-item visibility."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTRY_TYPE, CONF_SHOW_IN_CALENDAR, DOMAIN, ENTRY_TYPE_HUB
from .coordinator import ExpirationCoordinator
from .hub import ExpirationHub


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    if DOMAIN not in hass.data or "hub" not in hass.data[DOMAIN]:
        return

    hub: ExpirationHub = hass.data[DOMAIN]["hub"]

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        if hass.data[DOMAIN].get("_expiration_hub_switch_added"):
            return
        registry = er.async_get(hass)
        if registry.async_get_entity_id("switch", DOMAIN, "expiration_hub_calendar_enabled"):
            hass.data[DOMAIN]["_expiration_hub_switch_added"] = True
            return
        async_add_entities([ExpirationHubCalendarSwitch(hass, hub)])
        hass.data[DOMAIN]["_expiration_hub_switch_added"] = True
        return

    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ExpirationItemCalendarSwitch(coordinator, entry)])


class ExpirationHubCalendarSwitch(SwitchEntity):
    """Master switch: show/hide all Expiration events in the calendar."""

    def __init__(self, hass: HomeAssistant, hub: ExpirationHub) -> None:
        """Initialize hub switch."""
        self.hass = hass
        self._hub = hub
        self._attr_unique_id = "expiration_hub_calendar_enabled"
        self._attr_has_entity_name = False
        self._attr_translation_key = "calendar_master"
        self._attr_icon = "mdi:calendar-multiple"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "hub")},
            name="Expiration Calendar",
            translation_key="expiration_hub",
            manufacturer="Expiration",
            model="Expiration",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if calendar events are enabled."""
        return self._hub.calendar_enabled

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable calendar events."""
        self._hub.calendar_enabled = True
        await self._hub.async_save()
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable calendar events."""
        self._hub.calendar_enabled = False
        await self._hub.async_save()
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        self.async_write_ha_state()


class ExpirationItemCalendarSwitch(CoordinatorEntity[ExpirationCoordinator], SwitchEntity):
    """Per-item switch: include this expiration in the shared calendar."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize item switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar_show"
        self._attr_has_entity_name = True
        self._attr_translation_key = "calendar_item"
        self._attr_icon = "mdi:calendar-check"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if this item is shown in the calendar."""
        return self._entry.options.get(CONF_SHOW_IN_CALENDAR, True)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Show this item in the calendar."""
        new_opts = {**self._entry.options, CONF_SHOW_IN_CALENDAR: True}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: object) -> None:
        """Hide this item from the calendar."""
        new_opts = {**self._entry.options, CONF_SHOW_IN_CALENDAR: False}
        self.hass.config_entries.async_update_entry(self._entry, options=new_opts)
        async_dispatcher_send(self.hass, f"{DOMAIN}_calendar_update")
        self.async_write_ha_state()
