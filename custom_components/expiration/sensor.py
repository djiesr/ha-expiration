"""Sensor platform for the Expiration integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ALERT_THRESHOLD,
    ATTR_DAYS_MAX,
    ATTR_END_DATE,
    ATTR_EXPIRATION_DATE,
    ATTR_HOURS_MAX,
    ATTR_LAST_RESET,
    ATTR_LAST_RESET_DATETIME,
    ATTR_START_DATE,
    CONF_MODE,
    DOMAIN,
    MODE_DAY,
    MODE_HOUR,
)
from .coordinator import ExpirationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Expiration sensors from a config entry."""
    coordinator: ExpirationCoordinator = hass.data[DOMAIN][entry.entry_id]

    mode = entry.data.get(CONF_MODE, MODE_DAY)
    entities: list[SensorEntity] = [
        ExpirationPercentSensor(coordinator, entry),
        ExpirationRemainingPercentSensor(coordinator, entry),
    ]
    if mode == MODE_DAY:
        entities.insert(0, ExpirationDaysSensor(coordinator, entry))
    else:
        entities.insert(0, ExpirationHoursSensor(coordinator, entry))

    async_add_entities(entities)


class ExpirationBaseSensor(CoordinatorEntity[ExpirationCoordinator], SensorEntity):
    """Base class for Expiration sensors."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data[CONF_NAME],
            manufacturer="Expiration",
            model="Expiration Tracker",
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Return common extra attributes."""
        data = self.coordinator.data or {}
        attrs: dict = {
            ATTR_LAST_RESET: data.get("last_reset"),
            ATTR_LAST_RESET_DATETIME: data.get("last_reset_datetime"),
            ATTR_EXPIRATION_DATE: data.get("expiration_date"),
            ATTR_ALERT_THRESHOLD: self.coordinator.alert_threshold,
        }
        if self.coordinator.mode == MODE_DAY:
            attrs[ATTR_DAYS_MAX] = self.coordinator.days_max
        else:
            attrs[ATTR_HOURS_MAX] = self.coordinator.hours_max
        return attrs


class ExpirationDaysSensor(ExpirationBaseSensor):
    """Sensor showing days remaining before expiration."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the days sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_days_remaining"
        self._attr_translation_key = "days_remaining"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfTime.DAYS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self) -> int | None:
        """Return the number of days remaining."""
        if self.coordinator.data:
            return self.coordinator.data["days_remaining"]
        return None

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        data = self.coordinator.data or {}
        if data.get("is_expired"):
            return "mdi:calendar-remove"
        if data.get("is_warning"):
            return "mdi:calendar-alert"
        return "mdi:calendar-clock"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including status."""
        attrs = super().extra_state_attributes
        data = self.coordinator.data or {}
        attrs[ATTR_START_DATE] = data.get("last_reset")
        attrs[ATTR_END_DATE] = data.get("expiration_date")
        if data.get("is_expired"):
            attrs["status"] = "expired"
        elif data.get("is_warning"):
            attrs["status"] = "warning"
        else:
            attrs["status"] = "ok"
        return attrs


class ExpirationPercentSensor(ExpirationBaseSensor):
    """Sensor showing percentage of time elapsed since last reset."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the percent sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_percentage_elapsed"
        self._attr_translation_key = "percentage_elapsed"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:percent"

    @property
    def native_value(self) -> int | None:
        """Return the percentage of time elapsed (integer, no decimals)."""
        if self.coordinator.data:
            return self.coordinator.data["percentage_elapsed"]
        return None


class ExpirationRemainingPercentSensor(ExpirationBaseSensor):
    """Sensor showing remaining usage percentage (100% at start, down to 0%)."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the remaining usage sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_remaining_usage"
        self._attr_translation_key = "remaining_usage"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:progress-clock"

    @property
    def native_value(self) -> int | None:
        """Return the remaining usage percentage."""
        if self.coordinator.data:
            return self.coordinator.data["percentage_remaining"]
        return None


class ExpirationHoursSensor(ExpirationBaseSensor):
    """Sensor showing hours remaining (hour mode)."""

    def __init__(
        self,
        coordinator: ExpirationCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the hours sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_hours_remaining"
        self._attr_translation_key = "hours_remaining"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfTime.HOURS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:timer-sand"

    @property
    def native_value(self) -> float | None:
        """Return hours remaining."""
        if self.coordinator.data:
            return self.coordinator.data.get("hours_remaining")
        return None

    @property
    def icon(self) -> str:
        """Return icon based on state."""
        data = self.coordinator.data or {}
        if data.get("is_expired"):
            return "mdi:timer-remove"
        if data.get("is_warning"):
            return "mdi:timer-alert"
        return "mdi:timer-sand"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes including status."""
        attrs = super().extra_state_attributes
        data = self.coordinator.data or {}
        attrs[ATTR_START_DATE] = data.get("last_reset")
        attrs[ATTR_END_DATE] = data.get("expiration_date")
        if data.get("is_expired"):
            attrs["status"] = "expired"
        elif data.get("is_warning"):
            attrs["status"] = "warning"
        else:
            attrs["status"] = "ok"
        return attrs
