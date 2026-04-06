# Expiration — Home Assistant Integration

Track expiration and replacement schedules for household items directly in Home Assistant.

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/djiesr/ha-expiration.svg)](https://github.com/djiesr/ha-expiration/releases)
[![Validate](https://github.com/djiesr/ha-expiration/actions/workflows/validate.yml/badge.svg)](https://github.com/djiesr/ha-expiration/actions/workflows/validate.yml)

## What it does

Add any item you want to track — sponges, filters, batteries, medications, etc. — and set how often it should be replaced.

The integration uses a **hub** config entry (shared **calendar** + **master switch** for calendar visibility) and a separate **config entry per item** (sensors, reset button, per-item calendar visibility). Removing an item does **not** remove the hub.

**First time you add Expiration** (no hub yet):

1. **Hub step** — short intro, then confirm to create the hub (calendar + master switch).
2. **Item step 1** — **Item name** and **Countdown type** (**Days** or **Hours**): day mode uses day-based sensors and all-day calendar events; hour mode uses hour-based sensors and a timed calendar event.
3. **Item step 2** — **Period** and **Alert threshold** (labels depend on mode: days vs hours until expiration, and threshold in days or hours before due).

**Adding another item later** (hub already exists): you go **directly** to the item steps (step 1 + step 2).

For each item:

- **Day mode**: **days remaining** sensor, **% elapsed**, **remaining usage %** (calendar: **all-day** event on the due date).
- **Hour mode**: **hours remaining** sensor, **% elapsed**, **remaining usage %** (calendar: **timed** event at the due date/time). Thresholds are in **hours**.

Common to all items:

- A **Reset button** (attributes: days or hours remaining, end date, last reset date/time)

The **hub** device holds the shared calendar entity and the master switch. Each **item** has its own device with sensors, button, and per-item “show in calendar” switch.

The reset date/time is persisted in Home Assistant's storage, so it survives restarts.

### Language / translations

UI strings for the config flow, options, entity names, and hub device name are provided in **English** and **French** (`custom_components/expiration/translations/`). The language follows your Home Assistant UI / account language when available.

## Entities per item

Entity IDs use the slug derived from the item name (example: `kitchen_sponge`). Actual IDs may vary slightly depending on your HA version and naming.

| Entity | Type | Example value |
|--------|------|---------------|
| `sensor.<slug>_days_remaining` | Sensor | `9 days` (day mode only) |
| `sensor.<slug>_hours_remaining` | Sensor | `12.5 h` (hour mode only) |
| `sensor.<slug>_percentage_elapsed` | Sensor | `35 %` (integer) |
| `sensor.<slug>_remaining_usage` | Sensor | `65 %` (100% → 0%) |
| `switch.<slug>_…` | Switch | Per-item visibility in the shared calendar |
| `button.<slug>_reset` | Button | — |
| *(hub)* `calendar.*` | Calendar | Shared calendar (hub device: **Expiration Calendar** / **Expiration Calendrier** in FR) |
| *(hub)* `switch.*` | Switch | Master: enable/disable all calendar events on the hub device |

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

# Calendar: all-day due date (day mode), or timed event at due hour (hour mode)
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
4. **First run only**: create the **hub**, then complete **item step 1** (name + **Days** / **Hours**), then **item step 2** (period + alert threshold).
5. **Further items**: **Add integration → Expiration** again (or **Add integration** from the Expiration card) — you only fill the **item** steps.

**Options** (per item entry): adjust mode, period, and alert threshold; calendar visibility per item is controlled by the per-item switch or the entity options where applicable.

### UI labels (English)

| Concept | Config flow label |
|--------|-------------------|
| Mode | **Countdown type** — Days / Hours |
| Period | **Days until expiration** or **Hours until expiration** |
| Alert | **Alert threshold** (days before due in day mode, hours before due in hour mode) |

French equivalents are in `translations/fr.json` (e.g. *Type de compte à rebours*, *Jours avant expiration*, *Heures avant expiration*, *Seuil d'alerte*).

## Dashboard example

```yaml
type: entities
title: Expiration Tracker
entities:
  - entity: sensor.kitchen_sponge_days_remaining
  - entity: sensor.kitchen_sponge_percentage_elapsed
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

Pull requests are welcome. Please open an issue first to discuss major changes.

## License

MIT License — see [LICENSE](LICENSE) for details.
