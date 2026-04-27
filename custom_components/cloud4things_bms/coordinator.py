from __future__ import annotations

import logging
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


def flatten_dict(data: Any, prefix: str = "", sep: str = "_") -> dict[str, Any]:
    """Recursively flatten nested dict/list into dot-key → scalar pairs."""
    result: dict[str, Any] = {}
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}{sep}{k}" if prefix else k
            if isinstance(v, (dict, list)):
                result.update(flatten_dict(v, new_key, sep))
            elif isinstance(v, (int, float)):
                result[new_key] = v
            elif isinstance(v, str):
                # keep strings that look numeric
                try:
                    result[new_key] = float(v)
                except ValueError:
                    result[new_key] = v
    elif isinstance(data, list):
        for i, item in enumerate(data):
            result.update(flatten_dict(item, f"{prefix}{sep}{i}" if prefix else str(i), sep))
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
        flat = flatten_dict(raw)
        # only keep numeric values for sensors
        return {k: v for k, v in flat.items() if isinstance(v, (int, float))}
