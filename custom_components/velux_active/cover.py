"""Cover platform for Velux ACTIVE (NXO roller shutters and windows)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODULE_TYPE_BRIDGE, MODULE_TYPE_ROLLER_SHUTTER
from .coordinator import VeluxActiveCoordinator

_LOGGER = logging.getLogger(__name__)

VELUX_TYPE_TO_DEVICE_CLASS = {
    "window": CoverDeviceClass.WINDOW,
    "shutter": CoverDeviceClass.SHUTTER,
    "blind": CoverDeviceClass.BLIND,
    "awning": CoverDeviceClass.AWNING,
    "curtain": CoverDeviceClass.CURTAIN,
    "shade": CoverDeviceClass.SHADE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velux ACTIVE cover entities from a config entry."""
    coordinator: VeluxActiveCoordinator = hass.data[DOMAIN][entry.entry_id]

    modules: list[dict[str, Any]] = coordinator.data.get("modules", [])
    entities = [
        VeluxActiveCover(coordinator, module)
        for module in modules
        if module.get("type") == MODULE_TYPE_ROLLER_SHUTTER
    ]
    async_add_entities(entities)


class VeluxActiveCover(CoordinatorEntity[VeluxActiveCoordinator], CoverEntity):
    """Representation of a Velux ACTIVE cover (roller shutter / window)."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(
        self,
        coordinator: VeluxActiveCoordinator,
        module: dict[str, Any],
    ) -> None:
        """Initialize the cover entity."""
        super().__init__(coordinator)
        self._module_id: str = module["id"]
        self._bridge_id: str = module.get("bridge", "")
        self._attr_unique_id = self._module_id
        velux_type: str = module.get("velux_type", "shutter")
        self._attr_device_class = VELUX_TYPE_TO_DEVICE_CLASS.get(
            velux_type, CoverDeviceClass.SHUTTER
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._module_id)},
            name=module.get("name", self._module_id),
            manufacturer=module.get("manufacturer", "Velux"),
            model=module.get("velux_type", MODULE_TYPE_ROLLER_SHUTTER),
            via_device=(DOMAIN, self._bridge_id) if self._bridge_id else None,
        )

    @property
    def _module(self) -> dict[str, Any]:
        """Return the current module status data."""
        for mod in self.coordinator.data.get("modules", []):
            if mod.get("id") == self._module_id:
                return mod
        return {}

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the cover (0=closed, 100=open)."""
        pos = self._module.get("current_position")
        return pos if pos is not None else None

    @property
    def is_closed(self) -> bool | None:
        """Return True if the cover is fully closed."""
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    @property
    def is_opening(self) -> bool:
        """Return True if the cover is opening."""
        mod = self._module
        cur = mod.get("current_position")
        tgt = mod.get("target_position")
        if cur is None or tgt is None:
            return False
        return tgt > cur

    @property
    def is_closing(self) -> bool:
        """Return True if the cover is closing."""
        mod = self._module
        cur = mod.get("current_position")
        tgt = mod.get("target_position")
        if cur is None or tgt is None:
            return False
        return tgt < cur

    @property
    def available(self) -> bool:
        """Return True if the module is reachable."""
        return self.coordinator.last_update_success and self._module.get(
            "reachable", True
        )

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover fully (100%)."""
        await self.coordinator.api.async_set_cover_position(
            self.coordinator.home_id, self._bridge_id, self._module_id, 100
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover fully (0%)."""
        await self.coordinator.api.async_set_cover_position(
            self.coordinator.home_id, self._bridge_id, self._module_id, 0
        )
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Set the cover to a specific position."""
        position: int = kwargs[ATTR_POSITION]
        await self.coordinator.api.async_set_cover_position(
            self.coordinator.home_id, self._bridge_id, self._module_id, position
        )
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop any cover movement."""
        await self.coordinator.api.async_stop_movements(
            self.coordinator.home_id, self._bridge_id
        )
        await self.coordinator.async_request_refresh()
