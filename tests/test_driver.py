"""Test WinixDriver component."""

from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from custom_components.winix.const import ATTR_POWER, OFF_VALUE
from custom_components.winix.driver import (
    AirConditionerDriver,
    AirPurifierDriver,
    DehumidifierDriver,
)
from homeassistant.exceptions import HomeAssistantError

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
        ("super", "airflow", "super"),
    ],
)
async def test_turn_off(
    mock_rpc_attr, mock_airpurifier_driver, method, category, value
) -> None:
    """Test various driver methods."""

    await getattr(mock_airpurifier_driver, method)()
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (
        AirPurifierDriver.category_keys[category],
        AirPurifierDriver.state_keys[category][value],
    )


async def test_control_success(mock_airpurifier_driver) -> None:
    """Test _rpc_attr sends the correct request and reads the response."""

    response = Mock()
    response.raise_for_status = Mock()
    response.text = AsyncMock(return_value="OK")

    mock_airpurifier_driver._client.get = AsyncMock(return_value=response)  # noqa: SLF001

    await mock_airpurifier_driver.control(ATTR_POWER, OFF_VALUE)

    expected_url = AirPurifierDriver.CTRL_URL.format(
        deviceid="device_1",
        identityid="test_identity_id",
        attribute="A02",
        value="0",
    )
    mock_airpurifier_driver._client.get.assert_awaited_once_with(expected_url)  # noqa: SLF001
    response.text.assert_awaited_once()


@pytest.mark.parametrize(
    "status",
    [
        500,
        503,
    ],
)
async def test_control_retries_on_server_error(mock_airpurifier_driver, status) -> None:
    """Test _rpc_attr retries once for 500/503 server errors."""

    first_response = Mock()
    first_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=Mock(), history=(), status=status, message="Server error"
    )

    second_response = Mock()
    second_response.raise_for_status = Mock()
    second_response.text = AsyncMock(return_value="OK")

    mock_airpurifier_driver._client.get = AsyncMock(  # noqa: SLF001
        side_effect=[first_response, second_response]
    )

    with patch("custom_components.winix.driver.asyncio.sleep", AsyncMock()) as sleep:
        await mock_airpurifier_driver.control(ATTR_POWER, OFF_VALUE)

    assert mock_airpurifier_driver._client.get.call_count == 2  # noqa: SLF001
    sleep.assert_awaited_once()


async def test_control_raises_on_non_retryable_http_error(
    mock_airpurifier_driver,
) -> None:
    """Test _rpc_attr raises HomeAssistantError for non-retryable HTTP errors."""

    response = Mock()
    response.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=Mock(), history=(), status=404, message="Not found"
    )
    mock_airpurifier_driver._client.get = AsyncMock(return_value=response)  # noqa: SLF001

    with pytest.raises(HomeAssistantError, match="Failed to download data: HTTP 404"):
        await mock_airpurifier_driver.control(ATTR_POWER, OFF_VALUE)


async def test_control_raises_on_client_error(mock_airpurifier_driver) -> None:
    """Test _rpc_attr raises HomeAssistantError on aiohttp client errors."""

    mock_airpurifier_driver._client.get = AsyncMock(  # noqa: SLF001
        side_effect=aiohttp.ClientError("Boom")
    )

    with pytest.raises(HomeAssistantError, match="Error communicating with Winix"):
        await mock_airpurifier_driver.control(ATTR_POWER, OFF_VALUE)


async def test_control_raises_on_timeout(mock_airpurifier_driver) -> None:
    """Test _rpc_attr raises HomeAssistantError on timeout."""

    mock_airpurifier_driver._client.get = AsyncMock(side_effect=TimeoutError())  # noqa: SLF001

    with pytest.raises(HomeAssistantError, match="Timeout communicating with Winix"):
        await mock_airpurifier_driver.control(ATTR_POWER, OFF_VALUE)


