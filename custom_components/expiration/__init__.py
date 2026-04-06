"""The Expiration integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ALERT_THRESHOLD,
    CONF_DAYS_MAX,
    CONF_ENTRY_TYPE,
    CONF_HOURS_MAX,
    CONF_MODE,
    CONF_SHOW_IN_CALENDAR,
    DEFAULT_ALERT_THRESHOLD,
    DOMAIN,
    ENTRY_TYPE_HUB,
    MODE_DAY,
    MODE_HOUR,
)
from .coordinator import ExpirationCoordinator
from .hub import ExpirationHub
from .hub_entry import async_ensure_hub_entry

_LOGGER = logging.getLogger(__name__)

HUB_PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SWITCH]
ITEM_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SWITCH]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entries."""
    if config_entry.version > 4:
        return False

    entry = config_entry
    if entry.version < 2:
        data = dict(entry.data)
        data.setdefault(CONF_HOURS_MAX, 0)
        options = dict(entry.options)
        options.setdefault(CONF_SHOW_IN_CALENDAR, True)
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options=options,
            version=2,
        )
        entry = hass.config_entries.async_get_entry(entry.entry_id)

    if entry is None:
        return False

    if entry.version < 3:
        data = dict(entry.data)
        data.setdefault(CONF_HOURS_MAX, 0)
        if data.get(CONF_HOURS_MAX, 0) > 0:
            data[CONF_MODE] = MODE_HOUR
            data[CONF_DAYS_MAX] = 0
        else:
            data[CONF_MODE] = MODE_DAY
            data[CONF_HOURS_MAX] = 0
        hass.config_entries.async_update_entry(entry, data=data, version=3)
        entry = hass.config_entries.async_get_entry(entry.entry_id)

    if entry is None:
        return False

    if entry.version < 4:
        data = dict(entry.data)
        data.setdefault(CONF_ENTRY_TYPE, ENTRY_TYPE_ITEM)
        hass.config_entries.async_update_entry(entry, data=data, version=4)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Expiration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        if "hub" not in hass.data[DOMAIN]:
            hub = ExpirationHub(hass)
            await hub.async_load()
            hass.data[DOMAIN]["hub"] = hub

        await hass.config_entries.async_forward_entry_setups(entry, HUB_PLATFORMS)
        return True

    await async_ensure_hub_entry(hass)

    if "hub" not in hass.data[DOMAIN]:
        hub = ExpirationHub(hass)
        await hub.async_load()
        hass.data[DOMAIN]["hub"] = hub

    hub: ExpirationHub = hass.data[DOMAIN]["hub"]

    mode = entry.data.get(CONF_MODE, MODE_DAY)
    days_max = entry.data.get(CONF_DAYS_MAX, 14)
    hours_max = entry.data.get(CONF_HOURS_MAX, 0)
    if mode == MODE_HOUR:
        days_max = 0
    else:
        hours_max = 0

    coordinator = ExpirationCoordinator(
        hass=hass,
        entry_id=entry.entry_id,
        name=entry.data[CONF_NAME],
        mode=mode,
        days_max=days_max,
        alert_threshold=entry.data.get(CONF_ALERT_THRESHOLD, DEFAULT_ALERT_THRESHOLD),
        hours_max=hours_max,
    )

    await coordinator.async_setup()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    hub.register_coordinator(entry.entry_id, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, ITEM_PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        return await hass.config_entries.async_unload_platforms(entry, HUB_PLATFORMS)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, ITEM_PLATFORMS)
    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop(entry.entry_id, None)
        if "hub" in domain_data:
            domain_data["hub"].unregister_coordinator(entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up after config entry removal."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        domain_data = hass.data.get(DOMAIN, {})
        domain_data.pop("_expiration_calendar_entity_added", None)
        domain_data.pop("_expiration_hub_switch_added", None)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
