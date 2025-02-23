"""Winix Air Purfier Air QValue Sensor."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import logging
from typing import Any, Final

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import WINIX_DOMAIN
from .const import (
    ATTR_AIR_AQI,
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    ATTR_FILTER_HOUR,
    SENSOR_AIR_QVALUE,
    SENSOR_AQI,
    SENSOR_FILTER_LIFE,
    WINIX_DATA_COORDINATOR,
)
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager

_LOGGER = logging.getLogger(__name__)
TOTAL_FILTER_LIFE: Final = 6480  # 9 months


@dataclass(frozen=True, kw_only=True)
class WininxSensorEntityDescription(SensorEntityDescription):
    """Describe VeSync sensor entity."""

    value_fn: Callable[[dict[str, str]], StateType]
    extra_state_attributes_fn: Callable[[WinixDeviceWrapper], Mapping[str, Any] | None]


SENSOR_DESCRIPTIONS: tuple[WininxSensorEntityDescription, ...] = (
    WininxSensorEntityDescription(
        key=SENSOR_AIR_QVALUE,
        icon="mdi:cloud",
        name="Air QValue",
        native_unit_of_measurement="qv",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.get(ATTR_AIR_QVALUE),
        extra_state_attributes_fn=lambda state: get_air_quality_attr,
    ),
    WininxSensorEntityDescription(
        key=SENSOR_FILTER_LIFE,
        icon="mdi:air-filter",
        name="Filter Life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: get_filter_life,
        extra_state_attributes_fn=None,
    ),
    WininxSensorEntityDescription(
        key=SENSOR_AQI,
        icon="mdi:blur",
        name="AQI",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.get(ATTR_AIR_AQI),
        extra_state_attributes_fn=None,
    ),
)


def get_air_quality_attr(state: dict[str, str]) -> Mapping[str, Any] | None:
    """Get air quality attribute."""
    attributes = {ATTR_AIR_QUALITY: None}
    if state is not None:
        attributes[ATTR_AIR_QUALITY] = state.get(ATTR_AIR_QUALITY)

    return attributes


def get_filter_life(state: dict[str, str]) -> StateType:
    """Get filter life."""
    value = state.get(ATTR_FILTER_HOUR)
    if value is None:
        return None

    hours: int = int(value)
    if hours > TOTAL_FILTER_LIFE:
        _LOGGER.warning(
            "Reported filter life '%d' is more than max value '%d'",
            hours,
            TOTAL_FILTER_LIFE,
        )
        return None

    return int((TOTAL_FILTER_LIFE - hours) * 100 / TOTAL_FILTER_LIFE)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Winix sensors."""
    data = hass.data[WINIX_DOMAIN][entry.entry_id]
    manager: WinixManager = data[WINIX_DATA_COORDINATOR]

    entities = [
        WinixSensor(wrapper, manager, description)
        for description in SENSOR_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %s sensors", len(entities))


class WinixSensor(WinixEntity, SensorEntity):
    """Representation of a Winix Purifier sensor."""

    entity_description: WininxSensorEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WininxSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = (
            f"{SENSOR_DOMAIN}.{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""

        if self.entity_description.extra_state_attributes_fn is None:
            return None

        return self.entity_description.extra_state_attributes_fn(
            self._wrapper.get_state()
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        state = self._wrapper.get_state()
        if state is None:
            return None

        return self.entity_description.value_fn(state)
