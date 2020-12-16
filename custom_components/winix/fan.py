"""Winix Air Purfier Device"""

import asyncio
from datetime import timedelta
import logging
from typing import Any, Callable, Dict, Optional

from homeassistant.components.fan import (
    DOMAIN,
    PLATFORM_SCHEMA,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

from . import WinixDeviceWrapper, WinixManager
from .const import (
    ATTR_AIRFLOW,
    ATTR_FILTER_REPLACEMENT_DATE,
    ATTR_LOCATION,
    ATTR_POWER,
    DOMAIN as WINIX_DOMAIN,
    SERVICES,
    SPEED_HIGH,
    SPEED_LIST,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SPEED_SLEEP,
    SPEED_TURBO,
    WINIX_DATA_KEY,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)


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

    async def async_service_handler(service):
        """Service handler."""
        method = "async_" + service.service
        _LOGGER.debug("Service '%s' invoked", service)

        # The defined services do not accept any additional parameters
        params = {}

        entity_ids = service.data.get(ATTR_ENTITY_ID)
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
    """Representation of a Winix Purifier device"""

    def __init__(self, wrapper: WinixDeviceWrapper) -> None:
        """Initialize the device."""
        self._wrapper = wrapper

        self._id = f"{DOMAIN}.{WINIX_DOMAIN}_{wrapper.info.mac.lower()}"
        self._name = f"Winix {self._wrapper.info.alias}"
        self._state = None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        self._state = self._wrapper.get_state()
        return not self._state is None

    @property
    def device_state_attributes(self) -> None:
        """Return the state attributes."""
        attributes = {}

        wrapperState = self._state
        if wrapperState is not None:
            for f, v in wrapperState.items():
                # The power attribute is the entity state, so skip it
                if not f == ATTR_POWER:
                    attributes[f] = v

        attributes[ATTR_LOCATION] = self._wrapper.info.location_code
        attributes[
            ATTR_FILTER_REPLACEMENT_DATE
        ] = self._wrapper.info.filter_replace_date

        return attributes

    @property
    def entity_id(self) -> str:
        """Return the unique id of the switch."""
        return self._id

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._wrapper.is_on()

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return SPEED_LIST

    @property
    def speed(self):
        """Return the current speed."""
        return None if self._state is None else self._state.get(ATTR_AIRFLOW)

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    async def async_turn_on(self, speed: Optional[str] = None, **kwargs):
        """Turn the fan on."""
        if speed:
            await self._wrapper.async_set_speed(speed)
        else:
            await self._wrapper.async_ensure_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._wrapper.async_turn_off()

    async def async_set_speed(self, speed: str):
        """Set the speed of the fan."""
        await self._wrapper.async_set_speed(speed)

    async def async_plasmawave_on(self):
        """Turn plasma wave on."""
        await self._wrapper.async_plasmawave_on()

    async def async_plasmawave_off(self):
        """Turn plasma wave off."""
        await self._wrapper.async_plasmawave_off()