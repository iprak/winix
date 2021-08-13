"""Tests for Winixdevice component."""

from unittest.mock import AsyncMock, MagicMock, Mock

import aiohttp
import pytest

from custom_components.winix.WinixDeviceWrapper import WinixDeviceWrapper
from custom_components.winix.WinixDriver import WinixDriver


@pytest.fixture
def mock_device_wrapper() -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""

    device_wrapper = MagicMock()
    device_wrapper.info.mac = "f190d35456d0"
    device_wrapper.info.alias = "Purifier1"

    device_wrapper.async_plasmawave_off = AsyncMock()
    device_wrapper.async_plasmawave_on = AsyncMock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_set_speed = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    yield device_wrapper


@pytest.fixture
def mock_driver() -> WinixDriver:
    """Return a mocked WinixDriver instance."""
    client = Mock()
    device_id = "device_1"
    yield WinixDriver(device_id, client)


@pytest.fixture
def mock_driver_with_payload(request) -> WinixDriver:
    """Return a mocked WinixDriver instance."""

    json_value = {"body": {"data": [{"attributes": request.param}]}}

    response = Mock()
    response.json = AsyncMock(return_value=json_value)

    client = Mock()  # aiohttp.ClientSession
    client.get = AsyncMock(return_value=response)

    device_id = "device_1"
    yield WinixDriver(device_id, client)
