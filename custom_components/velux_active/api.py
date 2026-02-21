"""Velux ACTIVE API client."""
from __future__ import annotations

import time
from typing import Any

import aiohttp

from .const import (
    AUTH_URL,
    HOME_STATUS_URL,
    HOMES_DATA_URL,
    SET_STATE_URL,
    SET_PERSONS_AWAY_URL,
    SET_PERSONS_HOME_URL,
)


class VeluxActiveAuthError(Exception):
    """Authentication error."""


class VeluxActiveConnectionError(Exception):
    """Connection error."""


class VeluxActiveApi:
    """Velux ACTIVE API client using OAuth2 password grant."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0

    @property
    def access_token(self) -> str | None:
        """Return the current access token."""
        return self._access_token

    @property
    def refresh_token(self) -> str | None:
        """Return the current refresh token."""
        return self._refresh_token

    @property
    def token_expires_at(self) -> float:
        """Return the token expiry timestamp."""
        return self._token_expires_at

    def restore_tokens(
        self,
        access_token: str,
        refresh_token: str,
        token_expires_at: float,
    ) -> None:
        """Restore tokens from stored data."""
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_expires_at = token_expires_at

    def _is_token_valid(self) -> bool:
        """Return True if the access token is still valid."""
        return (
            self._access_token is not None
            and time.time() < self._token_expires_at - 30
        )

    async def async_authenticate(self) -> dict[str, Any]:
        """Authenticate with username/password and return token data."""
        try:
            async with self._session.post(
                AUTH_URL,
                data={
                    "grant_type": "password",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "username": self._username,
                    "password": self._password,
                    "user_prefix": "velux",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                if resp.status == 401:
                    raise VeluxActiveAuthError("Invalid credentials")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Authentication failed with status {resp.status}"
                    )
                data: dict[str, Any] = await resp.json()
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 10800)
        return data

    async def async_refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if self._refresh_token is None:
            await self.async_authenticate()
            return
        try:
            async with self._session.post(
                AUTH_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                if resp.status in (400, 401):
                    # Refresh token expired – fall back to password grant
                    await self.async_authenticate()
                    return
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Token refresh failed with status {resp.status}"
                    )
                data: dict[str, Any] = await resp.json()
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 10800)

    async def _ensure_token(self) -> None:
        """Ensure we have a valid access token."""
        if not self._is_token_valid():
            await self.async_refresh_token()

    async def async_get_homes_data(self) -> dict[str, Any]:
        """Fetch homes and modules data."""
        await self._ensure_token()
        try:
            async with self._session.post(
                HOMES_DATA_URL,
                data={"access_token": self._access_token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as resp:
                if resp.status == 403:
                    raise VeluxActiveAuthError("Access denied")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Failed to get homes data: {resp.status}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

    async def async_get_home_status(self, home_id: str) -> dict[str, Any]:
        """Fetch the current status of a home."""
        await self._ensure_token()
        try:
            async with self._session.post(
                HOME_STATUS_URL,
                json={"home_id": home_id},
                headers={"Authorization": f"Bearer {self._access_token}"},
            ) as resp:
                if resp.status == 403:
                    raise VeluxActiveAuthError("Access denied")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Failed to get home status: {resp.status}"
                    )
                return await resp.json()
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

    async def async_set_cover_position(
        self, home_id: str, bridge_id: str, module_id: str, position: int
    ) -> None:
        """Set the target position of a cover module (0–100)."""
        await self._ensure_token()
        payload = {
            "home": {
                "id": home_id,
                "modules": [
                    {
                        "bridge": bridge_id,
                        "id": module_id,
                        "target_position": position,
                    }
                ],
            }
        }
        try:
            async with self._session.post(
                SET_STATE_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {self._access_token}",
                },
            ) as resp:
                if resp.status == 403:
                    raise VeluxActiveAuthError("Access denied")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Failed to set cover position: {resp.status}"
                    )
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

    async def async_set_silent_mode(
        self, home_id: str, bridge_id: str, module_id: str, silent: bool
    ) -> None:
        """Set the silent mode of a module."""
        await self._ensure_token()
        payload = {
            "home": {
                "id": home_id,
                "modules": [
                    {
                        "bridge": bridge_id,
                        "id": module_id,
                        "silent": silent,
                    }
                ],
            }
        }
        try:
            async with self._session.post(
                SET_STATE_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {self._access_token}",
                },
            ) as resp:
                if resp.status == 403:
                    raise VeluxActiveAuthError("Access denied")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Failed to set silent mode: {resp.status}"
                    )
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err

    async def async_stop_movements(self, home_id: str, bridge_id: str) -> None:
        """Stop all movements on the given bridge."""
        await self._ensure_token()
        payload = {
            "home": {
                "id": home_id,
                "modules": [
                    {
                        "id": bridge_id,
                        "stop_movements": "all",
                    }
                ],
            }
        }
        try:
            async with self._session.post(
                SET_STATE_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Bearer {self._access_token}",
                },
            ) as resp:
                if resp.status == 403:
                    raise VeluxActiveAuthError("Access denied")
                if not resp.ok:
                    raise VeluxActiveConnectionError(
                        f"Failed to stop movements: {resp.status}"
                    )
        except aiohttp.ClientError as err:
            raise VeluxActiveConnectionError(
                f"Cannot connect to Velux ACTIVE: {err}"
            ) from err
