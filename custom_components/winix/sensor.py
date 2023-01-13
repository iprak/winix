"""Winix Air Purfier Air QValue Sensor."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any, Union

from homeassistant.components.sensor import DOMAIN, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from custom_components.winix.device_wrapper import WinixDeviceWrapper
from custom_components.winix.manager import WinixEntity, WinixManager

from . import WINIX_DOMAIN
from .const import (
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    ATTR_FILTER_HOUR,
    WINIX_DATA_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)
TOTAL_FILTER_LIFE = 6480  # 9 months


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Winix sensors."""
    data = hass.data[WINIX_DOMAIN][entry.entry_id]
    manager: WinixManager = data[WINIX_DATA_COORDINATOR]
    entities = [
        WinixAirQualitySensor(wrapper, manager)
        for wrapper in manager.get_device_wrappers()
    ] + [
        WinixFilterLifeSensor(wrapper, manager)
        for wrapper in manager.get_device_wrappers()
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixAirQualitySensor(WinixEntity, SensorEntity):
    """Representation of a Winix Purifier air qValue sensor."""

    _attr_icon = "mdi:cloud"
    _attr_name = "Air Quality"
    _attr_native_unit_of_measurement = "QV"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_qvalue_{self._mac}"

    @property
    def extra_state_attributes(self) -> Union[Mapping[str, Any], None]:
        """Return the state attributes."""
        attributes = {ATTR_AIR_QUALITY: None}

        state = self._wrapper.get_state()
        if state is not None:
            attributes[ATTR_AIR_QUALITY] = state.get(ATTR_AIR_QUALITY)

        return attributes

    @property
    def native_value(self) -> Union[str, None]:
        """Return the state of the sensor."""
        state = self._wrapper.get_state()
        return None if state is None else state.get(ATTR_AIR_QVALUE)


class WinixFilterLifeSensor(WinixEntity, SensorEntity):
    """Representation of a Winix Purifier fiter life sensor."""

    _attr_icon = "mdi:air-filter"
    _attr_name = "Filter Life"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = f"{DOMAIN}.{WINIX_DOMAIN}_filter_life_{self._mac}"

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        state = self._wrapper.get_state()
        if state is None:
            return None
        hours: int = state.get(ATTR_FILTER_HOUR)
        if hours > TOTAL_FILTER_LIFE:
            _LOGGER.warning(
                "Reported filter life '%d' is more than max value '%d'.",
                hours,
                TOTAL_FILTER_LIFE,
            )
            return None

        return int((TOTAL_FILTER_LIFE - hours) * 100 / TOTAL_FILTER_LIFE)
