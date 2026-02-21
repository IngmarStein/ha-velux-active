"""Button platform for Velux ACTIVE."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODULE_TYPE_DEPARTURE_SWITCH
from .coordinator import VeluxActiveCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velux ACTIVE button entities from a config entry."""
    coordinator: VeluxActiveCoordinator = hass.data[DOMAIN][entry.entry_id]

    modules: list[dict[str, Any]] = coordinator.data.get("modules", [])
    entities: list[VeluxActiveDepartureButton] = []
    
    for module in modules:
        if module.get("type") == MODULE_TYPE_DEPARTURE_SWITCH:
            entities.append(VeluxActiveDepartureButton(coordinator, module))

    # Also add a single home-level virtual departure button regardless of physical switches
    entities.append(VeluxActiveHomeDepartureButton(coordinator))

    async_add_entities(entities)


class VeluxActiveDepartureButton(CoordinatorEntity[VeluxActiveCoordinator], ButtonEntity):
    """A button for a physical Velux ACTIVE departure switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "departure"
    _attr_icon = "mdi:home-export-outline"

    def __init__(
        self,
        coordinator: VeluxActiveCoordinator,
        module: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._module_id: str = module["id"]
        self._attr_unique_id = f"{self._module_id}_departure"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._module_id)},
            name=module.get("name", self._module_id),
            manufacturer="Velux",
            model="NXD",
        )

    async def async_press(self) -> None:
        """Trigger the departure action."""
        await self.coordinator.api.async_set_persons_away(self.coordinator.home_id)


class VeluxActiveHomeDepartureButton(CoordinatorEntity[VeluxActiveCoordinator], ButtonEntity):
    """A virtual button for the home's departure action."""

    _attr_has_entity_name = True
    _attr_translation_key = "departure"
    _attr_icon = "mdi:home-export-outline"

    def __init__(self, coordinator: VeluxActiveCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.home_id}_home_departure"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.home_id)},
            name="Velux ACTIVE System",
            manufacturer="Velux",
            model="KIX 300",
        )

    async def async_press(self) -> None:
        """Trigger the departure action."""
        await self.coordinator.api.async_set_persons_away(self.coordinator.home_id)
