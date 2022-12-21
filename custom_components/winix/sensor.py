"""Winix Air Purfier Air QValue Sensor."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Union

from homeassistant.components.sensor import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.winix.device_wrapper import WinixDeviceWrapper
from custom_components.winix.manager import WinixEntity, WinixManager

from . import WINIX_DOMAIN
from .const import ATTR_AIR_QUALITY, ATTR_AIR_QVALUE, WINIX_DATA_COORDINATOR

_LOGGER = logging.getLogger(__name__)
ICON = "mdi:cloud"
UNIT_OF_MEASUREMENT = "QV"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Winix sensors."""
    data = hass.data[WINIX_DOMAIN][entry.entry_id]
    manager: WinixManager = data[WINIX_DATA_COORDINATOR]
    entities = [
        WinixSensor(wrapper, manager) for wrapper in manager.get_device_wrappers()
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixSensor(WinixEntity, Entity):
    """Representation of a Winix Purifier air qValue sensor."""

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self._unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_qvalue_{self._mac}"

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return self._unique_id

    @property
    def extra_state_attributes(self) -> Union[Mapping[str, Any], None]:
        """Return the state attributes."""
        attributes = {ATTR_AIR_QUALITY: None}

        state = self._wrapper.get_state()
        if state is not None:
            attributes[ATTR_AIR_QUALITY] = state.get(ATTR_AIR_QUALITY)

        return attributes

    @property
    def icon(self) -> str:
        """Return the icon to use for device if any."""
        return ICON

    @property
    def state(self) -> Union[str, None]:
        """Return the state of the sensor."""
        state = self._wrapper.get_state()
        return None if state is None else state.get(ATTR_AIR_QVALUE)

    @property
    def unit_of_measurement(self) -> Union[str, None]:
        """Return the unit of measurement of this entity, if any."""
        return UNIT_OF_MEASUREMENT
