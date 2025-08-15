"""Tests for Winix component."""

from unittest.mock import MagicMock, Mock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from voluptuous.validators import Number

from custom_components.winix.const import WINIX_AUTH_RESPONSE, WINIX_DOMAIN
from custom_components.winix.device_wrapper import MyWinixDeviceStub, WinixDeviceWrapper
from custom_components.winix.fan import WinixPurifier
from custom_components.winix.manager import WinixManager
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

TEST_DEVICE_ID = "847207352CE0_364yr8i989"


def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create a mock config entry."""
    user_input = {
        WINIX_AUTH_RESPONSE: {
            "user_id": "user_id",
            "access_token": "access_token",
            "refresh_token": "refresh_token",
            "id_token": "id_token",
        },
        CONF_USERNAME: "username",
        CONF_PASSWORD: "password",
    }

    entry = MockConfigEntry(
        domain=WINIX_DOMAIN,
        data=user_input,
    )
    entry.add_to_hass(hass)
    return entry


async def init_integration(
    hass: HomeAssistant,
    test_device_stub: MyWinixDeviceStub,
    test_device_json: any,
    aioclient_mock: AiohttpClientMocker,
) -> MockConfigEntry:
    """Prepare the integration."""

    entry = config_entry(hass)

    aioclient_mock.get(
        f"https://us.api.winix-iot.com/common/event/sttus/devices/{TEST_DEVICE_ID}",
        json=test_device_json,
    )

    with (
        patch(
            "custom_components.winix.Helpers.get_device_stubs",
            return_value=[test_device_stub],
        ),
        patch("winix.WinixAccount.get_uuid"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


def build_mock_wrapper(index: Number = 0) -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""
    client = Mock()

    device_stub = Mock()

    device_stub.mac = f"f190d35456d{index}"
    device_stub.alias = f"Purifier{index}"

    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()

    return WinixDeviceWrapper(client, device_stub, logger)


def build_fake_manager(wrapper_count: Number) -> WinixManager:
    """Return a mocked WinixManager instance."""
    wrappers = []

    # Prepare fake wrappers
    wrappers = {build_mock_wrapper(index) for index in range(wrapper_count)}

    manager = MagicMock()
    manager.get_device_wrappers = Mock(return_value=wrappers)
    return manager


def build_purifier(
    hass: HomeAssistant, device_wrapper: WinixDeviceWrapper
) -> WinixPurifier:
    """Return a WinixPurifier instance."""

    device = WinixPurifier(device_wrapper, Mock())
    device.add_to_platform_start(hass, None, None)

    # Use unique_id as entity_id, this is required for async_update_ha_state
    device.entity_id = device.unique_id
    return device
