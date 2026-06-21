"""Button platform for the Expiration integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_DAYS_REMAINING,
    ATTR_END_DATE,
    ATTR_LAST_RESET_DATETIME,
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_TYPE_HUB,
)
from .coordinator import ExpirationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Expiration buttons from a config entry."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        return

    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ExpirationResetButton(coordinator, entry),
            ExpirationStepBackButton(coordinator, entry),
            ExpirationStepForwardButton(coordinator, entry),
        ]
    )


class ExpirationButtonBase(CoordinatorEntity[ExpirationCoordinator], ButtonEntity):
    """Base class for Expiration buttons."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )


class ExpirationResetButton(ExpirationButtonBase):
    """Button to reset the expiration timer."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reset button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_reset"
        self._attr_translation_key = "reset"
        self._attr_icon = "mdi:restart"

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Expose remaining days and end date on the button."""
        data = self.coordinator.data or {}
        return {
            ATTR_DAYS_REMAINING: data.get("days_remaining"),
            ATTR_END_DATE: data.get("expiration_date"),
            ATTR_LAST_RESET_DATETIME: data.get("last_reset_datetime"),
        }

    async def async_press(self) -> None:
        """Handle the button press — reset the timer."""
        await self.coordinator.async_reset()


class ExpirationStepBackButton(ExpirationButtonBase):
    """Button to increase remaining time by one day/hour."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the step back button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_step_back"
        self._attr_translation_key = "step_back"
        self._attr_icon = "mdi:chevron-left"

    async def async_press(self) -> None:
        """Increase remaining by moving last reset later."""
        await self.coordinator.async_step_last_reset_forward()


class ExpirationStepForwardButton(ExpirationButtonBase):
    """Button to decrease remaining time by one day/hour."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the step forward button."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_step_forward"
        self._attr_translation_key = "step_forward"
        self._attr_icon = "mdi:chevron-right"

    async def async_press(self) -> None:
        """Decrease remaining by moving last reset earlier."""
        await self.coordinator.async_step_last_reset_back()
