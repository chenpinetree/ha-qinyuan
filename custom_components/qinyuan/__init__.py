"""The Qinyuan Water Purifier integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import QinyuanApiClient
from .const import CONF_APP_SECRET, CONF_AUTH_TOKEN, CONF_IOT_TOKEN, DOMAIN
from .coordinator import QinyuanDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Qinyuan from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    auth_token = entry.data[CONF_AUTH_TOKEN]
    iot_token = entry.data.get(CONF_IOT_TOKEN)
    app_secret = entry.data.get(CONF_APP_SECRET)

    api = QinyuanApiClient(
        auth_token=auth_token,
        iot_token=iot_token,
        app_secret=app_secret,
    )

    # Fetch device list to initialize coordinator
    devices = await api.async_get_device_list()
    if not devices:
        _LOGGER.error("Failed to find any Qinyuan devices on account")
        return False

    # Choose device matching entry or default to first online device
    device_info = devices[0]
    for dev in devices:
        if dev.get("productModel") == "KRL3913" or dev.get("status") == 1:
            device_info = dev
            break

    coordinator = QinyuanDataCoordinator(
        hass,
        api,
        device_id=device_info.get("deviceId", ""),
        iot_id=device_info.get("iotId", ""),
        product_key=device_info.get("productKey", ""),
        device_name=device_info.get("deviceNickName", "沁园净水机"),
        identity_id=device_info.get("identityId", ""),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: QinyuanDataCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

    return unload_ok
