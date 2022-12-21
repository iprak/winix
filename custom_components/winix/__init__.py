"""The Winix Air Purifier component."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.winix.helpers import Helpers
from custom_components.winix.manager import WinixManager
from winix import auth

from .const import WINIX_AUTH_RESPONSE, WINIX_DATA_COORDINATOR, WINIX_DOMAIN, WINIX_NAME

_LOGGER = logging.getLogger(__name__)
SUPPORTED_PLATFORMS = [Platform.FAN, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Winix component."""

    hass.data.setdefault(WINIX_DOMAIN, {})
    user_input = entry.data

    auth_response_data = user_input.get(WINIX_AUTH_RESPONSE)
    auth_response = (
        auth_response_data
        if isinstance(auth_response_data, auth.WinixAuthResponse)
        else auth.WinixAuthResponse(**auth_response_data)
    )

    if not auth_response:
        Helpers.send_notification(
            hass,
            "async_setup_entry",
            WINIX_NAME,
            "No authentication data found. Please reconfigure the integration.",
        )
        return False

    # try:
    #     new_auth_response = await Helpers.async_refresh_auth(hass, auth_response)

    #     auth_response.access_token = new_auth_response.access_token
    #     auth_response.refresh_token = new_auth_response.refresh_token
    #     auth_response.id_token = new_auth_response.id_token

    # except AuthenticationError as err:
    #     # Raising ConfigEntryAuthFailed will automatically put the config entry in a
    #     # failure state and start a reauth flow.
    #     # https://developers.home-assistant.io/docs/integration_setup_failures/
    #     if err.error_code == "UserNotFoundException":
    #         raise ConfigEntryAuthFailed from err

    #     _LOGGER.warning("Unable to authenticate", exc_info=True)

    # except Exception as err:  # pylint: disable=broad-except
    #     _LOGGER.warning("Unable to authenticate", exc_info=True)
    #     raise ConfigEntryNotReady(
    #         "Unable to authenticate. Sensi integration is not ready."
    #     ) from err

    scan_interval = 30
    manager = WinixManager(hass, auth_response, scan_interval)

    if await manager.async_prepare_devices_wrappers():
        # await manager.async_setup_updates()
        await manager.async_config_entry_first_refresh()

        hass.data[WINIX_DOMAIN][entry.entry_id] = {WINIX_DATA_COORDINATOR: manager}
        await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)
    else:
        Helpers.send_notification(
            hass, "async_setup_entry", WINIX_NAME, "Unable to obtain device data."
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # pylint: disable=unused-argument
    """Unload a config entry."""
    hass.data.pop(WINIX_DOMAIN)
