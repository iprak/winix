"""Test component setup."""

import dataclasses

import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.winix.const import WINIX_DOMAIN
from custom_components.winix.stub import MyWinixDeviceStub
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .common import init_integration  # noqa: TID251

UPPERCASE_MAC = "847207352CE0"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_deprecated_sensors_removed_for_uppercase_mac(
    hass: HomeAssistant,
    device_stub: MyWinixDeviceStub,
    device_data,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Deprecated sensors are removed when the API reports an uppercase MAC."""

    device_stub = dataclasses.replace(device_stub, mac=UPPERCASE_MAC)
    entity_registry = er.async_get(hass)

    # v1.x registered these with the lowercased MAC.
    unique_ids = [
        f"{SENSOR_DOMAIN}.{WINIX_DOMAIN}_{prefix}_{UPPERCASE_MAC.lower()}"
        for prefix in ("air_qvalue", "aqi")
    ]
    for unique_id in unique_ids:
        entity_registry.async_get_or_create(SENSOR_DOMAIN, WINIX_DOMAIN, unique_id)

    await init_integration(hass, device_stub, device_data, aioclient_mock)

    for unique_id in unique_ids:
        assert (
            entity_registry.async_get_entity_id(SENSOR_DOMAIN, WINIX_DOMAIN, unique_id)
            is None
        )
