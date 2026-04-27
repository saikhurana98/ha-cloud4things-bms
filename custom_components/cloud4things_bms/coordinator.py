from __future__ import annotations

import json
import logging
import re
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_ACCESS_TOKEN,
    CONF_INTENT,
    CONF_INTENT_ID,
    CONF_SKILL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

# strip units suffix like "808.5 kWh", "3.0 kW", "Rs. 5578.66"
_NUMERIC_RE = re.compile(r"^(?:Rs\.\s*)?([+-]?\d+(?:\.\d+)?)")


def _coerce_numeric(value: str) -> float | None:
    m = _NUMERIC_RE.match(value.strip())
    if m:
        return float(m.group(1))
    return None


def _extract_slots(slots: list) -> dict[str, Any]:
    """Convert C4T slots array [{name, value}] → {name: numeric_value}."""
    result: dict[str, Any] = {}
    for slot in slots:
        name = slot.get("name", "")
        raw = slot.get("value", "")
        if not name or raw is None:
            continue
        raw = str(raw).strip()
        # try direct numeric
        try:
            result[name] = float(raw)
            continue
        except ValueError:
            pass
        # try stripping unit suffix / currency prefix
        numeric = _coerce_numeric(raw)
        if numeric is not None:
            result[name] = numeric
        # try parsing nested JSON string (e.g. extra_data)
        elif raw.startswith("{"):
            try:
                nested = json.loads(raw)
                for k, v in nested.items():
                    if isinstance(v, (int, float)):
                        result[f"{name}_{k}"] = float(v)
                    elif isinstance(v, str):
                        n = _coerce_numeric(v)
                        if n is not None:
                            result[f"{name}_{k}"] = n
            except (json.JSONDecodeError, TypeError):
                pass
    return result


class C4TBMSCoordinator(DataUpdateCoordinator):
    """Poll Cloud4Things BMS API and expose flat sensor map."""

    def __init__(self, hass: HomeAssistant, config_entry) -> None:
        self._api_url = config_entry.data[CONF_API_URL]
        self._access_token = config_entry.data[CONF_ACCESS_TOKEN]
        self._intent = config_entry.data[CONF_INTENT]
        self._intent_id = config_entry.data[CONF_INTENT_ID]
        self._skill = config_entry.data[CONF_SKILL]
        interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=interval),
        )

    def _build_payload(self) -> dict:
        return {
            "context": {
                "access_token": self._access_token,
                "requestTime": 0,
            },
            "intent": {
                "intent": self._intent,
                "intent_id": self._intent_id,
                "skill": self._skill,
                "slots": [],
            },
        }

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._api_url,
                    json=self._build_payload(),
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    resp.raise_for_status()
                    raw = await resp.json(content_type=None)
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"HTTP {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        _LOGGER.debug("C4T BMS raw response: %s", raw)
        slots = raw.get("slots") if isinstance(raw, dict) else None
        if isinstance(slots, list):
            return _extract_slots(slots)
        # fallback: generic flatten for non-slots response shapes
        return {k: v for k, v in _generic_flatten(raw).items() if isinstance(v, (int, float))}


def _generic_flatten(data: Any, prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}_{k}" if prefix else k
            if isinstance(v, (dict, list)):
                result.update(_generic_flatten(v, key))
            elif isinstance(v, (int, float)):
                result[key] = v
            elif isinstance(v, str):
                try:
                    result[key] = float(v)
                except ValueError:
                    pass
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result.update(_generic_flatten(item, f"{prefix}_{i}" if prefix else str(i)))
    return result
