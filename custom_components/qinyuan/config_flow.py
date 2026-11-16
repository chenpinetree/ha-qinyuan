"""Config flow for Qinyuan Water Purifier integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .api import QinyuanApiClient
from .const import CONF_APP_SECRET, CONF_AUTH_TOKEN, CONF_IOT_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class QinyuanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Qinyuan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_token = user_input[CONF_AUTH_TOKEN].strip()
            iot_token = user_input.get(CONF_IOT_TOKEN, "").strip() or None
            app_secret = user_input.get(CONF_APP_SECRET, "").strip() or None

            api = QinyuanApiClient(auth_token, iot_token, app_secret)
            devices = await api.async_get_device_list()
            await api.close()

            if not devices:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id("qinyuan_account")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="沁园净水机",
                    data={
                        CONF_AUTH_TOKEN: auth_token,
                        CONF_IOT_TOKEN: iot_token,
                        CONF_APP_SECRET: app_secret,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_AUTH_TOKEN): str,
                vol.Optional(CONF_IOT_TOKEN, default=""): str,
                vol.Optional(CONF_APP_SECRET, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
