# Cloud4Things BMS Energy Monitor

Home Assistant custom integration for [Cloud4Things](https://cloud4things.com) Building Management System (BMS) energy meters.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

## Features

- Polls any C4T BMS API endpoint
- Auto-discovers all numeric meter fields (energy, power, voltage, current, frequency, power factor)
- Assigns correct HA device classes and units automatically
- Fully configurable via UI — no YAML required
- Supports multiple instances (multiple buildings / tokens)

## Installation via HACS

1. Open HACS → Integrations
2. Click ⋮ → **Custom repositories**
3. Add `https://github.com/saikhurana98/ha-cloud4things-bms` — category **Integration**
4. Click **Download**
5. Restart Home Assistant

## Manual Installation

Copy `custom_components/cloud4things_bms/` into your HA config `custom_components/` directory and restart.

## Configuration

1. Settings → Integrations → **Add Integration** → search `Cloud4Things BMS`
2. Fill in:

| Field | Description | Default |
|-------|-------------|---------|
| Access Token | Your C4T API token | — |
| API URL | C4T API endpoint | `https://apiaarurobot.cloud4things.com/api/request` |
| Intent | BMS intent name | `BMS-METER-DASHBOARD-ANDROID` |
| Intent ID | Full intent ID | `BUILDING-MANAGEMENT-SYSTEM-BMS-METER-DASHBOARD-ANDROID` |
| Skill | C4T skill name | `BUILDING-MANAGEMENT-SYSTEM` |
| Poll Interval | Seconds between updates | `60` |

## Finding Your Access Token

Reverse-engineer your C4T mobile app traffic (e.g. via HTTP proxy) — look for POST requests to `/api/request`. The `context.access_token` field is your token.

## Sensor Auto-Classification

Keys containing these substrings get auto-assigned device class + unit:

| Keyword match | Device class | Unit |
|---------------|-------------|------|
| `kwh`, `energy`, `consumption` | energy | kWh |
| `kw`, `power`, `demand`, `load` | power | kW |
| `volt`, `voltage` | voltage | V |
| `amp`, `current` | current | A |
| `freq`, `hz` | frequency | Hz |
| `pf`, `power_factor` | power factor | — |

## Compatibility

Tested against C4T BMS Meter Dashboard API. Should work with any C4T skill that returns numeric JSON fields. Open an issue if your endpoint uses a different schema.

## License

MIT
