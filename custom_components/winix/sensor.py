"""Winix sensor entities (air quality, filter life)."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfDensity, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import (
    ATTR_AIR_AQI,
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    ATTR_FILTER_HOUR,
    ATTR_PM25,
    LOGGER,
    SENSOR_AIR_QVALUE,
    SENSOR_AQI,
    SENSOR_FILTER_LIFE,
    SENSOR_MAX_FILTER_LIFE,
    SENSOR_PM25,
)
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager


def get_air_quality_attr(
    state: dict[str, str], wrapper: WinixDeviceWrapper
) -> dict[str, Any]:
    """Get air quality attribute."""

    return {ATTR_AIR_QUALITY: state.get(ATTR_AIR_QUALITY)}


def get_filter_life(state: dict[str, str], wrapper: WinixDeviceWrapper) -> int | None:
    """Get filter life percentage."""

    return get_filter_life_percentage(
        state.get(ATTR_FILTER_HOUR), wrapper.filter_max_life
    )


def get_filter_life_percentage(hours: str | None, max_life_hours: int) -> int | None:
    """Get filter life percentage."""

    if hours is None:
        return None

    hours = int(hours)
    if max_life_hours < hours:
        return None

    return round((max_life_hours - hours) * 100 / max_life_hours)


@dataclass(frozen=True, kw_only=True)
class WinixSensorEntityDescription(SensorEntityDescription):
    """Describe Winix sensor entity."""

    value_fn: Callable[[dict[str, str], WinixDeviceWrapper], StateType]
    extra_state_attributes_fn: Callable[[dict[str, str]], dict[str, Any]] | None = None
    exists_fn: Callable[[WinixDeviceWrapper], bool] = field(default=lambda _: True)


SENSOR_DESCRIPTIONS: tuple[WinixSensorEntityDescription, ...] = (
    WinixSensorEntityDescription(
        extra_state_attributes_fn=get_air_quality_attr,
        icon="mdi:cloud",
        key=SENSOR_AIR_QVALUE,
        translation_key="air_qvalue",
        native_unit_of_measurement="qv",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state, wrapper: state.get(ATTR_AIR_QVALUE),
        exists_fn=lambda device: device.is_air_purifier,
    ),
    WinixSensorEntityDescription(
        icon="mdi:air-filter",
        key=SENSOR_FILTER_LIFE,
        translation_key="filter_life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=get_filter_life,
        exists_fn=lambda device: device.is_air_purifier,
    ),
    WinixSensorEntityDescription(
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        key=SENSOR_MAX_FILTER_LIFE,
        translation_key="max_filter_life",
        value_fn=lambda state, wrapper: wrapper.filter_max_life,
        exists_fn=lambda device: device.is_air_purifier,
    ),
    WinixSensorEntityDescription(
        icon="mdi:blur",
        key=SENSOR_AQI,
        translation_key="aqi",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state, wrapper: state.get(ATTR_AIR_AQI),
        exists_fn=lambda device: device.is_air_purifier,
    ),
    WinixSensorEntityDescription(
        device_class=SensorDeviceClass.PM25,
        key=SENSOR_PM25,
        translation_key="pm2_5",
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        value_fn=lambda state, wrapper: state.get(ATTR_PM25),
        exists_fn=lambda device: (
            device.is_air_purifier and device.features.supports_pm25
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Winix sensors."""
    manager = entry.runtime_data

    entities = [
        WinixSensor(wrapper, manager, description)
        for description in SENSOR_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s sensors", len(entities))


class WinixSensor(WinixEntity, SensorEntity):
    """Representation of a Winix Purifier sensor."""

    entity_description: WinixSensorEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WinixSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        # Legacy format retained for existing installations; new entity types
        # should use f"<key>_{self._mac}" without the platform/winix prefix.
        self._attr_unique_id = ENTITY_ID_FORMAT.format(
            f"{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""

        if self.entity_description.extra_state_attributes_fn is None:
            return None

        state = self.device_wrapper.get_state()
        return (
            None
            if state is None
            else self.entity_description.extra_state_attributes_fn(
                state, self.device_wrapper
            )
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        state = self.device_wrapper.get_state()
        return (
            None
            if state is None
            else self.entity_description.value_fn(state, self.device_wrapper)
        )
