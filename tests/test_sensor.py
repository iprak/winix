"""Test Winix sensors."""

from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.winix import model
from custom_components.winix.const import WINIX_DOMAIN
from homeassistant.config_entries import ConfigEntryState
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
async def test_sensors(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the sensors."""

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is not None

    entity_state = hass.states.get("sensor.winix_devicealias_aqi")
    assert entity_state is None  # aqi sensor has been removed

    entity_state = hass.states.get("sensor.winix_devicealias_gas_sensor_level")
    assert entity_state is not None
    assert int(entity_state.state) == 1  # From S07 in device_data

    entity_state = hass.states.get("sensor.winix_devicealias_gas_sensor")
    assert entity_state is not None
    assert int(entity_state.state) == 74  # From S08 in device_data

    entity_state = hass.states.get("sensor.winix_devicealias_max_filter_life")
    assert entity_state is not None
    assert entity_state.state == "6480"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_all_model_sensors(
    hass: HomeAssistant,
    device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that every model sensor can be set up."""

    all_sensors = SimpleNamespace(value=tuple(model.ModelSensor))
    monkeypatch.setattr(
        model.ModelSensorProfile, "ALL_SENSORS", all_sensors, raising=False
    )
    monkeypatch.setattr(
        model,
        "MODEL_INFO_DATA",
        (
            *model.MODEL_INFO_DATA,
            ("test_model_id", "Test Model", model.ModelSensorProfile.ALL_SENSORS),
        ),
    )
    device_stub.model_id = "test_model_id"
    device_data["body"]["data"][0]["modelId"] = "test_model_id"

    entry = await init_integration(hass, device_stub, device_data, aioclient_mock)

    sensors = entry.runtime_data.models.get_sensors("test_model_id")
    assert len(sensors) == len(model.ModelSensor)
    assert len(hass.states.async_entity_ids("sensor")) == len(model.ModelSensor) + 2

    for sensor in sensors:
        entity_state = hass.states.get(f"sensor.winix_devicealias_{sensor.key}")
        assert entity_state is not None
        assert entity_state.state is not None


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


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_air_conditioner_sensors(
    hass: HomeAssistant,
    air_conditioner_device_stub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test the sensors."""

    await init_integration(
        hass, air_conditioner_device_stub, device_data, aioclient_mock
    )

    entity_state = hass.states.get("sensor.winix_devicealias_filter_life")
    assert entity_state is None

    entity_state = hass.states.get("sensor.winix_devicealias_aqi")
    assert entity_state is None

    entity_state = hass.states.get("sensor.winix_devicealias_power_consumption")
    assert entity_state is not None
