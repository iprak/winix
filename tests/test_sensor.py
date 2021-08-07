"""Test WinixSensor component."""

from unittest.mock import MagicMock, Mock

from custom_components.winix.const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE
from custom_components.winix.sensor import ICON, UNIT_OF_MEASUREMENT, WinixSensor


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


def test_sensor_attributes():
    """Test sensor attributes."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value=None)

    sensor = WinixSensor(device_wrapper)

    assert sensor.device_state_attributes[ATTR_AIR_QUALITY] is None

    device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QUALITY: 12})
    assert sensor.device_state_attributes[ATTR_AIR_QUALITY] == 12


def test_sensor_state():
    """Test sensor state."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value=None)

    sensor = WinixSensor(device_wrapper)

    assert sensor.state is None

    device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QVALUE: 100})
    assert sensor.state == 100
