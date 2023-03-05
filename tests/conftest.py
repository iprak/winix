"""Tests for Winixdevice component."""

from unittest.mock import AsyncMock, MagicMock, Mock

from homeassistant import loader
from homeassistant.components.sensor import SensorEntityDescription, SensorStateClass
from homeassistant.const import PERCENTAGE
import pytest

from custom_components.winix.const import SENSOR_AIR_QVALUE, SENSOR_FILTER_LIFE
from custom_components.winix.device_wrapper import WinixDeviceWrapper
from custom_components.winix.driver import WinixDriver


@pytest.fixture
def mock_device_wrapper() -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""

    device_wrapper = MagicMock()
    device_wrapper.device_stub.mac = "f190d35456d0"
    device_wrapper.device_stub.alias = "Purifier1"

    device_wrapper.async_plasmawave_off = AsyncMock()
    device_wrapper.async_plasmawave_on = AsyncMock()
    device_wrapper.async_set_preset_mode = AsyncMock()
    device_wrapper.async_set_speed = AsyncMock()
    device_wrapper.async_turn_on = AsyncMock()

    yield device_wrapper


@pytest.fixture
def mock_sensor_description(sensor_key) -> SensorEntityDescription:
    """Return a mocked SensorEntityDescription instance."""

    yield SensorEntityDescription(
        key=sensor_key,
        name="Test sensor description",
        state_class=SensorStateClass.MEASUREMENT,
    )


@pytest.fixture
def mock_qvalue_description() -> SensorEntityDescription:
    """Return a mocked qValue SensorEntityDescription instance."""

    yield SensorEntityDescription(
        key=SENSOR_AIR_QVALUE,
        name="Air QValue",
        native_unit_of_measurement="qv",
        state_class=SensorStateClass.MEASUREMENT,
    )


@pytest.fixture
def mock_filter_life_description() -> SensorEntityDescription:
    """Return a mocked SensorEntityDescription instance."""

    yield SensorEntityDescription(
        key=SENSOR_FILTER_LIFE,
        name="Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    )


@pytest.fixture
def mock_driver() -> WinixDriver:
    """Return a mocked WinixDriver instance."""
    client = Mock()
    device_id = "device_1"
    yield WinixDriver(device_id, client)


@pytest.fixture
def mock_driver_with_payload(request) -> WinixDriver:
    """Return a mocked WinixDriver instance."""

    json_value = {"body": {"data": [{"attributes": request.param}]}}

    response = Mock()
    response.json = AsyncMock(return_value=json_value)

    client = Mock()  # aiohttp.ClientSession
    client.get = AsyncMock(return_value=response)

    device_id = "device_1"
    yield WinixDriver(device_id, client)


@pytest.fixture
def enable_custom_integrations(hass):
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS)
