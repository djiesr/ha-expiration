# Expiration — Home Assistant Integration

Track expiration and replacement schedules for household items directly in Home Assistant.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/djiesr/ha-expiration.svg)](https://github.com/djiesr/ha-expiration/releases)
[![Validate](https://github.com/djiesr/ha-expiration/actions/workflows/validate.yml/badge.svg)](https://github.com/djiesr/ha-expiration/actions/workflows/validate.yml)

## What it does

Add any item you want to track — sponges, filters, batteries, medications, etc. — and set how often it should be replaced. Each item gets:

- A **days remaining** sensor (with start/end dates in attributes)
- A **% elapsed** sensor (integer %)
- A **remaining usage** sensor (100% at start, counts down to 0%)
- Optionally **hours remaining** (if you set *Hours until expiration* when adding or in options)
- A **Reset button** to restart the counter (attributes: days remaining, end date, last reset date/time)

The integration also exposes a **single shared calendar** entity listing due dates for all items, with a **master switch** (on the hub device) and a **per-item switch** to show or hide each item in that calendar.

The reset date/time is persisted in Home Assistant's storage, so it survives restarts.

## Entities per item

| Entity | Type | Example value |
|--------|------|---------------|
| `sensor.<name>_days_remaining` | Sensor | `9 days` |
| `sensor.<name>_elapsed` | Sensor | `35 %` (integer) |
| `sensor.<name>_remaining_usage` | Sensor | `65 %` (100% → 0%) |
| `sensor.<name>_hours_remaining` | Sensor | `12.5 h` (if hours configured) |
| `switch.<name>_show_in_calendar` | Switch | Per-item visibility in the shared calendar |
| `button.<name>_reset` | Button | — |
| *(shared)* `calendar.*` | Calendar | One calendar for all items (device **Expiration**) |
| *(shared)* `switch.*` | Switch | Master: enable/disable all calendar events (same hub device) |

### Sensor attributes

```yaml
# Days remaining sensor attributes (also: start_date, end_date)
last_reset: "2026-03-01"
expiration_date: "2026-03-15"
start_date: "2026-03-01"   # same as last_reset
end_date: "2026-03-15"     # same as expiration_date
days_max: 14
alert_threshold: 3
status: ok  # ok | warning | expired

# Reset button attributes
# days_remaining, end_date, last_reset_datetime

# Calendar: all-day due date at end of day (days mode), or timed event at due hour (hours mode)
```

## Installation

### Via HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three-dot menu and select **Custom repositories**
4. Add `https://github.com/djiesr/ha-expiration` with category **Integration**
5. Search for **Expiration** and install it
6. Restart Home Assistant

### Manual

1. Download the latest release zip from the [Releases page](https://github.com/djiesr/ha-expiration/releases)
2. Extract and copy the `custom_components/expiration` folder into your HA `custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services**
2. Click **+ Add Integration**
3. Search for **Expiration**
4. Fill in the form:
   - **Item name** — e.g. `Kitchen Sponge`
   - **Days until expiration** — e.g. `14`
   - **Alert threshold** — number of days before expiration to trigger warning state (e.g. `3`)
   - **Hours until expiration** (optional) — e.g. `75` for an hours-remaining sensor and a timed calendar event; day sensors stay in **days** only.

Repeat for each item you want to track. Each item creates its own device with sensors + button + per-item calendar switch. The **hub** device holds the shared calendar and the master calendar switch.

## Dashboard example

```yaml
type: entities
title: Expiration Tracker
entities:
  - entity: sensor.kitchen_sponge_days_remaining
  - entity: sensor.kitchen_sponge_elapsed
  - entity: button.kitchen_sponge_reset
```

Or use a button card for the reset:

```yaml
type: button
entity: button.kitchen_sponge_reset
name: Reset Sponge
icon: mdi:restart
```

## Automation example

Send a notification when an item is about to expire:

```yaml
automation:
  alias: "Alert - Kitchen Sponge expiring soon"
  trigger:
    - platform: numeric_state
      entity_id: sensor.kitchen_sponge_days_remaining
      below: 3
  action:
    - service: notify.notify
      data:
        message: "The kitchen sponge needs to be replaced in {{ states('sensor.kitchen_sponge_days_remaining') }} days!"
```

## Requirements

- Home Assistant 2023.5.0 or newer

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.
