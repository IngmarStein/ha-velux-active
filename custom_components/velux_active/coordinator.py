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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Velux ACTIVE API."""
        try:
            status = await self.api.async_get_home_status(self.home_id)
        except VeluxActiveAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except VeluxActiveConnectionError as err:
            raise UpdateFailed(err) from err

        home: dict[str, Any] = status.get("body", {}).get("home", {})
        return home
