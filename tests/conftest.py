"""Test fixtures for Velux ACTIVE integration tests."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.velux_active.api import VeluxActiveApi

MOCK_USERNAME = "test@example.com"
MOCK_PASSWORD = "testpassword"
MOCK_CLIENT_ID = "testclientid"
MOCK_CLIENT_SECRET = "testclientsecret"
MOCK_HOME_ID = "home123"
MOCK_HOME_NAME = "My Home"
MOCK_MODULE_ID = "module456"
MOCK_BRIDGE_ID = "bridge789"

MOCK_TOKEN_DATA: dict[str, Any] = {
    "access_token": "mock_access_token",
    "refresh_token": "mock_refresh_token",
    "expires_in": 10800,
    "scope": ["all_scopes"],
}

MOCK_HOMES_DATA: dict[str, Any] = {
    "body": {
        "homes": [
            {
                "id": MOCK_HOME_ID,
                "name": MOCK_HOME_NAME,
            }
        ]
    },
    "status": "ok",
}

MOCK_HOME_STATUS: dict[str, Any] = {
    "body": {
        "home": {
            "id": MOCK_HOME_ID,
            "modules": [
                {
                    "id": MOCK_MODULE_ID,
                    "bridge": MOCK_BRIDGE_ID,
                    "type": "NXO",
                    "velux_type": "shutter",
                    "name": "Living Room Shutter",
                    "manufacturer": "Velux",
                    "current_position": 50,
                    "target_position": 50,
                    "reachable": True,
                }
            ],
            "rooms": [
                {
                    "id": "room001",
                    "name": "Living Room",
                    "co2": 650,
                    "humidity": 45,
                    "temperature": 21,
                    "lux": 300,
                    "air_quality": 2,
                }
            ],
        }
    },
    "status": "ok",
}
