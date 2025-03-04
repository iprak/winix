"""The Winix C545 Air Purifier component."""

from __future__ import annotations

from datetime import timedelta
import logging

from winix import auth

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import WINIX_DOMAIN
from .device_wrapper import WinixDeviceWrapper
from .helpers import Helpers

_LOGGER = logging.getLogger(__name__)

# category_keys = {
#     "power": "A02",
#     "mode": "A03",
#     "airflow": "A04",
#     "aqi": "A05",
#     "plasma": "A07",
#     "filter_hour": "A21",
#     "air_quality": "S07",
#     "air_qvalue": "S08",
#     "ambient_light": "S14",
# }


class WinixEntity(CoordinatorEntity):
    """Represents a Winix entity."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by Winix"

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the Winix entity."""
        super().__init__(coordinator)

        device_stub = wrapper.device_stub

        self._mac = device_stub.mac.lower()
        self._wrapper = wrapper

        self._attr_device_info: DeviceInfo = {
            "identifiers": {(WINIX_DOMAIN, self._mac)},
            "name": f"Winix {device_stub.alias}",
            "manufacturer": "Winix",
            "model": device_stub.model,
            "sw_version": device_stub.sw_version,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        state = self._wrapper.get_state()
        return state is not None


class WinixManager(DataUpdateCoordinator):
    """Representation of the Winix device manager."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_response: auth.WinixAuthResponse,
        scan_interval: int,
    ) -> None:
        """Initialize the manager."""

        # Always initialize _device_wrappers in case async_prepare_devices_wrappers
        # was not invoked.
        self._device_wrappers: list[WinixDeviceWrapper] = []
        self._auth_response = auth_response

        super().__init__(
            hass,
            _LOGGER,
            name="WinixManager",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> None:
        """Fetch the latest data from the source. This overrides the method in DataUpdateCoordinator."""
        await self.async_update()

    async def async_prepare_devices_wrappers(self) -> None:
        """Prepare device wrappers.

        Raises WinixException.
        """

        self._device_wrappers = []  # Reset device_stubs

        device_stubs = await Helpers.async_get_device_stubs(
            self.hass, self._auth_response.access_token
        )

        if device_stubs:
            client = aiohttp_client.async_get_clientsession(self.hass)

            for device_stub in device_stubs:
                self._device_wrappers.append(
                    WinixDeviceWrapper(client, device_stub, _LOGGER)
                )

            _LOGGER.info("%d purifiers found", len(self._device_wrappers))
        else:
            _LOGGER.info("No purifiers found")

    async def async_update(self, now=None) -> None:
        """Asynchronously update all the devices."""
        _LOGGER.info("Updating devices")
        for device_wrapper in self._device_wrappers:
            await device_wrapper.update()

    def get_device_wrappers(self) -> list[WinixDeviceWrapper]:
        """Return the device wrapper objects."""
        return self._device_wrappers
