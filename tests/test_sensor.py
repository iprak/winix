"""Test WinixAirQualitySensor component."""

from unittest.mock import MagicMock, Mock

from homeassistant.config_entries import ConfigEntry

from custom_components.winix.const import (
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    WINIX_DATA_COORDINATOR,
    WINIX_DOMAIN,
)
from custom_components.winix.sensor import WinixSensor, async_setup_entry

from tests import build_fake_manager


async def test_setup_platform():
    """Test platform setup."""

    manager = build_fake_manager(3)
    hass = Mock()
    config = ConfigEntry(1, WINIX_DOMAIN, "", {}, "Test", entry_id="id1")
    hass.data = {WINIX_DOMAIN: {"id1": {WINIX_DATA_COORDINATOR: manager}}}

    async_add_entities = Mock()
    await async_setup_entry(hass, config, async_add_entities)
    assert async_add_entities.called
    assert len(async_add_entities.call_args[0][0]) == 9  # 3 sensors per device


def test_sensor_construction(mock_qvalue_description):
    """Test sensor construction."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value={})
    coordinator = Mock()

    sensor = WinixSensor(device_wrapper, coordinator, mock_qvalue_description)
    assert sensor.unique_id is not None
    assert sensor.device_info is not None
    assert sensor.name is not None
    assert sensor.unit_of_measurement == "qv"


def test_sensor_availability(mock_qvalue_description):
    """Test sensor availability."""
    device_wrapper = Mock()
    device_wrapper.get_state = MagicMock(return_value=None)
    coordinator = Mock()

    sensor = WinixSensor(device_wrapper, coordinator, mock_qvalue_description)
    assert not sensor.available

    device_wrapper.get_state = MagicMock(return_value={})
    assert sensor.available


def test_sensor_attributes(mock_device_wrapper, mock_qvalue_description):
    """Test sensor attributes."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)
    coordinator = Mock()

    sensor = WinixSensor(mock_device_wrapper, coordinator, mock_qvalue_description)

    # Initially we will have no value
    assert sensor.extra_state_attributes is not None
    assert sensor.extra_state_attributes[ATTR_AIR_QUALITY] is None

    mock_device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QUALITY: 12})
    assert sensor.extra_state_attributes[ATTR_AIR_QUALITY] == 12


def test_sensor_native_value(mock_device_wrapper, mock_qvalue_description):
    """Test sensor state."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)
    coordinator = Mock()

    sensor = WinixSensor(mock_device_wrapper, coordinator, mock_qvalue_description)

    assert sensor.state is None

    mock_device_wrapper.get_state = MagicMock(return_value={ATTR_AIR_QVALUE: 100})
    assert sensor.native_value == 100
