"""Test component setup."""

from datetime import timedelta
from unittest.mock import Mock, patch

from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
import pytest

from custom_components.winix import (
    MIN_SCAN_INTERVAL,
    WinixManager,
    async_setup,
    manager,
)
from custom_components.winix.const import DOMAIN


@pytest.mark.parametrize(
    "scan_interval, expected_scan_interval",
    [
        (MIN_SCAN_INTERVAL, MIN_SCAN_INTERVAL),
        (MIN_SCAN_INTERVAL - timedelta(minutes=15), MIN_SCAN_INTERVAL),
    ],
)
async def test_async_setup(hass, scan_interval, expected_scan_interval):
    """Test scan interval."""
    config = {DOMAIN: {CONF_SCAN_INTERVAL: scan_interval}}
    await async_setup(hass, config)
    wininx_manager = hass.data[DOMAIN]
    assert wininx_manager.scan_interval == expected_scan_interval


def test_manager_login(hass):
    """Test login."""
    domain_config = {CONF_USERNAME: "user", CONF_PASSWORD: "password"}
    wininx_manager = WinixManager(hass, domain_config, MIN_SCAN_INTERVAL)

    wininx_manager.setup_services = mock_setup_services = Mock()
    hass.async_create_task = mock_async_create_task = Mock()

    with patch("winix.WinixAccount.register_user") as mock_register_user, patch(
        "winix.WinixAccount.check_access_token"
    ) as mock_check_access_token, patch(
        "winix.WinixAccount.get_device_info_list"
    ) as mock_get_device_info_list, patch.object(
        manager.auth, "login"
    ) as mock_winix_login:

        wininx_manager.login()

        assert mock_register_user.call_count == 1
        assert mock_check_access_token.call_count == 1
        assert mock_winix_login.call_count == 1
        assert mock_get_device_info_list.call_count == 1

        assert mock_async_create_task.call_count == 1
        assert mock_setup_services.call_count == 1


async def test_async_prepare_devices(hass):
    """Test device creation."""
    domain_config = {CONF_USERNAME: "user", CONF_PASSWORD: "password"}
    wininx_manager = WinixManager(hass, domain_config, MIN_SCAN_INTERVAL)

    device_stub = Mock()
    device_stubs = [device_stub]

    wininx_manager.async_setup_platforms = mock_async_setup_platforms = Mock()

    with patch.object(manager.aiohttp_client, "async_get_clientsession"):
        await wininx_manager.async_prepare_devices(device_stubs)
        await hass.async_block_till_done()

        assert mock_async_setup_platforms.call_count == 1
