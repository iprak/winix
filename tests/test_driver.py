"""Test WinixDevice component."""

from unittest.mock import patch

import pytest

from custom_components.winix.driver import WinixDriver


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
@pytest.mark.parametrize(
    ("method", "category", "value"),
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
async def test_turn_off(mock_rpc_attr, mock_driver, method, category, value):
    """Test various driver methods."""

    await getattr(mock_driver, method)()
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (
        WinixDriver.category_keys[category],
        WinixDriver.state_keys[category][value],
    )


@pytest.mark.parametrize(
    ("mock_driver_with_payload", "expected"),
    [
        ({"A02": "0"}, {"power": "off"}),
        ({"A02": "1"}, {"power": "on"}),
        ({"S08": "79"}, {"air_qvalue": 79}),  # air_qvalue
    ],
    indirect=["mock_driver_with_payload"],
)
async def test_get_state(mock_driver_with_payload, expected):
    """Test get_state."""

    # payload = {"A02": "0"}  # "A02" represents "power" and "0" means "off"

    state = await mock_driver_with_payload.get_state()
    assert state == expected
