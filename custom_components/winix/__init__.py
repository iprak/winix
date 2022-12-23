"""The Winix Air Purifier component."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.winix.helpers import Helpers, WinixException
from custom_components.winix.manager import WinixManager
from winix import auth

from .const import WINIX_AUTH_RESPONSE, WINIX_DATA_COORDINATOR, WINIX_DOMAIN, WINIX_NAME

_LOGGER = logging.getLogger(__name__)
SUPPORTED_PLATFORMS = [Platform.FAN, Platform.SENSOR]
DEFAULT_SCAN_INTERVAL: Final = 30


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

    manager = WinixManager(hass, auth_response, DEFAULT_SCAN_INTERVAL)
    try_login_once = True
    try_prepare_devices_wrappers = True

    while try_prepare_devices_wrappers:
        try:
            await manager.async_prepare_devices_wrappers()
            break
        except WinixException as err:
            # 900:MULTI LOGIN: Same credentials were used to login elwsewhere. We need to
            # login again and get new tokens.
            # 400:The user is not valid.
            if try_login_once and err.result_code in ("900", "400"):
                try_login_once = False

                try:
                    new_auth_response = await Helpers.async_login(
                        hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    )

                    # Copy over new values
                    _LOGGER.debug(
                        "access_token %s",
                        "changed"
                        if auth_response.access_token != new_auth_response.access_token
                        else "unchanged",
                    )
                    _LOGGER.debug(
                        "refresh_token %s",
                        "changed"
                        if auth_response.refresh_token
                        != new_auth_response.refresh_token
                        else "unchanged",
                    )
                    _LOGGER.debug(
                        "id_token %s",
                        "changed"
                        if auth_response.id_token != new_auth_response.id_token
                        else "unchanged",
                    )

                    auth_response.access_token = new_auth_response.access_token
                    auth_response.refresh_token = new_auth_response.refresh_token
                    auth_response.id_token = new_auth_response.id_token

                    # Update tokens into entry.data
                    hass.config_entries.async_update_entry(
                        entry,
                        data={**user_input, WINIX_AUTH_RESPONSE: auth_response},
                    )

                except WinixException as login_err:
                    if login_err.result_code == "UserNotFoundException":
                        raise ConfigEntryAuthFailed(
                            "Wininx reported multi login"
                        ) from login_err

                    _LOGGER.error(
                        "Unable to log in. Device access previously failed with `%s`.",
                        str(err),
                        exc_info=True,
                    )
                    raise ConfigEntryNotReady("Unable to authenticate.") from login_err
            else:
                _LOGGER.error(
                    "async_prepare_devices_wrappers failed with `%s`.", str(err)
                )
                try_prepare_devices_wrappers = False

                # ConfigEntryNotReady will cause async_setup_entry to be invoked in background.
                raise ConfigEntryNotReady("Unable to access device data.") from err

    await manager.async_config_entry_first_refresh()

    hass.data[WINIX_DOMAIN][entry.entry_id] = {WINIX_DATA_COORDINATOR: manager}
    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # pylint: disable=unused-argument
    """Unload a config entry."""
    hass.data.pop(WINIX_DOMAIN)
