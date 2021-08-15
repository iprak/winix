"""The Winix C545 Air Purifier component."""

import asyncio
from datetime import timedelta
import logging
from typing import List

from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client, discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_interval
import voluptuous as vol

from custom_components.winix.device_wrapper import WinixDeviceWrapper
from winix import WinixAccount, auth, cmd

from .const import DOMAIN, SERVICE_REFRESH_ACCESS

_LOGGER = logging.getLogger(__name__)
MIN_SCAN_INTERVAL = timedelta(seconds=30)
SUPPORTED_PLATFORMS = ["fan", "sensor"]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=MIN_SCAN_INTERVAL
                ): cv.time_period,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


class WinixManager:
    """Representation of the Winix device manager."""

    def __init__(self, hass: HomeAssistant, domain_config, scan_interval: int) -> None:
        """Initialize the manager."""
        self._device_wrappers: List[WinixDeviceWrapper] = None
        self._domain_config = domain_config
        self._hass = hass
        self._scan_interval = scan_interval

        # Not creating local configuration file which always results in updated configuration
        self._config = cmd.Configuration("")

    @property
    def scan_interval(self):
        """Return the scan interval."""
        return self._scan_interval

    def login(self) -> None:
        """Login and setup platforms."""
        config = self._config
        username = self._domain_config.get(CONF_USERNAME)
        password = self._domain_config.get(CONF_PASSWORD)

        try:
            config.cognito = auth.login(username, password)
            account = WinixAccount(config.cognito.access_token)
            account.register_user(username)
            account.check_access_token()
            config.devices = account.get_device_info_list()

            self._config = config
            device_stubs = self._config.devices

            _LOGGER.debug("Configuration initialized")

            self._hass.async_create_task(self.async_prepare_devices(device_stubs))
            self.setup_services()

        except Exception as err:
            _LOGGER.error(err)

    async def async_prepare_devices(self, device_stubs) -> None:
        """Create devices and setup platforms."""
        if device_stubs:
            self._device_wrappers = []
            client = aiohttp_client.async_get_clientsession(self._hass)

            for device_stub in device_stubs:
                self._device_wrappers.append(
                    WinixDeviceWrapper(client, device_stub, _LOGGER)
                )

            _LOGGER.info("Found %d purifiers", len(self._device_wrappers))
            self._hass.async_create_task(self.async_setup_platforms())

    async def async_setup_platforms(self) -> None:
        """Set up platforms."""
        if self.get_device_wrappers():
            # Get data once
            await self.async_update()

            for component in SUPPORTED_PLATFORMS:
                discovery.load_platform(
                    self._hass, component, DOMAIN, {}, self._domain_config
                )

            def update_devices(event_time):
                asyncio.run_coroutine_threadsafe(self.async_update(), self._hass.loop)

            async_track_time_interval(self._hass, update_devices, self._scan_interval)

    def setup_services(self) -> None:
        """Set up services."""
        self._hass.services.register(
            DOMAIN,
            SERVICE_REFRESH_ACCESS,
            self.handle_platform_services,
        )

    def handle_platform_services(self, call) -> None:
        """Handle common services."""
        service = call.service

        if self._config:
            if service == SERVICE_REFRESH_ACCESS:
                self._config.cognito = auth.refresh(
                    user_id=self._config.cognito.user_id,
                    refresh_token=self._config.cognito.refresh_token,
                )

                account = WinixAccount(self._config.cognito.access_token)
                account.check_access_token()
                _LOGGER.info("Access token refreshed")

    async def async_update(self, now=None) -> None:
        """Asynchronously update all the devices."""
        _LOGGER.info("Updating devices")
        for device in self._device_wrappers:
            await device.update()

    def get_device_wrappers(self) -> List[WinixDeviceWrapper]:
        """Return the device wrapper objects."""
        return self._device_wrappers