@pytest.mark.parametrize(
    ("mock_airpurifier_driver_with_payload", "expected"),
    [
        ({"A02": "0"}, {"power": "off"}),
        ({"A02": "1"}, {"power": "on"}),
        ({"S08": "79"}, {"air_qvalue": 79}),  # air_qvalue
        ({"S04": "12"}, {"pm2_5": 12}),  # pm2_5
        ({"A04": "08"}, {"airflow": "super"}),
        ({"S07": "04"}, {"air_quality": "very_poor"}),
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
async def test_dehumidifier_get_state(
    mock_dehumidifier_driver_with_payload, expected
) -> None:
    """Test get_state for DehumidifierDriver."""

    state = await mock_dehumidifier_driver_with_payload.get_state()
    assert state == expected


# ---------------------------------------------------------------------------
# AirConditionerDriver tests
# ---------------------------------------------------------------------------


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
@pytest.mark.parametrize(
    ("method", "args", "category", "value"),
    [
        ("turn_on", [], "ac_power", "on"),
        ("turn_off", [], "ac_power", "off"),
        ("set_mode", ["auto"], "ac_mode", "auto"),
        ("set_mode", ["cool"], "ac_mode", "cool"),
        ("set_mode", ["fan_only"], "ac_mode", "fan_only"),
        ("set_mode", ["dry"], "ac_mode", "dry"),
        ("set_swing", [True], "ac_swing", "on"),
        ("set_swing", [False], "ac_swing", "off"),
        ("set_turbo", [True], "ac_turbo", "on"),
        ("set_turbo", [False], "ac_turbo", "off"),
    ],
)
async def test_air_conditioner_control(
    mock_rpc_attr, mock_air_conditioner_driver, method, args, category, value
) -> None:
    """Test AirConditionerDriver control methods that go through control()."""

    await getattr(mock_air_conditioner_driver, method)(*args)
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == (
        AirConditionerDriver.category_keys[category],
        AirConditionerDriver.state_keys[category][value],
    )


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
async def test_air_conditioner_set_target_temperature(
    mock_rpc_attr, mock_air_conditioner_driver
) -> None:
    """Test set_target_temperature writes C07 directly."""

    await mock_air_conditioner_driver.set_target_temperature(24)
    assert mock_rpc_attr.call_count == 1
    assert mock_rpc_attr.call_args[0] == ("C07", "24")


@patch("custom_components.winix.driver.WinixDriver._rpc_attr")
async def test_air_conditioner_set_fan_speed_clears_turbo(
    mock_rpc_attr, mock_air_conditioner_driver
) -> None:
    """Test set_fan_speed writes C04 and also clears turbo (C05)."""

    await mock_air_conditioner_driver.set_fan_speed(3)
    assert mock_rpc_attr.call_count == 2
    assert mock_rpc_attr.call_args_list[0][0] == ("C04", "03")
    assert mock_rpc_attr.call_args_list[1][0] == ("C05", "0")


@pytest.mark.parametrize(
    ("mock_air_conditioner_driver_with_payload", "expected"),
    [
        ({"C02": "0"}, {"ac_power": "off"}),
        ({"C02": "1"}, {"ac_power": "on"}),
        ({"C03": "01"}, {"ac_mode": "auto"}),
        ({"C03": "02"}, {"ac_mode": "cool"}),
        ({"C03": "03"}, {"ac_mode": "fan_only"}),
        ({"C03": "04"}, {"ac_mode": "dry"}),
        ({"C04": "03"}, {"ac_fan_speed": 3}),
        ({"C05": "1"}, {"ac_turbo": "on"}),
        ({"C07": "24"}, {"ac_target_temperature": 24}),
        ({"C10": "1"}, {"ac_swing": "on"}),
        ({"S01": "26"}, {"ac_current_temperature": 26}),
        ({"S06": "512"}, {"power_consumption": 512}),
        # Unmapped attributes (S05 - compressor load, not exposed) are ignored.
        # S06 is also absent entirely from the real payload when the unit is
        # powered off, which get_state() handles the same way via .get().
        ({"C02": "0", "S05": "0"}, {"ac_power": "off"}),
    ],
    indirect=["mock_air_conditioner_driver_with_payload"],
)
async def test_air_conditioner_get_state(
    mock_air_conditioner_driver_with_payload, expected
) -> None:
    """Test get_state for AirConditionerDriver."""

    state = await mock_air_conditioner_driver_with_payload.get_state()
    assert state == expected
