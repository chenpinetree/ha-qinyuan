"""Binary sensor platform for Qinyuan Water Purifier."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QinyuanDataCoordinator
from .sensor import QinyuanBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Qinyuan binary sensors based on a config entry."""
    coordinator: QinyuanDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        QinyuanConnectivitySensor(coordinator),
        QinyuanPurifyingSensor(coordinator),
    ]

    async_add_entities(entities)


class QinyuanConnectivitySensor(QinyuanBaseEntity, BinarySensorEntity):
    """Binary sensor for cloud connectivity."""

    def __init__(self, coordinator: QinyuanDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.device_name} 在线状态"
        self._attr_unique_id = f"{coordinator.device_id}_connectivity"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("status") == 1


class QinyuanPurifyingSensor(QinyuanBaseEntity, BinarySensorEntity):
    """Binary sensor for purifying state."""

    def __init__(self, coordinator: QinyuanDataCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.device_name} 制水状态"
        self._attr_unique_id = f"{coordinator.device_id}_purifying"
        self._attr_icon = "mdi:water-sync"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("pure_state") == 1
