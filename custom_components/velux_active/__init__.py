"""The Velux ACTIVE integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import VeluxActiveApi, VeluxActiveAuthError, VeluxActiveConnectionError
from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    DOMAIN,
)
from .coordinator import VeluxActiveCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER, Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Velux ACTIVE from a config entry."""
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]
    client_id: str = entry.data.get(CONF_CLIENT_ID, DEFAULT_CLIENT_ID)
    client_secret: str = entry.data.get(CONF_CLIENT_SECRET, DEFAULT_CLIENT_SECRET)

    session = async_get_clientsession(hass)
    api = VeluxActiveApi(session, username, password, client_id, client_secret)

    # Restore cached tokens if available
    if token_data := entry.data.get("token_data"):
        api.restore_tokens(
            token_data["access_token"],
            token_data["refresh_token"],
            token_data["token_expires_at"],
        )

    home_id: str = entry.data["home_id"]
    coordinator = VeluxActiveCoordinator(hass, api, home_id)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
