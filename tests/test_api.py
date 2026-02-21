"""Tests for the Velux ACTIVE API client."""
from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.velux_active.api import (
    VeluxActiveApi,
    VeluxActiveAuthError,
    VeluxActiveConnectionError,
)
from tests.conftest import (
    MOCK_CLIENT_ID,
    MOCK_CLIENT_SECRET,
    MOCK_HOME_ID,
    MOCK_MODULE_ID,
    MOCK_BRIDGE_ID,
    MOCK_PASSWORD,
    MOCK_TOKEN_DATA,
    MOCK_USERNAME,
)


def _make_mock_response(status: int, json_data: dict) -> MagicMock:
    """Create a mock aiohttp response."""
    mock_resp = AsyncMock()
    mock_resp.status = status
    mock_resp.ok = status < 400
    mock_resp.json = AsyncMock(return_value=json_data)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)
    return mock_resp


def _make_api(session: MagicMock) -> VeluxActiveApi:
    return VeluxActiveApi(
        session, MOCK_USERNAME, MOCK_PASSWORD, MOCK_CLIENT_ID, MOCK_CLIENT_SECRET
    )


class TestAuthentication:
    """Tests for VeluxActiveApi authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        """Test successful authentication."""
        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(200, MOCK_TOKEN_DATA))
        api = _make_api(session)

        result = await api.async_authenticate()

        assert result["access_token"] == "mock_access_token"
        assert api.access_token == "mock_access_token"
        assert api.refresh_token == "mock_refresh_token"
        assert api.token_expires_at > time.time()

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self) -> None:
        """Test authentication with invalid credentials raises VeluxActiveAuthError."""
        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(401, {}))
        api = _make_api(session)

        with pytest.raises(VeluxActiveAuthError):
            await api.async_authenticate()

    @pytest.mark.asyncio
    async def test_authenticate_connection_error(self) -> None:
        """Test that connection errors are wrapped."""
        import aiohttp

        session = MagicMock()
        session.post = MagicMock(side_effect=aiohttp.ClientError("timeout"))
        api = _make_api(session)

        with pytest.raises(VeluxActiveConnectionError):
            await api.async_authenticate()

    @pytest.mark.asyncio
    async def test_refresh_token_success(self) -> None:
        """Test successful token refresh."""
        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(200, MOCK_TOKEN_DATA))
        api = _make_api(session)
        api.restore_tokens("old_token", "old_refresh", time.time() - 1)

        await api.async_refresh_token()

        assert api.access_token == "mock_access_token"

    @pytest.mark.asyncio
    async def test_refresh_token_expired_falls_back_to_password(self) -> None:
        """Test that a 401 on refresh falls back to password grant."""
        session = MagicMock()
        refresh_resp = _make_mock_response(401, {})
        auth_resp = _make_mock_response(200, MOCK_TOKEN_DATA)
        session.post = MagicMock(side_effect=[refresh_resp, auth_resp])
        api = _make_api(session)
        api.restore_tokens("old_token", "old_refresh", time.time() - 1)

        await api.async_refresh_token()

        assert api.access_token == "mock_access_token"

    def test_restore_tokens(self) -> None:
        """Test restoring tokens from stored data."""
        session = MagicMock()
        api = _make_api(session)
        expires_at = time.time() + 3600

        api.restore_tokens("access", "refresh", expires_at)

        assert api.access_token == "access"
        assert api.refresh_token == "refresh"
        assert api.token_expires_at == expires_at

    def test_token_valid_when_not_expired(self) -> None:
        """Test that token validity is checked correctly."""
        session = MagicMock()
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        assert api._is_token_valid() is True

    def test_token_invalid_when_expired(self) -> None:
        """Test that expired token is detected."""
        session = MagicMock()
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() - 1)

        assert api._is_token_valid() is False


class TestApiMethods:
    """Tests for VeluxActiveApi data fetching methods."""

    @pytest.mark.asyncio
    async def test_get_homes_data(self) -> None:
        """Test fetching homes data."""
        from tests.conftest import MOCK_HOMES_DATA

        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(200, MOCK_HOMES_DATA))
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        result = await api.async_get_homes_data()

        assert result["body"]["homes"][0]["id"] == MOCK_HOME_ID

    @pytest.mark.asyncio
    async def test_get_home_status(self) -> None:
        """Test fetching home status."""
        from tests.conftest import MOCK_HOME_STATUS

        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(200, MOCK_HOME_STATUS))
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        result = await api.async_get_home_status(MOCK_HOME_ID)

        modules = result["body"]["home"]["modules"]
        assert modules[0]["id"] == MOCK_MODULE_ID

    @pytest.mark.asyncio
    async def test_set_cover_position(self) -> None:
        """Test setting a cover position."""
        session = MagicMock()
        session.post = MagicMock(
            return_value=_make_mock_response(200, {"status": "ok"})
        )
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        await api.async_set_cover_position(MOCK_HOME_ID, MOCK_BRIDGE_ID, MOCK_MODULE_ID, 75)

        assert session.post.called

    @pytest.mark.asyncio
    async def test_stop_movements(self) -> None:
        """Test stopping all movements."""
        session = MagicMock()
        session.post = MagicMock(
            return_value=_make_mock_response(200, {"status": "ok"})
        )
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        await api.async_stop_movements(MOCK_HOME_ID, MOCK_BRIDGE_ID)

        assert session.post.called

    @pytest.mark.asyncio
    async def test_set_persons_away(self) -> None:
        """Test setting persons away."""
        session = MagicMock()
        session.post = MagicMock(
            return_value=_make_mock_response(200, {"status": "ok"})
        )
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        await api.async_set_persons_away(MOCK_HOME_ID)

        assert session.post.called

    @pytest.mark.asyncio
    async def test_set_persons_home(self) -> None:
        """Test setting persons home."""
        session = MagicMock()
        session.post = MagicMock(
            return_value=_make_mock_response(200, {"status": "ok"})
        )
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        await api.async_set_persons_home(MOCK_HOME_ID)

        assert session.post.called

    @pytest.mark.asyncio
    async def test_get_homes_data_auth_error(self) -> None:
        """Test that 403 raises VeluxActiveAuthError."""
        session = MagicMock()
        session.post = MagicMock(return_value=_make_mock_response(403, {}))
        api = _make_api(session)
        api.restore_tokens("token", "refresh", time.time() + 3600)

        with pytest.raises(VeluxActiveAuthError):
            await api.async_get_homes_data()
