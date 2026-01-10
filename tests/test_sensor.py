"""Test WinixAirQualitySensor component."""


from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.winix.const import (
    ATTR_AIR_QUALITY,
    DEFAULT_FILTER_ALARM_DURATION_HOURS,
    WINIX_DOMAIN,
)
from custom_components.winix.sensor import get_filter_life_percentage
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .common import init_integration

TEST_DEVICE_ID = "847207352CE0_364yr8i989"


async def test_setup_integration(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    enable_custom_integrations,
) -> None:
    """Test integration setup."""

    entry = await init_integration(hass, device_stub, device_data, aioclient_mock)
    assert len(hass.config_entries.async_entries(WINIX_DOMAIN)) == 1
    assert entry.state is ConfigEntryState.LOADED


async def test_sensor_air_qvalue(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    enable_custom_integrations,
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


async def test_sensors(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    enable_custom_integrations,
) -> None:
    """Test other sensor."""

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    filter_life_hours = "1257"
    aqi = "01"

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None
    assert int(entity_state.state) == get_filter_life_percentage(
        filter_life_hours, DEFAULT_FILTER_ALARM_DURATION_HOURS
    )

    entity_state = hass.states.get("sensor.winix_devicealias_aqi")
    assert entity_state is not None
    assert int(entity_state.state) == int(aqi)

    pm25 = "12"
    entity_state = hass.states.get("sensor.winix_devicealias_pm2_5")
    assert entity_state is not None
    assert int(entity_state.state) == int(pm25)
    assert entity_state.attributes.get("unit_of_measurement") == "µg/m³"


async def test_sensor_filter_life_missing(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    enable_custom_integrations,
) -> None:
    """Test filter life sensor for missing data."""

    del device_data["body"]["data"][0]["attributes"]["A21"]  # Mock missing data

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None
    assert (
        entity_state.state == "unknown"
    )  # Missing data evaluates to None which is unknown state
