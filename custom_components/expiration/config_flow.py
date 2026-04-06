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
    CONF_HOURS_MAX,
    CONF_SHOW_IN_CALENDAR,
    DEFAULT_ALERT_THRESHOLD,
    DOMAIN,
)


class ExpirationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Expiration."""

    VERSION = 2

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_NAME].strip()

            # Ensure unique name
            await self.async_set_unique_id(name.lower().replace(" ", "_"))
            self._abort_if_unique_id_configured()

            if not name:
                errors[CONF_NAME] = "name_required"
            elif user_input[CONF_DAYS_MAX] < 1:
                errors[CONF_DAYS_MAX] = "days_min_one"
            elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_DAYS_MAX]:
                errors[CONF_ALERT_THRESHOLD] = "threshold_too_high"
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_NAME: name,
                        CONF_DAYS_MAX: user_input[CONF_DAYS_MAX],
                        CONF_ALERT_THRESHOLD: user_input[CONF_ALERT_THRESHOLD],
                        CONF_HOURS_MAX: user_input.get(CONF_HOURS_MAX, 0),
                    },
                    options={CONF_SHOW_IN_CALENDAR: True},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_DAYS_MAX, default=14): vol.All(int, vol.Range(min=1)),
                vol.Required(
                    CONF_ALERT_THRESHOLD, default=DEFAULT_ALERT_THRESHOLD
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(CONF_HOURS_MAX, default=0): vol.All(int, vol.Range(min=0)),
            }
        )

        return self.async_show_form(
            step_id="user",
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
            if user_input[CONF_DAYS_MAX] < 1:
                errors[CONF_DAYS_MAX] = "days_min_one"
            elif user_input[CONF_ALERT_THRESHOLD] >= user_input[CONF_DAYS_MAX]:
                errors[CONF_ALERT_THRESHOLD] = "threshold_too_high"
            else:
                keep_calendar = self._config_entry.options.get(
                    CONF_SHOW_IN_CALENDAR, True
                )
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data={
                        **self._config_entry.data,
                        CONF_DAYS_MAX: user_input[CONF_DAYS_MAX],
                        CONF_ALERT_THRESHOLD: user_input[CONF_ALERT_THRESHOLD],
                        CONF_HOURS_MAX: user_input.get(CONF_HOURS_MAX, 0),
                    },
                )
                return self.async_create_entry(
                    title="",
                    data={CONF_SHOW_IN_CALENDAR: keep_calendar},
                )

        current_days_max = self._config_entry.data.get(CONF_DAYS_MAX, 14)
        current_threshold = self._config_entry.data.get(
            CONF_ALERT_THRESHOLD, DEFAULT_ALERT_THRESHOLD
        )
        current_hours_max = self._config_entry.data.get(CONF_HOURS_MAX, 0)

        schema = vol.Schema(
            {
                vol.Required(CONF_DAYS_MAX, default=current_days_max): vol.All(
                    int, vol.Range(min=1)
                ),
                vol.Required(CONF_ALERT_THRESHOLD, default=current_threshold): vol.All(
                    int, vol.Range(min=0)
                ),
                vol.Optional(CONF_HOURS_MAX, default=current_hours_max): vol.All(
                    int, vol.Range(min=0)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
