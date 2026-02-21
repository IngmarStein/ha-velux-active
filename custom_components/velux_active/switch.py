"""Switch platform for Velux ACTIVE."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODULE_TYPE_ROLLER_SHUTTER, MODEL_MAP
from .coordinator import VeluxActiveCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velux ACTIVE switch entities from a config entry."""
    coordinator: VeluxActiveCoordinator = hass.data[DOMAIN][entry.entry_id]

    modules: list[dict[str, Any]] = coordinator.data.get("modules", [])
    entities: list[SwitchEntity] = []
    
    for module in modules:
        # Check if the module supports silent mode (it's present in the payload)
        if module.get("type") == MODULE_TYPE_ROLLER_SHUTTER and "silent" in module:
            entities.append(VeluxActiveSilentSwitch(coordinator, module))

    async_add_entities(entities)


class VeluxActiveSilentSwitch(CoordinatorEntity[VeluxActiveCoordinator], SwitchEntity):
    """A switch to toggle silent mode for a Velux ACTIVE cover."""

    _attr_has_entity_name = True
    _attr_translation_key = "silent_mode"
    _attr_icon = "mdi:volume-variant-off"

    def __init__(
        self,
        coordinator: VeluxActiveCoordinator,
        module: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._module_id: str = module["id"]
        self._bridge_id: str = module.get("bridge", "")
        self._attr_unique_id = f"{self._module_id}_silent"
        
        velux_type: str = module.get("velux_type", "shutter")
        device_name = module.get("name")
        if not device_name or device_name == self._module_id:
            room_id = module.get("room_id")
            room_name = coordinator.room_names.get(room_id) if room_id else None
            type_name = velux_type.replace("_", " ").capitalize()
            if room_name:
                device_name = f"{room_name} {type_name}"
            else:
                device_name = f"{type_name} {self._module_id}"

        fw_ver = str(module.get("firmware_revision", ""))
        hw_ver = str(module.get("hardware_version", ""))
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._module_id)},
            name=device_name,
            manufacturer=module.get("manufacturer", "Velux"),
            model=MODEL_MAP.get(velux_type, velux_type),
            via_device=(DOMAIN, self._bridge_id) if self._bridge_id else None,
            sw_version=fw_ver if fw_ver else None,
            hw_version=hw_ver if hw_ver else None,
            connections=set(),
        )
        self._attr_is_on = module.get("silent", False)

    @property
    def _module(self) -> dict[str, Any]:
        """Return the current module status data."""
        for mod in self.coordinator.data.get("modules", []):
            if mod.get("id") == self._module_id:
                return mod
        return {}

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update cached state from the coordinator and write to HA."""
        mod = self._module
        self._attr_is_on = mod.get("silent", False)
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.api.async_set_silent_mode(
            self.coordinator.home_id, self._bridge_id, self._module_id, True
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.api.async_set_silent_mode(
            self.coordinator.home_id, self._bridge_id, self._module_id, False
        )
        self._attr_is_on = False
        self.async_write_ha_state()
