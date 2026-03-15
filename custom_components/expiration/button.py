"""Button platform for the Expiration integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ExpirationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Expiration button from a config entry."""
    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ExpirationResetButton(coordinator, entry)])


class ExpirationResetButton(CoordinatorEntity[ExpirationCoordinator], ButtonEntity):
    """Button to reset the expiration timer."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reset button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reset"
        self._attr_name = f"{entry.data[CONF_NAME]} Reset"
        self._attr_icon = "mdi:restart"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )

    async def async_press(self) -> None:
        """Handle the button press — reset the timer."""
        await self.coordinator.async_reset()
