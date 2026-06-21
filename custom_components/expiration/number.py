"""Number platform for editable Expiration cycle period."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTRY_TYPE, CONF_MODE, DOMAIN, ENTRY_TYPE_HUB, MODE_DAY
from .coordinator import ExpirationCoordinator

MAX_CYCLE_DAYS = 365
MAX_CYCLE_HOURS = 8760


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up editable cycle period number."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        return

    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ExpirationCyclePeriodNumber(coordinator, entry)])


class ExpirationCyclePeriodNumber(CoordinatorEntity[ExpirationCoordinator], NumberEntity):
    """Editable cycle length (days or hours), whole units only."""

    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True
    _attr_translation_key = "cycle_period"
    _attr_icon = "mdi:repeat"
    _attr_native_min_value = 1
    _attr_native_step = 1

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize cycle period number."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_cycle_period"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )
        if entry.data.get(CONF_MODE, MODE_DAY) == MODE_HOUR:
            self._attr_native_max_value = MAX_CYCLE_HOURS
            self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        else:
            self._attr_native_max_value = MAX_CYCLE_DAYS
            self._attr_native_unit_of_measurement = UnitOfTime.DAYS

    @property
    def native_value(self) -> int | None:
        """Return configured cycle length as a whole number."""
        return self.coordinator.cycle_limit()

    async def async_set_native_value(self, value: float) -> None:
        """Update cycle length with validation."""
        await self.coordinator.async_set_cycle_period(self._entry, int(value))
