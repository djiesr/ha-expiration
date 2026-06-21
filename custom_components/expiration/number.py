"""Number platform for editable Expiration values."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTRY_TYPE, CONF_MODE, DOMAIN, ENTRY_TYPE_HUB, MODE_DAY, MODE_HOUR
from .coordinator import ExpirationCoordinator

MAX_CYCLE_DAYS = 365
MAX_CYCLE_HOURS = 8760


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up editable number entities."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_HUB:
        return

    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]
    mode = entry.data.get(CONF_MODE, MODE_DAY)
    entities: list[NumberEntity] = [
        ExpirationCyclePeriodNumber(coordinator, entry),
        ExpirationElapsedNumber(coordinator, entry),
    ]
    if mode == MODE_DAY:
        entities.append(ExpirationDaysRemainingNumber(coordinator, entry))
    else:
        entities.append(ExpirationHoursRemainingNumber(coordinator, entry))

    async_add_entities(entities)


class ExpirationNumberBase(CoordinatorEntity[ExpirationCoordinator], NumberEntity):
    """Base class for Expiration number entities."""

    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )


class ExpirationCyclePeriodNumber(ExpirationNumberBase):
    """Editable cycle length (days or hours)."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize cycle period number."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cycle_period"
        self._attr_translation_key = "cycle_period"
        self._attr_icon = "mdi:repeat"
        self._attr_native_min_value = 1
        self._attr_native_step = 1
        if entry.data.get(CONF_MODE, MODE_DAY) == MODE_HOUR:
            self._attr_native_max_value = MAX_CYCLE_HOURS
            self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        else:
            self._attr_native_max_value = MAX_CYCLE_DAYS
            self._attr_native_unit_of_measurement = UnitOfTime.DAYS

    @property
    def native_value(self) -> float | None:
        """Return configured cycle length."""
        return float(self.coordinator.cycle_limit())

    async def async_set_native_value(self, value: float) -> None:
        """Update cycle length with validation."""
        await self.coordinator.async_set_cycle_period(self._entry, value)


class ExpirationElapsedNumber(ExpirationNumberBase):
    """Editable elapsed time since last reset."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize elapsed number."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_time_elapsed"
        self._attr_translation_key = "time_elapsed"
        self._attr_icon = "mdi:history"
        self._attr_native_min_value = 0
        if entry.data.get(CONF_MODE, MODE_DAY) == MODE_HOUR:
            self._attr_native_step = 0.1
            self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        else:
            self._attr_native_step = 1
            self._attr_native_unit_of_measurement = UnitOfTime.DAYS

    @property
    def native_max_value(self) -> float:
        """Elapsed cannot exceed the cycle length."""
        return float(self.coordinator.cycle_limit())

    @property
    def native_value(self) -> float | None:
        """Return elapsed days or hours."""
        if not self.coordinator.data:
            return self.coordinator.current_elapsed()
        if self.coordinator.mode == MODE_HOUR:
            elapsed = self.coordinator.data.get("elapsed_hours")
        else:
            elapsed = self.coordinator.data.get("elapsed_days")
        if elapsed is None:
            return self.coordinator.current_elapsed()
        return float(min(elapsed, self.coordinator.cycle_limit()))

    async def async_set_native_value(self, value: float) -> None:
        """Set elapsed time (clamped to 0..cycle)."""
        await self.coordinator.async_set_elapsed(value)


class ExpirationDaysRemainingNumber(ExpirationNumberBase):
    """Editable days remaining."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize days remaining number."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_days_remaining"
        self._attr_translation_key = "days_remaining"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_native_min_value = 0
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.DAYS

    @property
    def native_max_value(self) -> float:
        """Remaining cannot exceed cycle minus elapsed (max = cycle when elapsed is 0)."""
        return float(self.coordinator.cycle_limit())

    @property
    def native_value(self) -> float | None:
        """Return days remaining."""
        if not self.coordinator.data:
            return None
        remaining = self.coordinator.data.get("days_remaining")
        if remaining is None:
            return None
        return float(max(0, min(remaining, self.coordinator.cycle_limit())))

    async def async_set_native_value(self, value: float) -> None:
        """Set days remaining (0..cycle)."""
        await self.coordinator.async_set_remaining(value)


class ExpirationHoursRemainingNumber(ExpirationNumberBase):
    """Editable hours remaining."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize hours remaining number."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_hours_remaining"
        self._attr_translation_key = "hours_remaining"
        self._attr_icon = "mdi:timer-sand"
        self._attr_native_min_value = 0
        self._attr_native_step = 0.1
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS

    @property
    def native_max_value(self) -> float:
        """Remaining cannot exceed the cycle length."""
        return float(self.coordinator.cycle_limit())

    @property
    def native_value(self) -> float | None:
        """Return hours remaining."""
        if not self.coordinator.data:
            return None
        remaining = self.coordinator.data.get("hours_remaining")
        if remaining is None:
            return None
        return float(max(0.0, min(float(remaining), float(self.coordinator.cycle_limit()))))

    async def async_set_native_value(self, value: float) -> None:
        """Set hours remaining (0..cycle)."""
        await self.coordinator.async_set_remaining(value)
