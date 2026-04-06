"""Config flow for the Expiration integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    ConfigEntry,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

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
    ENTRY_TYPE_ITEM,
    MODE_DAY,
    MODE_HOUR,
)
from .hub_entry import async_ensure_hub_entry, hub_config_entry


class ExpirationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Expiration."""

    VERSION = 4

    def __init__(self) -> None:
        """Initialize flow."""
        super().__init__()
        self._item_name: str = ""
        self._item_mode: str = MODE_DAY

    @staticmethod
    @callback
    def async_supports_options_flow(config_entry: ConfigEntry) -> bool:
        """Options apply to item entries only (not the hub)."""
        return config_entry.data.get(CONF_ENTRY_TYPE) != ENTRY_TYPE_HUB

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ensure hub exists, then continue to item steps."""
        if hub_config_entry(self.hass):
            return await self.async_step_item()

        if user_input is not None:
            await async_ensure_hub_entry(self.hass)
            return await self.async_step_item()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    async def async_step_item(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: item name and mode."""
        errors: dict[str, str] = {}

        if hub_config_entry(self.hass) is None:
            await async_ensure_hub_entry(self.hass)

        if user_input is not None:
            name = user_input[CONF_NAME].strip()
            mode = user_input[CONF_MODE]

            if not name:
                errors[CONF_NAME] = "name_required"
            else:
                await self.async_set_unique_id(name.lower().replace(" ", "_"))
                self._abort_if_unique_id_configured()
                self._item_name = name
                self._item_mode = mode
                return await self.async_step_item_period()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_MODE, default=MODE_DAY): vol.In([MODE_DAY, MODE_HOUR]),
            }
        )

        return self.async_show_form(
            step_id="item",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_item_period(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: period and alert threshold."""
        errors: dict[str, str] = {}
        mode = self._item_mode

        if user_input is not None:
            if mode == MODE_DAY:
                if user_input[CONF_DAYS_MAX] < 1:
                    errors[CONF_DAYS_MAX] = "days_min_one"
                elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_DAYS_MAX]:
                    errors[CONF_ALERT_THRESHOLD] = "threshold_too_high"
            elif mode == MODE_HOUR:
                if user_input[CONF_HOURS_MAX] < 1:
                    errors[CONF_HOURS_MAX] = "hours_min_one"
                elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_HOURS_MAX]:
                    errors[CONF_ALERT_THRESHOLD] = "threshold_hours_too_high"

            if not errors:
                data: dict[str, Any] = {
                    CONF_ENTRY_TYPE: ENTRY_TYPE_ITEM,
                    CONF_NAME: self._item_name,
                    CONF_MODE: mode,
                    CONF_ALERT_THRESHOLD: user_input[CONF_ALERT_THRESHOLD],
                }
                if mode == MODE_DAY:
                    data[CONF_DAYS_MAX] = user_input[CONF_DAYS_MAX]
                    data[CONF_HOURS_MAX] = 0
                else:
                    data[CONF_DAYS_MAX] = 0
                    data[CONF_HOURS_MAX] = user_input[CONF_HOURS_MAX]

                return self.async_create_entry(
                    title=self._item_name,
                    data=data,
                    options={CONF_SHOW_IN_CALENDAR: True},
                )

        if mode == MODE_DAY:
            schema = vol.Schema(
                {
                    vol.Required(CONF_DAYS_MAX, default=14): vol.All(int, vol.Range(min=1)),
                    vol.Required(
                        CONF_ALERT_THRESHOLD, default=DEFAULT_ALERT_THRESHOLD
                    ): vol.All(int, vol.Range(min=0)),
                }
            )
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOURS_MAX, default=48): vol.All(int, vol.Range(min=1)),
                    vol.Required(
                        CONF_ALERT_THRESHOLD, default=DEFAULT_ALERT_THRESHOLD
                    ): vol.All(int, vol.Range(min=0)),
                }
            )

        return self.async_show_form(
            step_id="item_period",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return ExpirationOptionsFlow(config_entry)


class ExpirationOptionsFlow(OptionsFlow):
    """Handle options for an existing Expiration entry."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mode = user_input[CONF_MODE]
            if mode == MODE_DAY:
                if user_input[CONF_DAYS_MAX] < 1:
                    errors[CONF_DAYS_MAX] = "days_min_one"
                elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_DAYS_MAX]:
                    errors[CONF_ALERT_THRESHOLD] = "threshold_too_high"
            elif mode == MODE_HOUR:
                if user_input[CONF_HOURS_MAX] < 1:
                    errors[CONF_HOURS_MAX] = "hours_min_one"
                elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_HOURS_MAX]:
                    errors[CONF_ALERT_THRESHOLD] = "threshold_hours_too_high"

            if not errors:
                keep_calendar = self._config_entry.options.get(
                    CONF_SHOW_IN_CALENDAR, True
                )
                data: dict[str, Any] = {
                    **self._config_entry.data,
                    CONF_MODE: mode,
                    CONF_ALERT_THRESHOLD: user_input[CONF_ALERT_THRESHOLD],
                }
                if mode == MODE_DAY:
                    data[CONF_DAYS_MAX] = user_input[CONF_DAYS_MAX]
                    data[CONF_HOURS_MAX] = 0
                else:
                    data[CONF_DAYS_MAX] = 0
                    data[CONF_HOURS_MAX] = user_input[CONF_HOURS_MAX]

                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=data,
                )
                return self.async_create_entry(
                    title="",
                    data={CONF_SHOW_IN_CALENDAR: keep_calendar},
                )

        current_mode = self._config_entry.data.get(CONF_MODE, MODE_DAY)
        raw_days = self._config_entry.data.get(CONF_DAYS_MAX, 14)
        raw_hours = self._config_entry.data.get(CONF_HOURS_MAX, 48)
        if current_mode == MODE_DAY:
            current_days_max = max(1, raw_days) if raw_days else 14
            current_hours_max = 48
        else:
            current_days_max = 14
            current_hours_max = max(1, raw_hours) if raw_hours else 48
        current_threshold = self._config_entry.data.get(
            CONF_ALERT_THRESHOLD, DEFAULT_ALERT_THRESHOLD
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_MODE, default=current_mode): vol.In(
                    [MODE_DAY, MODE_HOUR]
                ),
                vol.Required(CONF_DAYS_MAX, default=current_days_max): vol.All(
                    int, vol.Range(min=1)
                ),
                vol.Required(CONF_HOURS_MAX, default=current_hours_max): vol.All(
                    int, vol.Range(min=1)
                ),
                vol.Required(CONF_ALERT_THRESHOLD, default=current_threshold): vol.All(
                    int, vol.Range(min=0)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
