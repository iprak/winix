"""Test WinixSensor component."""

from unittest.mock import MagicMock, Mock

from custom_components.winix.const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE, DOMAIN
from custom_components.winix.sensor import (
    ICON,
    UNIT_OF_MEASUREMENT,
    WinixSensor,
    async_setup_platform,
)

from tests import build_fake_manager


async def test_setup_platform():
    """Test platform setup."""

    manager = build_fake_manager(3)
    hass = Mock()
    hass.data = {DOMAIN: manager}

    async_add_entities = Mock()
    await async_setup_platform(hass, None, async_add_entities, None)
    assert async_add_entities.called
    assert len(async_add_entities.call_args[0][0]) == 3


def test_sensor_construction():
    """Test sensor construction."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value={})

    sensor = WinixSensor(device_wrapper)
    assert sensor.unique_id is not None
    assert sensor.device_info is not None
    assert sensor.icon == ICON
    assert sensor.name is not None
    assert sensor.unit_of_measurement is UNIT_OF_MEASUREMENT


def test_sensor_availability():
    """Test sensor availability."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value=None)

    sensor = WinixSensor(device_wrapper)
    assert not sensor.available

    device_wrapper.get_state = MagicMock(return_value={})
    assert sensor.available


def test_sensor_attributes(mock_device_wrapper):
    """Test sensor attributes."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)

    sensor = WinixSensor(mock_device_wrapper)

    assert sensor.extra_state_attributes[ATTR_AIR_QUALITY] is None

    mock_device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QUALITY: 12})
    assert sensor.extra_state_attributes[ATTR_AIR_QUALITY] == 12


def test_sensor_state(mock_device_wrapper):
    """Test sensor state."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)

    sensor = WinixSensor(mock_device_wrapper)

    assert sensor.state is None

    mock_device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QVALUE: 100})
    assert sensor.state == 100
