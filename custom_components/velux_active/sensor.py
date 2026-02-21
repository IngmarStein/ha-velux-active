"""Sensor platform for Velux ACTIVE (room sensors: CO2, humidity, temperature, etc.)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
    LIGHT_LUX,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VeluxActiveCoordinator


@dataclass(frozen=True)
class VeluxRoomSensorEntityDescription(SensorEntityDescription):
    """Description of a Velux room sensor."""

    room_key: str = ""


ROOM_SENSOR_DESCRIPTIONS: tuple[VeluxRoomSensorEntityDescription, ...] = (
    VeluxRoomSensorEntityDescription(
        key="co2",
        room_key="co2",
        name="CO2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
    ),
    VeluxRoomSensorEntityDescription(
        key="humidity",
        room_key="humidity",
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    VeluxRoomSensorEntityDescription(
        key="temperature",
        room_key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    VeluxRoomSensorEntityDescription(
        key="lux",
        room_key="lux",
        name="Illuminance",
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=LIGHT_LUX,
    ),
    VeluxRoomSensorEntityDescription(
        key="air_quality",
        room_key="air_quality",
        name="Air Quality Index",
        device_class=None,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        icon="mdi:air-filter",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Velux ACTIVE sensor entities from a config entry."""
    coordinator: VeluxActiveCoordinator = hass.data[DOMAIN][entry.entry_id]

    rooms: list[dict[str, Any]] = coordinator.data.get("rooms", [])
    entities: list[VeluxActiveRoomSensor] = []
    for room in rooms:
        for description in ROOM_SENSOR_DESCRIPTIONS:
            if room.get(description.room_key) is not None:
                entities.append(VeluxActiveRoomSensor(coordinator, room, description))

    async_add_entities(entities)


class VeluxActiveRoomSensor(
    CoordinatorEntity[VeluxActiveCoordinator], SensorEntity
):
    """A sensor for a Velux ACTIVE room measurement."""

    _attr_has_entity_name = True
    entity_description: VeluxRoomSensorEntityDescription

    def __init__(
        self,
        coordinator: VeluxActiveCoordinator,
        room: dict[str, Any],
        description: VeluxRoomSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._room_id: str = room["id"]
        self.entity_description = description
        self._attr_unique_id = f"{self._room_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._room_id)},
            name=room.get("name", self._room_id),
            manufacturer="Velux",
            model="NXS",
        )

    @property
    def _room(self) -> dict[str, Any]:
        """Return the current room status data."""
        for room in self.coordinator.data.get("rooms", []):
            if room.get("id") == self._room_id:
                return room
        return {}

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self._room.get(self.entity_description.room_key)
