"""The Winix C545 Air Purifier component."""

from __future__ import annotations

from datetime import timedelta

from winix import WinixAccount, auth

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import LOGGER, WINIX_DOMAIN
from .device_wrapper import WinixDeviceWrapper
from .helpers import Helpers

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
        self.device_wrapper = wrapper

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
        state = self.device_wrapper.get_state()
        return state is not None


class WinixManager(DataUpdateCoordinator):
    """Representation of the Winix device manager."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        auth_response: auth.WinixAuthResponse,
        scan_interval: int,
        client,
    ) -> None:
        """Initialize the manager."""

        # Always initialize _device_wrappers in case async_prepare_devices_wrappers
        # was not invoked.
        self._device_wrappers: list[WinixDeviceWrapper] = []
        self._auth_response = auth_response
        self._client = client

        super().__init__(
            hass,
            LOGGER,
            name="WinixManager",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )

    async def _async_update_data(self) -> None:
        """Fetch the latest data from the source. This overrides the method in DataUpdateCoordinator."""
        await self.async_update()

    async def prepare_devices_wrappers(self, access_token: str = "") -> None:
        """Prepare device wrappers.

        Raises WinixException.
        """
        self._device_wrappers = []  # Reset device_stubs

        token = access_token or self._auth_response.access_token
        uuid = WinixAccount(token).get_uuid()
        device_stubs = await Helpers.get_device_stubs(self._client, token, uuid)

        if device_stubs:
            for device_stub in device_stubs:
                filter_alarm_duration = await Helpers.get_filter_alarm_duration(
                    self._client, token, uuid, device_stub.id
                )
                self._device_wrappers.append(
                    WinixDeviceWrapper(
                        self._client, device_stub, filter_alarm_duration, LOGGER
                    )
                )

            LOGGER.info("%d purifiers found", len(self._device_wrappers))
        else:
            LOGGER.info("No purifiers found")

    async def async_update(self, now=None) -> None:
        """Asynchronously update all the devices."""
        LOGGER.info("Updating devices")
        for device_wrapper in self._device_wrappers:
            await device_wrapper.update()

    def get_device_wrappers(self) -> list[WinixDeviceWrapper]:
        """Return the device wrapper objects."""
        return self._device_wrappers
