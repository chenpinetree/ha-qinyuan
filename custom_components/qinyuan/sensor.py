"""Sensor platform for Qinyuan Water Purifier."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, WORK_STATE_MAP
from .coordinator import QinyuanDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Qinyuan sensors based on a config entry."""
    coordinator: QinyuanDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        QinyuanTdsSensor(coordinator, "finished_tds", "出水 TDS", "ppm", "mdi:water-check"),
        QinyuanTdsSensor(coordinator, "raw_tds", "原水 TDS", "ppm", "mdi:water-alert"),
        QinyuanFilterSensor(coordinator, "FilterStatus_1", "复合滤芯寿命", "mdi:filter"),
        QinyuanFilterSensor(coordinator, "FilterStatus_2", "RO膜滤芯寿命", "mdi:filter-outline"),
        QinyuanFilterSensor(coordinator, "FilterStatus_3", "炭棒滤芯寿命", "mdi:filter-variant"),
        QinyuanWorkStateSensor(coordinator),
        QinyuanPureWaterSensor(coordinator),
    ]

    async_add_entities(entities)


class QinyuanBaseEntity(CoordinatorEntity[QinyuanDataCoordinator]):
    """Base entity for Qinyuan devices."""

    def __init__(self, coordinator: QinyuanDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=coordinator.device_name,
            manufacturer="沁园 (Qinyuan)",
            model=coordinator.product_key,
            sw_version="1.0.0",
        )


class QinyuanTdsSensor(QinyuanBaseEntity, SensorEntity):
    """Sensor for TDS values."""

    def __init__(
        self,
        coordinator: QinyuanDataCoordinator,
        key: str,
        name: str,
        unit: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{coordinator.device_name} {name}"
        self._attr_unique_id = f"{coordinator.device_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get(self._key)


class QinyuanFilterSensor(QinyuanBaseEntity, SensorEntity):
    """Sensor for filter cartridge remaining life."""

    def __init__(
        self,
        coordinator: QinyuanDataCoordinator,
        filter_id: str,
        name: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator)
        self._filter_id = filter_id
        self._attr_name = f"{coordinator.device_name} {name}"
        self._attr_unique_id = f"{coordinator.device_id}_{filter_id}"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon

    @property
    def native_value(self) -> int | None:
        filters = self.coordinator.data.get("filters", {})
        filter_info = filters.get(self._filter_id, {})
        return filter_info.get("percent")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        filters = self.coordinator.data.get("filters", {})
        filter_info = filters.get(self._filter_id, {})
        return {
            "name": filter_info.get("name"),
            "status": filter_info.get("status"),
            "desc": filter_info.get("desc"),
        }


class QinyuanWorkStateSensor(QinyuanBaseEntity, SensorEntity):
    """Sensor for device running state."""

    def __init__(self, coordinator: QinyuanDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.device_name} 工作状态"
        self._attr_unique_id = f"{coordinator.device_id}_work_state"
        self._attr_icon = "mdi:water-pump"

    @property
    def native_value(self) -> str:
        state_code = self.coordinator.data.get("work_state", 0)
        return WORK_STATE_MAP.get(state_code, f"状态{state_code}")


class QinyuanPureWaterSensor(QinyuanBaseEntity, SensorEntity):
    """Sensor for pure water volume."""

    def __init__(self, coordinator: QinyuanDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.device_name} 累计制纯水量"
        self._attr_unique_id = f"{coordinator.device_id}_pure_water"
        self._attr_native_unit_of_measurement = UnitOfVolume.LITERS
        self._attr_device_class = SensorDeviceClass.WATER
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = "mdi:water"

    @property
    def native_value(self) -> float | None:
        raw_ml = self.coordinator.data.get("pure_water")
        if raw_ml is not None:
            return round(raw_ml / 1000.0, 1)
        return None
