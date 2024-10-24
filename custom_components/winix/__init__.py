"""The Winix Air Purifier component."""

from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Final

from awesomeversion import AwesomeVersion
from winix import auth

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    STATE_UNAVAILABLE,
    Platform,
    __version__,
)
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import (
    FAN_SERVICES,
    SERVICE_REMOVE_STALE_ENTITIES,
    WINIX_AUTH_RESPONSE,
    WINIX_DATA_COORDINATOR,
    WINIX_DOMAIN,
    WINIX_NAME,
    __min_ha_version__,
)
from .helpers import Helpers, WinixException
from .manager import WinixManager

_LOGGER = logging.getLogger(__name__)
SUPPORTED_PLATFORMS = [Platform.FAN, Platform.SENSOR]
DEFAULT_SCAN_INTERVAL: Final = 30


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the Winix component."""

    if not is_valid_ha_version():
        msg = (
            "This integration require at least HomeAssistant version "
            f" {__min_ha_version__}, you are running version {__version__}."
            " Please upgrade HomeAssistant to continue use this integration."
        )

        _LOGGER.warning(msg)
        persistent_notification.async_create(
            hass, msg, WINIX_NAME, f"{WINIX_DOMAIN}.inv_ha_version"
        )
        return False

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

                    _LOGGER.exception(
                        "Unable to log in. Device access previously failed"
                    )
                    raise ConfigEntryNotReady("Unable to authenticate.") from login_err
            else:
                try_prepare_devices_wrappers = False

                # ConfigEntryNotReady will cause async_setup_entry to be invoked in background.
                raise ConfigEntryNotReady("Unable to access device data.") from err

    await manager.async_config_entry_first_refresh()

    hass.data[WINIX_DOMAIN][entry.entry_id] = {WINIX_DATA_COORDINATOR: manager}
    await hass.config_entries.async_forward_entry_setups(entry, SUPPORTED_PLATFORMS)

    def remove_stale_entities(call: ServiceCall) -> None:
        """Remove stale entities."""
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        # Using set to avoid duplicates
        entity_ids = set()
        device_ids = set()

        for state in hass.states.async_all(SUPPORTED_PLATFORMS):
            entity_id = state.entity_id
            entity = entity_registry.async_get(entity_id)

            if entity.unique_id.startswith(f"{entity.domain}.{WINIX_DOMAIN}_"):
                device_id = entity.device_id
                device = device_registry.async_get(device_id)

                if state.state == STATE_UNAVAILABLE or not device:
                    entity_ids.add(entity_id)
                    device_ids.add(device_id)

        if entity_ids:
            hass.add_job(
                async_remove, entity_registry, device_registry, entity_ids, device_ids
            )
        else:
            _LOGGER.debug("Nothing to remove")

    hass.services.async_register(
        WINIX_DOMAIN, SERVICE_REMOVE_STALE_ENTITIES, remove_stale_entities
    )

    return True


@callback
def async_remove(
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    entity_ids: Iterable[str],
    device_ids: Iterable[str],
) -> None:
    """Remove devices and entities."""
    for entity_id in entity_ids:
        entity_registry.async_remove(entity_id)
        _LOGGER.debug("Removing entity %s", entity_id)

    for device_id in device_ids:
        device_registry.async_remove_device(device_id)
        _LOGGER.debug("Removing device %s", device_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SUPPORTED_PLATFORMS
    )
    if unload_ok:
        hass.data.pop(WINIX_DOMAIN)

    loaded_entries = [
        entry
        for entry in hass.config_entries.async_entries(WINIX_DOMAIN)
        if entry.state == ConfigEntryState.LOADED
    ]
    if len(loaded_entries) == 1:
        # If this is the last loaded instance, then unregister services
        hass.services.async_remove(WINIX_DOMAIN, SERVICE_REMOVE_STALE_ENTITIES)

        for service_name in FAN_SERVICES:
            hass.services.async_remove(WINIX_DOMAIN, service_name)

    return unload_ok


def is_valid_ha_version() -> bool:
    """Check if HA version is valid for this integration."""
    return AwesomeVersion(__version__) >= AwesomeVersion(__min_ha_version__)
