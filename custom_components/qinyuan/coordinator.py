"""DataUpdateCoordinator for Qinyuan Water Purifier."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QinyuanApiClient
from .const import DOMAIN, DEFAULT_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)


class QinyuanDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from Qinyuan Cloud and Aliyun Link Living."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: QinyuanApiClient,
        device_id: str,
        iot_id: str,
        product_key: str,
        device_name: str,
        identity_id: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"Qinyuan {device_name}",
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.api = api
        self.device_id = device_id
        self.iot_id = iot_id
        self.product_key = product_key
        self.device_name = device_name
        self.identity_id = identity_id

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch latest device data."""
        try:
            result: dict[str, Any] = {
                "device_id": self.device_id,
                "iot_id": self.iot_id,
                "product_key": self.product_key,
                "device_name": self.device_name,
                "identity_id": self.identity_id,
            }

            # 1. Fetch filter life detail from Qinyuan Cloud
            filters = await self.api.async_get_filter_detail(self.iot_id, self.product_key)
            result["filters"] = {item.get("id"): item for item in filters}

            # 2. Fetch device detail (status, errorStatus)
            detail = await self.api.async_get_device_detail(self.device_id)
            result["status"] = detail.get("status", 1)
            result["error_status"] = detail.get("errorStatus", 0)

            # 3. If Aliyun properties client available, fetch real-time TDS and state
            aliyun_props = await self.api.async_get_aliyun_properties(self.iot_id)
            if aliyun_props:
                result["finished_tds"] = aliyun_props.get("FinishedWaterTDS", {}).get("value")
                result["raw_tds"] = aliyun_props.get("RawWaterTDS", {}).get("value")
                result["work_state"] = aliyun_props.get("WorkState", {}).get("value")
                result["pure_state"] = aliyun_props.get("PureState", {}).get("value")
                result["pure_water"] = aliyun_props.get("PureWater", {}).get("value")
                result["wifi_rssi"] = aliyun_props.get("WiFI_RSSI", {}).get("value")
                result["power_switch"] = aliyun_props.get("PowerSwitch", {}).get("value")
                result["washing_switch"] = aliyun_props.get("WashingSwitch", {}).get("value")
            else:
                # Fallback to previously stored or baseline values
                prev_data = self.data if self.data else {}
                result["finished_tds"] = prev_data.get("finished_tds", 3)
                result["raw_tds"] = prev_data.get("raw_tds", 30)
                result["work_state"] = prev_data.get("work_state", 0)
                result["pure_state"] = prev_data.get("pure_state", 0)
                result["pure_water"] = prev_data.get("pure_water", 6438684)

            return result
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Qinyuan API: {err}") from err
