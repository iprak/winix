"""Test WinixAirQualitySensor component."""

from unittest.mock import MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.const import (
    ATTR_AIR_AQI,
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    ATTR_FILTER_HOUR,
    SENSOR_AIR_QVALUE,
    SENSOR_AQI,
    WINIX_DATA_COORDINATOR,
    WINIX_DOMAIN,
)
from custom_components.winix.sensor import (
    TOTAL_FILTER_LIFE,
    WinixSensor,
    async_setup_entry,
)
from tests import build_fake_manager


async def test_setup_platform():
    """Test platform setup."""

    manager = build_fake_manager(3)
    hass = Mock()
    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id1")
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


@pytest.mark.parametrize(
    ("sensor_key", "state_key", "state_value", "expected"),
    [
        (SENSOR_AIR_QVALUE, ATTR_AIR_QVALUE, 100, 100),
        (SENSOR_AQI, ATTR_AIR_AQI, 100, 100),
    ],
)
def test_sensor_native_value(
    state_key, state_value, expected, mock_sensor_description, mock_device_wrapper
):
    """Test sensor native state values."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)
    coordinator = Mock()

    sensor = WinixSensor(mock_device_wrapper, coordinator, mock_sensor_description)
    assert sensor.state is None

    mock_device_wrapper.get_state = MagicMock(return_value={state_key: state_value})
    assert sensor.native_value == expected


@pytest.mark.parametrize(
    ("filter_hour", "expected"),
    [
        (None, None),
        (100, 98),  # 100 hour
        (TOTAL_FILTER_LIFE + 1, None),  # Overbound filter life
    ],
)
def test_filter_life_sensor_native_value(
    filter_hour, expected, mock_device_wrapper, mock_filter_life_description
):
    """Test filter life sensor state."""
    mock_device_wrapper.get_state = MagicMock(return_value=None)
    coordinator = Mock()

    sensor = WinixSensor(mock_device_wrapper, coordinator, mock_filter_life_description)

    mock_device_wrapper.get_state = MagicMock(
        return_value={} if filter_hour is None else {ATTR_FILTER_HOUR: filter_hour}
    )
    assert sensor.native_value == expected
