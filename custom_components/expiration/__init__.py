"""The Expiration integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_ALERT_THRESHOLD,
    CONF_DAYS_MAX,
    CONF_HOURS_MAX,
    CONF_SHOW_IN_CALENDAR,
    DEFAULT_ALERT_THRESHOLD,
    DOMAIN,
)
from .coordinator import ExpirationCoordinator
from .hub import ExpirationHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.SWITCH,
]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entries."""
    if config_entry.version > 2:
        return False

    if config_entry.version < 2:
        data = dict(config_entry.data)
        data.setdefault(CONF_HOURS_MAX, 0)
        options = dict(config_entry.options)
        options.setdefault(CONF_SHOW_IN_CALENDAR, True)
        hass.config_entries.async_update_entry(
            config_entry,
            data=data,
            options=options,
            version=2,
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Expiration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    if "hub" not in hass.data[DOMAIN]:
        hub = ExpirationHub(hass)
        await hub.async_load()
        hass.data[DOMAIN]["hub"] = hub

    hub: ExpirationHub = hass.data[DOMAIN]["hub"]

    coordinator = ExpirationCoordinator(
        hass=hass,
        entry_id=entry.entry_id,
        name=entry.data[CONF_NAME],
        days_max=entry.data[CONF_DAYS_MAX],
        alert_threshold=entry.data.get(CONF_ALERT_THRESHOLD, DEFAULT_ALERT_THRESHOLD),
        hours_max=entry.data.get(CONF_HOURS_MAX, 0),
    )

    await coordinator.async_setup()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    hub.register_coordinator(entry.entry_id, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    domain_data = hass.data.get(DOMAIN, {})
    other_entries = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id
    ]
    if other_entries and domain_data.get("hub_owner_entry_id") == entry.entry_id:
        new_owner = other_entries[0].entry_id
        registry = er.async_get(hass)
        for platform, unique_id in (
            ("calendar", "expiration_aggregated_calendar"),
            ("switch", "expiration_hub_calendar_enabled"),
        ):
            entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
            if entity_id:
                registry.async_update_entity(entity_id, config_entry_id=new_owner)
        domain_data["hub_owner_entry_id"] = new_owner

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if "hub" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["hub"].unregister_coordinator(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
