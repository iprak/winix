"""Winix Air Purfier Air QValue Sensor"""

from datetime import timedelta
import logging

from homeassistant.components.sensor import DOMAIN
from homeassistant.helpers.entity import Entity
import voluptuous as vol

from . import DOMAIN as WINIX_DOMAIN, WinixDeviceWrapper, WinixManager
from .const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    manager: WinixManager = hass.data[WINIX_DOMAIN]

    entities = []
    for wrapper in manager.get_device_wrappers():
        entities.append(WinixPurifier(wrapper))

    async_add_entities(entities, False)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixPurifier(Entity):
    """Representation of a Winix Purifier air qValue sensor"""

    def __init__(self, wrapper: WinixDeviceWrapper) -> None:
        """Initialize the sensor."""
        self._wrapper = wrapper

        self._id = f"{DOMAIN}.{WINIX_DOMAIN}_qvalue_{wrapper.info.mac.lower()}"
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
        attributes = {ATTR_AIR_QUALITY: None}

        if self._state is not None:
            attributes[ATTR_AIR_QUALITY] = self._state.get(ATTR_AIR_QUALITY)

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
    def state(self):
        """Return the state of the sensor."""
        return None if self._state is None else self._state.get(ATTR_AIR_QVALUE)
