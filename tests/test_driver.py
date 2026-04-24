"""Test WinixDriver component."""

from unittest.mock import patch

import pytest

from custom_components.winix.driver import AirPurifierDriver, DehumidifierDriver


# ---------------------------------------------------------------------------
# AirPurifierDriver tests
# ---------------------------------------------------------------------------


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
async def test_turn_off(mock_rpc_attr, mock_airpurifier_driver, method, category, value) -> None:
    """Test various driver methods."""

    await getattr(mock_airpurifier_driver, method)()
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (
        AirPurifierDriver.category_keys[category],
        AirPurifierDriver.state_keys[category][value],
    )


@pytest.mark.parametrize(
    ("mock_airpurifier_driver_with_payload", "expected"),
    [
        ({"A02": "0"}, {"power": "off"}),
        ({"A02": "1"}, {"power": "on"}),
        ({"S08": "79"}, {"air_qvalue": 79}),  # air_qvalue
        ({"S04": "12"}, {"pm2_5": 12}),  # pm2_5
    ],
    indirect=["mock_airpurifier_driver_with_payload"],
)
async def test_get_state(mock_airpurifier_driver_with_payload, expected) -> None:
    """Test get_state for AirPurifierDriver."""

    # payload = {"A02": "0"}  # "A02" represents "power" and "0" means "off"

    state = await mock_airpurifier_driver_with_payload.get_state()
    assert state == expected


# ---------------------------------------------------------------------------
# DehumidifierDriver tests
# ---------------------------------------------------------------------------


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
@pytest.mark.parametrize(
    ("method", "args", "category", "value"),
    [
        ("turn_on", [], "power", "on"),
        ("turn_off", [], "power", "off"),
        ("set_mode", ["auto"], "mode", "auto"),
        ("set_mode", ["manual"], "mode", "manual"),
        ("set_mode", ["clothes"], "mode", "clothes"),
        ("set_mode", ["shoes"], "mode", "shoes"),
        ("set_mode", ["quiet"], "mode", "quiet"),
        ("set_mode", ["continuous"], "mode", "continuous"),
        ("set_fan_speed", ["high"], "airflow", "high"),
        ("set_fan_speed", ["low"], "airflow", "low"),
        ("set_fan_speed", ["turbo"], "airflow", "turbo"),
        ("child_lock_on", [], "child_lock", "on"),
        ("child_lock_off", [], "child_lock", "off"),
        ("uv_sanitize_on", [], "uv_sanitize", "on"),
        ("uv_sanitize_off", [], "uv_sanitize", "off"),
    ],
)
async def test_dehumidifier_control(
    mock_rpc_attr, mock_dehumidifier_driver, method, args, category, value
) -> None:
    """Test DehumidifierDriver control methods."""

    await getattr(mock_dehumidifier_driver, method)(*args)
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (
        DehumidifierDriver.category_keys[category],
        DehumidifierDriver.state_keys[category][value],
    )


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
@pytest.mark.parametrize(
    ("method", "args", "expected_attr", "expected_value"),
    [
        ("set_humidity", [50], "D05", "50"),
        ("set_humidity", [35], "D05", "35"),
        ("set_timer", [3], "D15", "3"),
        ("set_timer", [0], "D15", "0"),
    ],
)
async def test_dehumidifier_rpc(
    mock_rpc_attr, mock_dehumidifier_driver, method, args, expected_attr, expected_value
) -> None:
    """Test DehumidifierDriver direct RPC methods."""

    await getattr(mock_dehumidifier_driver, method)(*args)
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (expected_attr, expected_value)


@pytest.mark.parametrize(
    ("mock_dehumidifier_driver_with_payload", "expected"),
    [
        ({"D02": "0"}, {"power": "off"}),
        ({"D02": "1"}, {"power": "on"}),
        ({"D02": "2"}, {"power": "auto-dry"}),
        ({"D03": "01"}, {"mode": "auto"}),
        ({"D03": "02"}, {"mode": "manual"}),
        ({"D04": "01"}, {"airflow": "high"}),
        ({"D10": "55"}, {"current_humidity": 55}),
        ({"D05": "50"}, {"target_humidity": 50}),
        ({"D15": "3"}, {"timer": 3}),
        ({"D11": "1"}, {"water_tank": "on"}),
    ],
    indirect=["mock_dehumidifier_driver_with_payload"],
)
async def test_dehumidifier_get_state(mock_dehumidifier_driver_with_payload, expected) -> None:
    """Test get_state for DehumidifierDriver."""

    state = await mock_dehumidifier_driver_with_payload.get_state()
    assert state == expected
