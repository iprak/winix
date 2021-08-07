"""Test WinixDevice component."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.winix import WinixDevice
from custom_components.winix.const import (
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    AIRFLOW_SLEEP,
    ATTR_AIRFLOW,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    MODE_AUTO,
    MODE_MANUAL,
    OFF_VALUE,
    ON_VALUE,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
)


def build_mock_device() -> WinixDevice:
    """Returns a mock WinixDeviceWrapper."""
    client = Mock()
    device_id = "device_1"
    return WinixDevice(device_id, client)


@patch("custom_components.winix.WinixDevice._rpc_attr")
@pytest.mark.parametrize(
    "method, category, value",
    [
        ("turn_off", "power", "off"),
        ("turn_on", "power", "on"),
        ("auto", "mode", "auto"),
        ("manual", "mode", "manual"),
        ("plasmawave_off", "plasma", "off"),
        ("plasmawave_on", "plasma", "on"),
        ("low", "airflow", "low"),
        ("medium", "airflow", "medium"),
        ("high", "airflow", "high"),
        ("turbo", "airflow", "turbo"),
        ("sleep", "airflow", "sleep"),
    ],
)
async def test_turn_off(rpc_attr, method, category, value):
    """Test various methods."""
    device = build_mock_device()

    await getattr(device, method)()
    assert rpc_attr.call_count == 1
    assert rpc_attr.call_args[0] == (
        WinixDevice.category_keys[category],
        WinixDevice.state_keys[category][value],
    )
