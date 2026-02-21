"""DataUpdateCoordinator for the Velux ACTIVE integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VeluxActiveApi, VeluxActiveAuthError, VeluxActiveConnectionError
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class VeluxActiveCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages fetching data from the Velux ACTIVE cloud."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        api: VeluxActiveApi,
        home_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.api = api
        self.home_id = home_id
        self._module_names: dict[str, str] = {}
        self._room_names: dict[str, str] = {}
        self._names_fetched = False

    async def _async_fetch_names(self) -> None:
        """Fetch human-readable names from homesdata."""
        if self._names_fetched:
            return

        try:
            data = await self.api.async_get_homes_data()
        except (VeluxActiveAuthError, VeluxActiveConnectionError) as err:
            _LOGGER.warning("Failed to fetch homes data for names: %s", err)
            return

        homes = data.get("body", {}).get("homes", [])
        for home in homes:
            if home.get("id") == self.home_id:
                for module in home.get("modules", []):
                    if "id" in module and "name" in module:
                        self._module_names[module["id"]] = module["name"]
                for room in home.get("rooms", []):
                    if "id" in room and "name" in room:
                        self._room_names[room["id"]] = room["name"]
        
        self._names_fetched = True

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Velux ACTIVE API."""
        if not self._names_fetched:
            await self._async_fetch_names()

        try:
            status = await self.api.async_get_home_status(self.home_id)
        except VeluxActiveAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except VeluxActiveConnectionError as err:
            raise UpdateFailed(err) from err

        home: dict[str, Any] = status.get("body", {}).get("home", {})

        # Inject human-readable names
        for module in home.get("modules", []):
            if module.get("id") in self._module_names:
                module["name"] = self._module_names[module["id"]]
                
        for room in home.get("rooms", []):
            if room.get("id") in self._room_names:
                room["name"] = self._room_names[room["id"]]

        return home
