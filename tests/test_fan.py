"""Test Winixdevice component."""

from unittest.mock import AsyncMock, Mock, patch

from homeassistant.components.fan import SUPPORT_PRESET_MODE, SUPPORT_SET_SPEED
from homeassistant.const import ATTR_ENTITY_ID
import pytest

from custom_components.winix.const import (
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    ATTR_AIRFLOW,
    DOMAIN,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODE_AUTO,
    PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA_OFF,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
    SERVICE_PLASMAWAVE_ON,
    WINIX_DATA_KEY,
)
from custom_components.winix.fan import WinixPurifier, async_setup_platform

from tests import build_fake_manager, build_purifier


async def test_setup_platform(hass):
    """Test platform setup."""

    manager = build_fake_manager(3)
    hass.data = {DOMAIN: manager}

    async_add_entities = Mock()

    await async_setup_platform(hass, None, async_add_entities, None)

    assert async_add_entities.called
    assert len(async_add_entities.call_args[0][0]) == 3


async def test_service(hass):
    """Test platform setup."""

    manager = build_fake_manager(2)
    hass.data = {DOMAIN: manager}

    async_add_entities = Mock()

    await async_setup_platform(hass, None, async_add_entities, None)

    first_entity_id = None

    # Prepare the devices for serive call
    for device in hass.data[WINIX_DATA_KEY]:
        device.hass = hass
        device.entity_id = device.unique_id

        if first_entity_id is None:
            first_entity_id = device.entity_id

    # Test service call with a specific entity_id
    with patch(
        "custom_components.winix.fan.WinixPurifier.async_plasmawave_on"
    ) as mock_plasmawave_on, patch(
        "custom_components.winix.fan.WinixPurifier.async_update_ha_state"
    ) as mock_update_ha_state:
        service_data = {ATTR_ENTITY_ID: [first_entity_id]}
        await hass.services.async_call(
            DOMAIN, SERVICE_PLASMAWAVE_ON, service_data, blocking=True
        )

        assert mock_plasmawave_on.call_count == 1  # Should be called once

        # Devices on which service call is made have their state updated
        assert mock_update_ha_state.call_count == 1

    # Test service call with no entity_id, call is made on all devices
    with patch(
        "custom_components.winix.fan.WinixPurifier.async_plasmawave_on"
    ) as mock_plasmawave_on, patch(
        "custom_components.winix.fan.WinixPurifier.async_update_ha_state"
    ) as mock_update_ha_state:
        await hass.services.async_call(DOMAIN, SERVICE_PLASMAWAVE_ON, {}, blocking=True)
        assert mock_plasmawave_on.call_count == 2  # Called for each device

        # Devices on which service call is made have their state updated
        assert mock_update_ha_state.call_count == 2


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
    assert device.extra_state_attributes is not None

    device_wrapper.get_state = Mock(return_value={"DUMMY_ATTR": 12})
    assert device.extra_state_attributes["DUMMY_ATTR"] == 12


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
        ({ATTR_AIRFLOW: None}, None, None, None),
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
    "state,is_sleep,is_auto,is_manual,is_plasma_on,is_plasma_off,expected",
    [
        (None, None, None, None, None, None, None),
        ({}, True, False, False, False, False, PRESET_MODE_SLEEP),
        ({}, False, False, False, False, False, None),
        ({}, False, True, False, True, False, PRESET_MODE_AUTO),
        ({}, False, True, False, False, True, PRESET_MODE_AUTO_PLASMA_OFF),
        ({}, False, False, True, True, False, PRESET_MODE_MANUAL),
        ({}, False, False, True, False, True, PRESET_MODE_MANUAL_PLASMA_OFF),
    ],
)
def test_device_preset_mode(
    state, is_sleep, is_auto, is_manual, is_plasma_on, is_plasma_off, expected
):
    """Test device preset mode."""

    device_wrapper = Mock()
    type(device_wrapper).is_sleep = is_sleep
    type(device_wrapper).is_auto = is_auto
    type(device_wrapper).is_manual = is_manual
    type(device_wrapper).is_plasma_on = is_plasma_on
    type(device_wrapper).is_plasma_off = is_plasma_off
    device_wrapper.get_state = Mock(return_value=state)
    device = WinixPurifier(device_wrapper)
    assert device.preset_mode is expected


async def test_async_set_percentage_zero(hass, mock_device_wrapper):
    """Test setting percentage speed."""

    device = build_purifier(hass, mock_device_wrapper)
    device.async_turn_off = AsyncMock()

    await device.async_set_percentage(0)
    assert device.async_turn_off.call_count == 1
    assert mock_device_wrapper.async_set_speed.call_count == 0


async def test_async_set_percentage_non_zero(hass, mock_device_wrapper):
    """Test setting percentage speed."""

    device = build_purifier(hass, mock_device_wrapper)
    device.async_turn_off = AsyncMock()

    await device.async_set_percentage(20)
    assert device.async_turn_off.call_count == 0
    assert mock_device_wrapper.async_set_speed.call_count == 1


async def test_async_turn_on(hass, mock_device_wrapper):
    """Test turning on."""

    device = build_purifier(hass, mock_device_wrapper)
    device.async_set_percentage = AsyncMock()

    await device.async_turn_on()
    assert device.async_set_percentage.call_count == 0
    assert mock_device_wrapper.async_set_preset_mode.call_count == 0
    assert mock_device_wrapper.async_turn_on.call_count == 1


async def test_async_turn_on_percentage(hass, mock_device_wrapper):
    """Test turning on."""

    device = build_purifier(hass, mock_device_wrapper)
    device.async_set_percentage = AsyncMock()

    await device.async_turn_on(None, 25)
    assert device.async_set_percentage.call_count == 1
    assert mock_device_wrapper.async_set_preset_mode.call_count == 0
    assert mock_device_wrapper.async_turn_on.call_count == 0


async def test_async_turn_on_preset(hass, mock_device_wrapper):
    """Test turning on."""

    device = build_purifier(hass, mock_device_wrapper)
    device.async_set_percentage = AsyncMock()

    await device.async_turn_on(None, None, PRESET_MODE_MANUAL)
    assert device.async_set_percentage.call_count == 0
    assert mock_device_wrapper.async_set_preset_mode.call_count == 1
    assert mock_device_wrapper.async_turn_on.call_count == 0


@pytest.mark.parametrize(
    "args",
    [
        (["async_turn_off"]),
        (["async_plasmawave_on"]),
        (["async_plasmawave_off"]),
        (["async_set_preset_mode", PRESET_MODE_MANUAL]),
    ],
)
async def test_fan_operations(hass, mock_device_wrapper, args):
    """Test other fan operations."""
    mocked_method = AsyncMock()
    method = args[0]

    with patch.object(mock_device_wrapper, method, mocked_method):
        device = build_purifier(hass, mock_device_wrapper)

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
async def test_plasma_toggle(hass, mock_device_wrapper, is_plasma_on):
    """Test pasma toggle operation."""
    type(mock_device_wrapper).is_plasma_on = is_plasma_on

    device = build_purifier(hass, mock_device_wrapper)

    await device.async_plasmawave_toggle()

    if is_plasma_on:
        assert mock_device_wrapper.async_plasmawave_off.call_count == 1
        assert mock_device_wrapper.async_plasmawave_on.call_count == 0
    else:
        assert mock_device_wrapper.async_plasmawave_off.call_count == 0
        assert mock_device_wrapper.async_plasmawave_on.call_count == 1
