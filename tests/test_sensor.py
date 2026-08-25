"""Test Winix sensors."""

from unittest.mock import Mock

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.winix.const import ATTR_AIR_QUALITY, WINIX_DOMAIN
from custom_components.winix.sensor import SENSOR_DESCRIPTIONS
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import UnitOfDensity
from homeassistant.core import HomeAssistant

from .common import init_integration  # noqa: TID251

TEST_DEVICE_ID = "847207352CE0_364yr8i989"
PM25_SENSOR_ID = "sensor.winix_devicealias_pm_2_5"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_setup_integration(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test integration setup."""

    entry = await init_integration(hass, device_stub, device_data, aioclient_mock)
    assert len(hass.config_entries.async_entries(WINIX_DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_sensor_air_qvalue(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test qvalue sensor."""

    air_qvalue = "71"
    device_data["body"]["data"][0]["attributes"]["S08"] = air_qvalue

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get("sensor.winix_devicealias_air_qvalue")
    assert entity_state is not None
    assert int(entity_state.state) == int(air_qvalue)
    assert entity_state.attributes.get("unit_of_measurement") == "qv"
    assert entity_state.attributes.get(ATTR_AIR_QUALITY) == "good"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_sensors(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the sensors."""

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    aqi = "01"

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None

    entity_state = hass.states.get("sensor.winix_devicealias_aqi")
    assert entity_state is not None
    assert int(entity_state.state) == int(aqi)

    expected_pm25 = "12"
    entity_state = hass.states.get(PM25_SENSOR_ID)
    assert entity_state is not None
    assert int(entity_state.state) == int(expected_pm25)
    assert (
        entity_state.attributes.get("unit_of_measurement")
        == UnitOfDensity.MICROGRAMS_PER_CUBIC_METER
    )

    entity_state = hass.states.get("sensor.winix_devicealias_max_filter_life")
    assert entity_state is not None
    assert entity_state.state == "6480"


@pytest.mark.usefixtures("enable_custom_integrations")
@pytest.mark.parametrize(
    ("data_filter_life", "expected"),
    [("6481", "unknown"), ("6480", "0"), ("1257", "81")],
)
async def test_filter_life_sensor(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    data_filter_life,
    expected,
) -> None:
    """Test the sensors."""

    device_data["body"]["data"][0]["attributes"]["A21"] = data_filter_life
    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None
    assert entity_state.state == expected


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_sensor_filter_life_missing(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test filter life sensor for missing data."""

    del device_data["body"]["data"][0]["attributes"]["A21"]  # Mock missing data

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None
    assert (
        entity_state.state == "unknown"
    )  # Missing data evaluates to None which is unknown state


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_sensor_pm25_missing(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test PM 2.5 sensor for missing data."""

    del device_data["body"]["data"][0]["attributes"]["S04"]

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get(PM25_SENSOR_ID)
    assert entity_state is None


# ---------------------------------------------------------------------------
# Power consumption (air conditioner only)
# ---------------------------------------------------------------------------


def _get_description(key: str):
    """Return the WinixSensorEntityDescription for the given key."""
    return next(d for d in SENSOR_DESCRIPTIONS if d.key == key)


def test_power_consumption_exists_only_for_air_conditioner() -> None:
    """The power_consumption sensor is scoped to air conditioners only."""

    description = _get_description("power_consumption")

    ac_device = Mock(is_air_conditioner=True)
    purifier_device = Mock(is_air_conditioner=False)

    assert description.exists_fn(ac_device) is True
    assert description.exists_fn(purifier_device) is False


def test_power_consumption_value_fn() -> None:
    """value_fn reads the power_consumption key from state."""

    description = _get_description("power_consumption")

    assert description.value_fn({"power_consumption": 512}, Mock()) == 512
    assert description.value_fn({}, Mock()) is None
