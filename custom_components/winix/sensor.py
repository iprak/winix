"""Winix C545 Air Purfier Air QValue Sensor."""

from collections.abc import Mapping
from datetime import timedelta
import logging
from typing import Any, Union

from homeassistant.components.sensor import DOMAIN
from homeassistant.helpers.entity import DeviceInfo, Entity

from custom_components.winix.device_wrapper import WinixDeviceWrapper
from custom_components.winix.manager import WinixManager

from . import DOMAIN as WINIX_DOMAIN
from .const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)
ICON = "mdi:cloud"
UNIT_OF_MEASUREMENT = "QV"


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Winix sensor platform."""
    manager: WinixManager = hass.data[WINIX_DOMAIN]

    entities = []
    for wrapper in manager.get_device_wrappers():
        entities.append(WinixSensor(wrapper))

    async_add_entities(entities, False)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixSensor(Entity):
    """Representation of a Winix Purifier air qValue sensor."""

    def __init__(self, wrapper: WinixDeviceWrapper) -> None:
        """Initialize the sensor."""
        self._wrapper = wrapper

        self._unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_qvalue_{wrapper.info.mac.lower()}"
        self._name = f"Winix {self._wrapper.info.alias}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        state = self._wrapper.get_state()
        return state is not None

    @property
    def extra_state_attributes(self) -> Union[Mapping[str, Any], None]:
        """Return the state attributes."""
        attributes = {ATTR_AIR_QUALITY: None}

        state = self._wrapper.get_state()
        if state is not None:
            attributes[ATTR_AIR_QUALITY] = state.get(ATTR_AIR_QUALITY)

        return attributes

    @property
    def unique_id(self) -> Union[str, None]:
        """Return the unique id of the switch."""
        return self._unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device specific attributes."""
        return {
            "identifiers": {(WINIX_DOMAIN, self._wrapper.info.mac.lower())},
            "name": self._name,
        }

    @property
    def icon(self) -> str:
        """Return the icon to use for device if any."""
        return ICON

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def state(self) -> Union[str, None]:
        """Return the state of the sensor."""
        state = self._wrapper.get_state()
        return None if state is None else state.get(ATTR_AIR_QVALUE)

    @property
    def unit_of_measurement(self) -> Union[str, None]:
        """Return the unit of measurement of this entity, if any."""
        return UNIT_OF_MEASUREMENT
