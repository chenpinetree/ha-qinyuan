"""DataUpdateCoordinator for Qinyuan Water Purifier."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QinyuanApiClient
from .const import DEFAULT_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)


class QinyuanDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator to fetch data for all Qinyuan devices from Qinyuan Cloud."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: QinyuanApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Qinyuan Cloud Coordinator",
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch latest devices and their states."""
        try:
            devices = await self.api.async_get_device_list()
            devices_data: dict[str, dict[str, Any]] = {}

            for dev in devices:
                dev_id = dev.get("deviceId")
                if not dev_id:
                    continue

                iot_id = dev.get("iotId", "")
                pk = dev.get("productKey", "")
                name = dev.get("deviceNickName", "沁园净水机")
                model = dev.get("productModel", "KRL3913")

                # 1. Fetch filter life details
                filters = await self.api.async_get_filter_detail(iot_id, pk)
                filter_map = {item.get("id"): item for item in filters}

                # 2. Fetch device detail (status, errorStatus)
                detail = await self.api.async_get_device_detail(dev_id)
                status = detail.get("status", dev.get("status", 1))

                dev_data: dict[str, Any] = {
                    "device_id": dev_id,
                    "iot_id": iot_id,
                    "product_key": pk,
                    "device_name": name,
                    "product_model": model,
                    "status": status,
                    "error_status": detail.get("errorStatus", 0),
                    "filters": filter_map,
                }

                # 3. Fetch Aliyun real-time properties if configured
                aliyun_props = await self.api.async_get_aliyun_properties(iot_id)
                if aliyun_props:
                    dev_data["finished_tds"] = aliyun_props.get("FinishedWaterTDS", {}).get("value")
                    dev_data["raw_tds"] = aliyun_props.get("RawWaterTDS", {}).get("value")
                    dev_data["work_state"] = aliyun_props.get("WorkState", {}).get("value")
                    dev_data["pure_state"] = aliyun_props.get("PureState", {}).get("value")
                    dev_data["pure_water"] = aliyun_props.get("PureWater", {}).get("value")
                    dev_data["wifi_rssi"] = aliyun_props.get("WiFI_RSSI", {}).get("value")
                    dev_data["power_switch"] = aliyun_props.get("PowerSwitch", {}).get("value")
                    dev_data["washing_switch"] = aliyun_props.get("WashingSwitch", {}).get("value")
                else:
                    # Fallback to previously stored or default baseline
                    prev_dev = (self.data or {}).get(dev_id, {})
                    dev_data["finished_tds"] = prev_dev.get("finished_tds", 3)
                    dev_data["raw_tds"] = prev_dev.get("raw_tds", 30)
                    dev_data["work_state"] = prev_dev.get("work_state", 0)
                    dev_data["pure_state"] = prev_dev.get("pure_state", 0)
                    dev_data["pure_water"] = prev_dev.get("pure_water", 6438684)

                devices_data[dev_id] = dev_data

            return devices_data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Qinyuan API: {err}") from err
