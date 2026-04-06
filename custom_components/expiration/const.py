"""Constants for the Expiration integration."""

DOMAIN = "expiration"

CONF_DAYS_MAX = "days_max"
CONF_ALERT_THRESHOLD = "alert_threshold"
CONF_HOURS_MAX = "hours_max"
CONF_SHOW_IN_CALENDAR = "show_in_calendar"

ATTR_LAST_RESET = "last_reset"
ATTR_LAST_RESET_DATETIME = "last_reset_datetime"
ATTR_DAYS_MAX = "days_max"
ATTR_ALERT_THRESHOLD = "alert_threshold"
ATTR_EXPIRATION_DATE = "expiration_date"
ATTR_EXPIRATION_DATETIME = "expiration_datetime"
ATTR_START_DATE = "start_date"
ATTR_END_DATE = "end_date"
ATTR_DAYS_REMAINING = "days_remaining"
ATTR_HOURS_REMAINING = "hours_remaining"

DEFAULT_ALERT_THRESHOLD = 3

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "expiration"
