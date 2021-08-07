"""Test Winixdevice component."""

from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.fan import SUPPORT_PRESET_MODE, SUPPORT_SET_SPEED
import pytest

from custom_components.winix.const import (
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    ATTR_AIRFLOW,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
)
from custom_components.winix.fan import WinixPurifier


def test_construction():
    """Test device construction."""
    device_wrapper = Mock()
    device_wrapper.get_state = Mock(return_value={})

    device = WinixPurifier(device_wrapper)
    assert device.unique_id is not None
    assert device.preset_modes == PRESET_MODES
    assert device.speed_list == ORDERED_NAMED_FAN_SPEEDS
    assert device.speed_count == len(ORDERED_NAMED_FAN_SPEEDS)
    assert device.supported_features == (SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED)
    assert device.device_info is not None
    assert device.name is not None


def test_device_availability():
    """Test device availability."""
    device_wrapper = Mock()
    device_wrapper.get_state = Mock(return_value=None)

    device = WinixPurifier(device_wrapper)
    assert not device.available

    device_wrapper.get_state = Mock(return_value={})
    assert device.available


def test_device_attributes():
    """Test device attributes."""
    device_wrapper = Mock()
    device_wrapper.get_state = Mock(return_value=None)

    device = WinixPurifier(device_wrapper)
    assert device.device_state_attributes is not None

    device_wrapper.get_state = Mock(return_value={"DUMMY_ATTR": 12})
    assert device.device_state_attributes["DUMMY_ATTR"] == 12


@pytest.mark.parametrize("value", [(True), (False)])
def test_device_on(value):
    """Test device on."""

    device_wrapper = Mock()
    type(device_wrapper).is_on = value
    device = WinixPurifier(device_wrapper)
    assert device.is_on == value


@pytest.mark.parametrize(
    "state,is_sleep,is_auto,expected",
    [
        (None, None, None, None),
        ({}, True, False, None),
        ({}, False, True, None),
        ({ATTR_AIRFLOW: AIRFLOW_LOW}, False, False, 25),
        ({ATTR_AIRFLOW: AIRFLOW_HIGH}, False, False, 75),
    ],
)
def test_device_percentage(state, is_sleep, is_auto, expected):
    """Test device percentage."""

    device_wrapper = Mock()
    type(device_wrapper).is_sleep = is_sleep
    type(device_wrapper).is_auto = is_auto
    device_wrapper.get_state = Mock(return_value=state)
    device = WinixPurifier(device_wrapper)
    assert device.percentage is expected


@pytest.mark.parametrize(
    "state,is_sleep,is_auto,is_manual,is_plasma_on,expected",
    [
        (None, None, None, None, None, None),
        ({}, True, False, False, False, PRESET_MODE_SLEEP),
        ({}, False, False, False, False, None),
        ({}, False, True, False, False, PRESET_MODE_AUTO),
        ({}, False, False, True, False, PRESET_MODE_MANUAL),
        ({}, False, False, True, True, PRESET_MODE_MANUAL_PLASMA),
    ],
)
def test_device_preset_mode(
    state, is_sleep, is_auto, is_manual, is_plasma_on, expected
):
    """Test device preset mode."""

    device_wrapper = Mock()
    type(device_wrapper).is_sleep = is_sleep
    type(device_wrapper).is_auto = is_auto
    type(device_wrapper).is_manual = is_manual
    type(device_wrapper).is_plasma_on = is_plasma_on
    device_wrapper.get_state = Mock(return_value=state)
    device = WinixPurifier(device_wrapper)
    assert device.preset_mode is expected


async def test_async_set_percentage_zero():
    """Test setting percentage speed."""
    device_wrapper = Mock()
    device_wrapper.async_set_speed = AsyncMock()

    device = WinixPurifier(device_wrapper)
    device.async_turn_off = AsyncMock()

    await device.async_set_percentage(0)
    assert device.async_turn_off.call_count == 1
    assert device_wrapper.async_set_speed.call_count == 0


async def test_async_set_percentage_non_zero():
    """Test setting percentage speed."""
    device_wrapper = Mock()
    device_wrapper.async_set_speed = AsyncMock()

    device = WinixPurifier(device_wrapper)
    device.async_turn_off = AsyncMock()

    await device.async_set_percentage(20)
    assert device.async_turn_off.call_count == 0
    assert device_wrapper.async_set_speed.call_count == 1


async def test_async_turn_on():
    """Test turning on."""
    device_wrapper = Mock()

    device = WinixPurifier(device_wrapper)
    device.async_set_percentage = AsyncMock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    await device.async_turn_on()
    assert device.async_set_percentage.call_count == 0
    assert device_wrapper.async_set_preset_mode.call_count == 0
    assert device_wrapper.async_turn_on.call_count == 1


async def test_async_turn_on_percentage():
    """Test turning on."""
    device_wrapper = Mock()

    device = WinixPurifier(device_wrapper)
    device.async_set_percentage = AsyncMock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    await device.async_turn_on(None, 25)
    assert device.async_set_percentage.call_count == 1
    assert device_wrapper.async_set_preset_mode.call_count == 0
    assert device_wrapper.async_turn_on.call_count == 0


async def test_async_turn_on_preset():
    """Test turning on."""
    device_wrapper = Mock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    device = WinixPurifier(device_wrapper)
    device.async_set_percentage = AsyncMock()

    await device.async_turn_on(None, None, PRESET_MODE_MANUAL)
    assert device.async_set_percentage.call_count == 0
    assert device_wrapper.async_set_preset_mode.call_count == 1
    assert device_wrapper.async_turn_on.call_count == 0


@pytest.mark.parametrize(
    "args",
    [
        (["async_turn_off"]),
        (["async_plasmawave_on"]),
        (["async_plasmawave_off"]),
        (["async_set_preset_mode", PRESET_MODE_MANUAL]),
    ],
)
async def test_fan_operations(args):
    """Test other fan operations."""
    mocked_method = AsyncMock()
    device_wrapper = Mock()
    method = args[0]

    with patch.object(device_wrapper, method, mocked_method):
        device = WinixPurifier(device_wrapper)

        if len(args) == 2:
            await getattr(device, method)(args[1])
        else:
            await getattr(device, method)()

        assert mocked_method.call_count == 1


@pytest.mark.parametrize(
    "is_plasma_on",
    [
        (True),
        (False),
    ],
)
async def test_plasma_toggle(is_plasma_on):
    """Test pasma toggle operation."""
    device_wrapper = Mock()
    device_wrapper.async_plasmawave_off = AsyncMock()
    device_wrapper.async_plasmawave_on = AsyncMock()

    type(device_wrapper).is_plasma_on = is_plasma_on

    device = WinixPurifier(device_wrapper)
    await device.async_plasmawave_toggle()

    if is_plasma_on:
        assert device_wrapper.async_plasmawave_off.call_count == 1
        assert device_wrapper.async_plasmawave_on.call_count == 0
    else:
        assert device_wrapper.async_plasmawave_off.call_count == 0
        assert device_wrapper.async_plasmawave_on.call_count == 1
