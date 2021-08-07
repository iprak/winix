"""Test WinixDevice component."""
from unittest.mock import Mock, patch

import pytest

from custom_components.winix.WinixDriver import WinixDriver


def build_mock_device() -> WinixDriver:
    """Return a mocked WinixDeviceWrapper instance."""
    client = Mock()
    device_id = "device_1"
    return WinixDriver(device_id, client)


@patch("custom_components.winix.WinixDriver.WinixDriver._rpc_attr")
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
    """Test various driver methods."""
    device = build_mock_device()

    await getattr(device, method)()
    assert rpc_attr.call_count == 1
    assert rpc_attr.call_args[0] == (
        WinixDriver.category_keys[category],
        WinixDriver.state_keys[category][value],
    )
