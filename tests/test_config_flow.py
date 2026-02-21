"""Tests for the Velux ACTIVE config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.velux_active.const import DOMAIN
from tests.conftest import (
    MOCK_HOME_ID,
    MOCK_HOME_NAME,
    MOCK_HOMES_DATA,
    MOCK_PASSWORD,
    MOCK_USERNAME,
)


@pytest.fixture
def mock_validate_credentials():
    """Patch the credentials validation."""
    with patch(
        "custom_components.velux_active.config_flow.VeluxActiveConfigFlow._async_validate_credentials",
        new_callable=AsyncMock,
        return_value=MOCK_HOMES_DATA["body"]["homes"],
    ) as mock:
        yield mock


class TestConfigFlow:
    """Tests for VeluxActiveConfigFlow."""

    def test_step_user_data_schema_has_required_fields(self) -> None:
        """Test that the user step schema includes username and password."""
        from custom_components.velux_active.config_flow import STEP_USER_DATA_SCHEMA
        import voluptuous as vol

        schema_keys = {str(k): k for k in STEP_USER_DATA_SCHEMA.schema}
        assert "username" in schema_keys
        assert "password" in schema_keys

    @pytest.mark.asyncio
    async def test_config_flow_creates_entry_for_single_home(
        self, mock_validate_credentials
    ) -> None:
        """Test that a single-home account creates a config entry directly."""
        from custom_components.velux_active.config_flow import VeluxActiveConfigFlow

        flow = VeluxActiveConfigFlow()
        flow.hass = MagicMock()
        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()
        flow.async_create_entry = MagicMock(
            return_value={"type": "create_entry", "title": MOCK_HOME_NAME}
        )

        result = await flow.async_step_user(
            {"username": MOCK_USERNAME, "password": MOCK_PASSWORD}
        )

        assert flow.async_create_entry.called
        call_kwargs = flow.async_create_entry.call_args
        assert call_kwargs[1]["title"] == MOCK_HOME_NAME
        assert call_kwargs[1]["data"]["home_id"] == MOCK_HOME_ID

    @pytest.mark.asyncio
    async def test_config_flow_shows_form_initially(self) -> None:
        """Test that the flow shows a form when no input is provided."""
        from custom_components.velux_active.config_flow import VeluxActiveConfigFlow

        flow = VeluxActiveConfigFlow()
        flow.hass = MagicMock()
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "user"})

        result = await flow.async_step_user(None)

        assert flow.async_show_form.called
        assert flow.async_show_form.call_args[1]["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_config_flow_invalid_auth(self) -> None:
        """Test that invalid credentials show an error."""
        from custom_components.velux_active.api import VeluxActiveAuthError
        from custom_components.velux_active.config_flow import VeluxActiveConfigFlow

        flow = VeluxActiveConfigFlow()
        flow.hass = MagicMock()
        flow._async_validate_credentials = AsyncMock(
            side_effect=VeluxActiveAuthError("bad creds")
        )
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        await flow.async_step_user(
            {"username": MOCK_USERNAME, "password": "wrongpass"}
        )

        errors = flow.async_show_form.call_args[1]["errors"]
        assert errors["base"] == "invalid_auth"

    @pytest.mark.asyncio
    async def test_config_flow_cannot_connect(self) -> None:
        """Test that connection errors show an error."""
        from custom_components.velux_active.api import VeluxActiveConnectionError
        from custom_components.velux_active.config_flow import VeluxActiveConfigFlow

        flow = VeluxActiveConfigFlow()
        flow.hass = MagicMock()
        flow._async_validate_credentials = AsyncMock(
            side_effect=VeluxActiveConnectionError("timeout")
        )
        flow.async_show_form = MagicMock(return_value={"type": "form"})

        await flow.async_step_user(
            {"username": MOCK_USERNAME, "password": MOCK_PASSWORD}
        )

        errors = flow.async_show_form.call_args[1]["errors"]
        assert errors["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_config_flow_multiple_homes_shows_selection(self) -> None:
        """Test that multiple homes triggers the home selection step."""
        from custom_components.velux_active.config_flow import VeluxActiveConfigFlow

        multi_home_data = [
            {"id": "home1", "name": "Home 1"},
            {"id": "home2", "name": "Home 2"},
        ]

        flow = VeluxActiveConfigFlow()
        flow.hass = MagicMock()
        flow._async_validate_credentials = AsyncMock(return_value=multi_home_data)
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "select_home"})

        result = await flow.async_step_user(
            {"username": MOCK_USERNAME, "password": MOCK_PASSWORD}
        )

        assert flow.async_show_form.called
        assert flow.async_show_form.call_args[1]["step_id"] == "select_home"


class TestOptionsFlow:
    """Tests for VeluxActiveOptionsFlow."""

    @pytest.mark.asyncio
    async def test_options_flow_shows_form(self) -> None:
        """Test that the options flow shows the update_interval field."""
        from custom_components.velux_active.config_flow import VeluxActiveOptionsFlow

        entry = MagicMock()
        entry.options = {}
        flow = VeluxActiveOptionsFlow(entry)
        flow.async_show_form = MagicMock(return_value={"type": "form"})
        flow.async_create_entry = MagicMock()

        await flow.async_step_init(None)

        assert flow.async_show_form.called

    @pytest.mark.asyncio
    async def test_options_flow_saves_update_interval(self) -> None:
        """Test that options are saved correctly."""
        from custom_components.velux_active.config_flow import VeluxActiveOptionsFlow

        entry = MagicMock()
        entry.options = {}
        flow = VeluxActiveOptionsFlow(entry)
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        await flow.async_step_init({"update_interval": 120})

        assert flow.async_create_entry.called
        assert flow.async_create_entry.call_args[1]["data"] == {"update_interval": 120}
