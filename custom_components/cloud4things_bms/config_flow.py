from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_API_URL,
    CONF_ACCESS_TOKEN,
    CONF_INTENT,
    CONF_INTENT_ID,
    CONF_SKILL,
    CONF_SCAN_INTERVAL,
    DEFAULT_API_URL,
    DEFAULT_INTENT,
    DEFAULT_INTENT_ID,
    DEFAULT_SKILL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_TOKEN): str,
        vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): str,
        vol.Optional(CONF_INTENT, default=DEFAULT_INTENT): str,
        vol.Optional(CONF_INTENT_ID, default=DEFAULT_INTENT_ID): str,
        vol.Optional(CONF_SKILL, default=DEFAULT_SKILL): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=10, max=3600)
        ),
    }
)


async def _validate_connection(data: dict[str, Any]) -> None:
    payload = {
        "context": {
            "access_token": data[CONF_ACCESS_TOKEN],
            "requestTime": 0,
        },
        "intent": {
            "intent": data[CONF_INTENT],
            "intent_id": data[CONF_INTENT_ID],
            "skill": data[CONF_SKILL],
            "slots": [],
        },
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            data[CONF_API_URL],
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            if resp.status == 401:
                raise InvalidAuth
            resp.raise_for_status()
            body = await resp.json(content_type=None)
            if not body:
                raise CannotConnect


class Cloud4ThingsBMSConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _validate_connection(user_input)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during C4T BMS setup")
                errors["base"] = "unknown"
            else:
                # use skill + partial token as title for multi-instance support
                token_hint = user_input[CONF_ACCESS_TOKEN][:8]
                title = f"C4T BMS — {user_input[CONF_SKILL]} ({token_hint}…)"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    pass


class InvalidAuth(HomeAssistantError):
    pass
