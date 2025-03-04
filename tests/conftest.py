"""Tests for Winixdevice component."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from custom_components.winix.device_wrapper import MyWinixDeviceStub, WinixDeviceWrapper
from custom_components.winix.driver import WinixDriver

from .common import TEST_DEVICE_ID


@pytest.fixture
async def device_stub() -> any:
    """Build mocked device stub."""

    return MyWinixDeviceStub(
        id=TEST_DEVICE_ID,
        mac="mac",
        alias="deviceAlias",
        location_code="deviceLocCode",
        filter_replace_date="filterReplaceDate",
        model="modelName",
        sw_version="mcuVer",
    )


@pytest.fixture
async def device_data() -> any:
    """Get mocked device data."""

    filter_life_hours = "1257"
    air_qvalue = "74"
    aqi = "01"

    return {
        "statusCode": 200,
        "headers": {"resultCode": "S100", "resultMessage": ""},
        "body": {
            "deviceId": TEST_DEVICE_ID,
            "totalCnt": 1,
            "data": [
                {
                    "apiNo": "A210",
                    "apiGroup": "001",
                    "deviceGroup": "Air01",
                    "modelId": "C545",
                    "attributes": {
                        "A02": "0",
                        "A03": "01",
                        "A04": "01",
                        "A05": aqi,
                        "A07": "0",
                        "A21": filter_life_hours,
                        "S07": "01",
                        "S08": air_qvalue,
                        "S14": "121",
                    },
                    "rssi": "-55",
                    "creationTime": 1673449200634,
                    "utcDatetime": "2023-01-11 15:00:00",
                    "utcTimestamp": 1673449200,
                }
            ],
        },
    }


@pytest.fixture
def mock_device_wrapper() -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""

    device_wrapper = MagicMock()
    device_wrapper.device_stub.mac = "f190d35456d0"
    device_wrapper.device_stub.alias = "Purifier1"

    device_wrapper.async_plasmawave_off = AsyncMock()
    device_wrapper.async_plasmawave_on = AsyncMock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_set_speed = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    return device_wrapper


@pytest.fixture
def mock_driver() -> WinixDriver:
    """Return a mocked WinixDriver instance."""
    client = Mock()
    device_id = "device_1"
    return WinixDriver(device_id, client)


@pytest.fixture
def mock_driver_with_payload(request) -> WinixDriver:
    """Return a mocked WinixDriver instance."""

    json_value = {"body": {"data": [{"attributes": request.param}]}}

    response = Mock()
    response.json = AsyncMock(return_value=json_value)

    client = Mock()  # aiohttp.ClientSession
    client.get = AsyncMock(return_value=response)

    device_id = "device_1"
    return WinixDriver(device_id, client)
