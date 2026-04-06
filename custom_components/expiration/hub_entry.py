"""Create and migrate the singleton hub config entry (calendar + master switch)."""

from __future__ import annotations

import asyncio
import inspect
import logging
from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import SOURCE_USER, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import CONF_ENTRY_TYPE, DOMAIN, ENTRY_TYPE_HUB

_LOGGER = logging.getLogger(__name__)

HUB_UNIQUE_ID = "expiration_hub"


def _build_hub_config_entry() -> ConfigEntry:
    """Build a hub ConfigEntry compatible with the running Home Assistant version.

    ConfigEntry.__init__ signature changes across HA releases (e.g. discovery_keys,
    subentries_data). Only pass kwargs the current version accepts.
    """
    kwargs: dict[str, Any] = {
        "version": 4,
        "minor_version": 0,
        "domain": DOMAIN,
        "title": "Expiration",
        "data": {CONF_ENTRY_TYPE: ENTRY_TYPE_HUB},
        "options": {},
        "unique_id": HUB_UNIQUE_ID,
        "source": SOURCE_USER,
    }
    sig = inspect.signature(ConfigEntry.__init__)
    if "discovery_keys" in sig.parameters:
        kwargs["discovery_keys"] = MappingProxyType({})
    if "subentries_data" in sig.parameters:
        kwargs["subentries_data"] = None
    return ConfigEntry(**kwargs)


def hub_config_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """Return the hub config entry if it exists."""
    for e in hass.config_entries.async_entries(DOMAIN):
        if e.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
            return e
    return None


def _migrate_calendar_entities_to_hub(hass: HomeAssistant, hub_entry_id: str) -> None:
    """Re-link calendar + hub switch to the hub entry after migration."""
    registry = er.async_get(hass)
    for platform, unique_id in (
        ("calendar", "expiration_aggregated_calendar"),
        ("switch", "expiration_hub_calendar_enabled"),
    ):
        entity_id = registry.async_get_entity_id(platform, DOMAIN, unique_id)
        if entity_id:
            ent = registry.async_get(entity_id)
            if ent and ent.config_entry_id != hub_entry_id:
                registry.async_update_entity(entity_id, config_entry_id=hub_entry_id)


async def async_ensure_hub_entry(hass: HomeAssistant) -> ConfigEntry | None:
    """Ensure a hub config entry exists (singleton). Used for migration."""
    existing = hub_config_entry(hass)
    if existing:
        return existing

    hass.data.setdefault(DOMAIN, {})
    lock = hass.data[DOMAIN].setdefault("_ensure_hub_lock", asyncio.Lock())
    async with lock:
        existing = hub_config_entry(hass)
        if existing:
            return existing

        _LOGGER.info("Creating Expiration hub config entry for calendar")

        entry = _build_hub_config_entry()
        await hass.config_entries.async_add(entry)
        hub_entry_id = entry.entry_id
        _migrate_calendar_entities_to_hub(hass, hub_entry_id)
        return hass.config_entries.async_get_entry(hub_entry_id)
