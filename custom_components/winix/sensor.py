"""Winix C545 Air Purfier Air QValue Sensor."""

from datetime import timedelta
import logging

from homeassistant.components.sensor import DOMAIN
from homeassistant.helpers.entity import Entity

from . import DOMAIN as WINIX_DOMAIN, WinixDeviceWrapper, WinixManager
from .const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)

# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Winix sensor platform."""
    manager: WinixManager = hass.data[WINIX_DOMAIN]

    entities = []
    for wrapper in manager.get_device_wrappers():
        entities.append(WinixPurifier(wrapper))

    async_add_entities(entities, False)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixPurifier(Entity):
    """Representation of a Winix Purifier air qValue sensor."""

    def __init__(self, wrapper: WinixDeviceWrapper) -> None:
        """Initialize the sensor."""
        self._wrapper = wrapper

        self._unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_qvalue_{wrapper.info.mac.lower()}"
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
        attributes = {ATTR_AIR_QUALITY: None}

        if self._state is not None:
            attributes[ATTR_AIR_QUALITY] = self._state.get(ATTR_AIR_QUALITY)

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
    def icon(self):
        """Return the icon to use for device if any."""
        return "mdi:cloud"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return None if self._state is None else self._state.get(ATTR_AIR_QVALUE)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "QV"
