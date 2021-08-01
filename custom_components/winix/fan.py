"""Winix C545 Air Purifier Device."""

import asyncio
from datetime import timedelta
import logging
from typing import Any, Callable, Optional

from homeassistant.components.fan import (
    DOMAIN,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.const import ATTR_ENTITY_ID
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)
import voluptuous as vol

from . import WinixDeviceWrapper, WinixManager
from .const import (
    ATTR_AIRFLOW,
    ATTR_FILTER_REPLACEMENT_DATE,
    ATTR_LOCATION,
    ATTR_POWER,
    DOMAIN as WINIX_DOMAIN,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
    SERVICES,
    WINIX_DATA_KEY,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)

# pylint: disable=unused-argument
async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the Winix air purifiers."""

    # Create WINIX_DATA_KEY entry if not present
    if WINIX_DATA_KEY not in hass.data:
        hass.data[WINIX_DATA_KEY] = []

    manager: WinixManager = hass.data[WINIX_DOMAIN]

    entities = []
    for wrapper in manager.get_device_wrappers():
        entities.append(WinixPurifier(wrapper))

    # Keep track of etities in WINIX_DATA_KEY storage area for service processing
    hass.data[WINIX_DATA_KEY].extend(entities)
    async_add_entities(entities, False)

    async def async_service_handler(service_call):
        """Service handler."""
        method = "async_" + service_call.service
        _LOGGER.debug("Service '%s' invoked", service_call.service)

        # The defined services do not accept any additional parameters
        params = {}

        entity_ids = service_call.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                entity
                for entity in hass.data[WINIX_DATA_KEY]
                if entity.entity_id in entity_ids
            ]
        else:
            devices = hass.data[WINIX_DATA_KEY]

        state_update_tasks = []
        for device in devices:
            if not hasattr(device, method):
                continue

            await getattr(device, method)(**params)
            state_update_tasks.append(device.async_update_ha_state(True))

        if state_update_tasks:
            # Update device states in HA
            await asyncio.wait(state_update_tasks)

    for service in SERVICES:
        hass.services.async_register(
            WINIX_DOMAIN,
            service,
            async_service_handler,
            schema=vol.Schema({ATTR_ENTITY_ID: cv.entity_ids}),
        )

    _LOGGER.info("Added %s Winix fans", len(entities))


class WinixPurifier(FanEntity):
    """Representation of a Winix Purifier device."""

    def __init__(self, wrapper: WinixDeviceWrapper) -> None:
        """Initialize the device."""
        self._wrapper = wrapper

        self._unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_{wrapper.info.mac.lower()}"
        self._name = f"Winix {self._wrapper.info.alias}"
        self._state = None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        self._state = self._wrapper.get_state()
        return self._state is not None

    @property
    def device_state_attributes(self) -> None:
        """Return the state attributes."""
        attributes = {}

        if self._state is not None:
            for key, value in self._state.items():
                # The power attribute is the entity state, so skip it
                if not key == ATTR_POWER:
                    attributes[key] = value

        attributes[ATTR_LOCATION] = self._wrapper.info.location_code
        attributes[
            ATTR_FILTER_REPLACEMENT_DATE
        ] = self._wrapper.info.filter_replace_date

        return attributes

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return self._unique_id

    @property
    def device_info(self):
        """Return device specific attributes."""
        return {
            "identifiers": {(WINIX_DOMAIN, self._wrapper.info.mac.lower())},
            "name": self._name,
        }

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._wrapper.is_on

    @property
    def percentage(self):
        """Return the current speed percentage."""
        if self._state is None:
            return None
        elif self._wrapper.is_sleep or self._wrapper.is_auto:
            return None
        else:
            return ordered_list_item_to_percentage(
                ORDERED_NAMED_FAN_SPEEDS, self._state.get(ATTR_AIRFLOW)
            )

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        if self._state is None:
            return None
        if self._wrapper.is_sleep:
            return PRESET_MODE_SLEEP
        if self._wrapper.is_auto:
            return PRESET_MODE_AUTO
        if self._wrapper.is_manual:
            return (
                PRESET_MODE_MANUAL_PLASMA
                if self._wrapper.is_plasma_on
                else PRESET_MODE_MANUAL
            )
        else:
            return None

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return PRESET_MODES

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    # https://developers.home-assistant.io/docs/core/entity/fan/

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            await self._wrapper.async_set_speed(
                percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
            )

    async def async_turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the purifier."""
        if percentage:
            await self.async_set_percentage(percentage)
            return
        if preset_mode:
            await self._wrapper.async_set_preset_mode(preset_mode)
        else:
            await self._wrapper.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the purifier."""
        await self._wrapper.async_turn_off()

    async def async_plasmawave_on(self) -> None:
        """Turn on plasma wave."""
        await self._wrapper.async_plasmawave_on()

    async def async_plasmawave_off(self) -> None:
        """Turn off plasma wave."""
        await self._wrapper.async_plasmawave_off()

    async def async_plasmawave_toggle(self) -> None:
        """Toggle plasma wave."""

        if self._wrapper.is_plasma_on:
            await self._wrapper.async_plasmawave_off()
        else:
            await self._wrapper.async_plasmawave_on()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self._wrapper.async_set_preset_mode(preset_mode)
