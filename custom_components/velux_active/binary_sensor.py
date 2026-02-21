"""Binary sensor platform for Velux ACTIVE."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL_MAP
from .coordinator import VeluxActiveCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VeluxModuleBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description of a Velux module binary sensor."""

    module_key: str = ""


MODULE_BINARY_SENSOR_DESCRIPTIONS: tuple[VeluxModuleBinarySensorEntityDescription, ...] = (
    VeluxModuleBinarySensorEntityDescription(
        key="is_raining",
        module_key="is_raining",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velux ACTIVE binary sensor entities from a config entry."""
    coordinator: VeluxActiveCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    modules: list[dict[str, Any]] = coordinator.data.get("modules", [])
    for module in modules:
        for description in MODULE_BINARY_SENSOR_DESCRIPTIONS:
            if module.get(description.module_key) is not None:
                entities.append(VeluxActiveModuleBinarySensor(coordinator, module, description))

    async_add_entities(entities)


class VeluxActiveModuleBinarySensor(
    CoordinatorEntity[VeluxActiveCoordinator], BinarySensorEntity
):
    """A binary sensor for a Velux ACTIVE module (e.g. rain)."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: VeluxActiveCoordinator,
        module: dict[str, Any],
        description: VeluxModuleBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._module_id: str = module["id"]
        self.entity_description = description
        self._attr_unique_id = f"{self._module_id}_{description.key}"
        self._attr_translation_key = description.key
        
        device_id = self._module_id
        device_name = module.get("name", self._module_id)
        
        # Pass through gateway name if this is the bridge
        if module.get("type") == "NXG":
            device_name = module.get("name", "Velux ACTIVE System")
        
        fw_ver = str(module.get("firmware_revision", module.get("firmware_revision_netatmo", "")))
        hw_ver = str(module.get("hardware_version", ""))
        
        connections = None
        if ":" in self._module_id and module.get("type") == "NXG":
            connections = {(dr.CONNECTION_NETWORK_MAC, self._module_id)}
            
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=device_name,
            manufacturer="Velux",
            model=MODEL_MAP.get(module.get("type", "Unknown"), module.get("type", "Unknown")),
            sw_version=fw_ver if fw_ver else None,
            hw_version=hw_ver if hw_ver else None,
            connections=connections,
        )

    @property
    def _module(self) -> dict[str, Any]:
        """Return the current module status data."""
        for module in self.coordinator.data.get("modules", []):
            if module.get("id") == self._module_id:
                return module
        return {}

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        return self._module.get(self.entity_description.module_key)
