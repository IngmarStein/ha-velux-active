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

    entities: list[ButtonEntity] = []

    # Add a single home-level virtual departure button
    entities.append(VeluxActiveHomeDepartureButton(coordinator))
    
    # Add a virtual button for returning home
    entities.append(VeluxActiveHomeArriveButton(coordinator))

    async_add_entities(entities)


class VeluxActiveHomeDepartureButton(CoordinatorEntity[VeluxActiveCoordinator], ButtonEntity):
    """A virtual button for the home's departure action."""

    _attr_has_entity_name = True
    _attr_translation_key = "departure"
    _attr_icon = "mdi:home-export-outline"

    def __init__(self, coordinator: VeluxActiveCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.home_id}_home_departure"
        
        # Retrieve gateway metadata
        fw_ver = str(coordinator.data.get("firmware_revision_netatmo", ""))
        hw_ver = str(coordinator.data.get("hardware_version", ""))
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.home_id)},
            name="Velux ACTIVE System",
            manufacturer="Velux",
            model="KIX 300",
            sw_version=fw_ver if fw_ver else None,
            hw_version=hw_ver if hw_ver else None,
        )

    async def async_press(self) -> None:
        """Trigger the departure action."""
        await self.coordinator.api.async_set_persons_away(self.coordinator.home_id)


class VeluxActiveHomeArriveButton(CoordinatorEntity[VeluxActiveCoordinator], ButtonEntity):
    """A virtual button for the home's arrive/return action."""

    _attr_has_entity_name = True
    _attr_translation_key = "arrive_home"
    _attr_icon = "mdi:home-import-outline"

    def __init__(self, coordinator: VeluxActiveCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.home_id}_home_arrive"
        
        # Retrieve gateway metadata
        fw_ver = str(coordinator.data.get("firmware_revision_netatmo", ""))
        hw_ver = str(coordinator.data.get("hardware_version", ""))
        
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.home_id)},
            name="Velux ACTIVE System",
            manufacturer="Velux",
            model="KIX 300",
            sw_version=fw_ver if fw_ver else None,
            hw_version=hw_ver if hw_ver else None,
        )

    async def async_press(self) -> None:
        """Trigger the arrive home action."""
        await self.coordinator.api.async_set_persons_home(self.coordinator.home_id)
