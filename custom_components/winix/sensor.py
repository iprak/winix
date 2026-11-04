"""Winix sensor entities."""

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
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import (
    ATTR_FILTER_HOUR,
    ATTR_FILTER_REPLACEMENT_DATE,
    ATTR_OPERATING_HOURS,
    LOGGER,
    SENSOR_FILTER_LIFE,
    SENSOR_MAX_FILTER_LIFE,
)
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager
from .model import EnumSensorInfo, SensorInfo


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


def get_operating_time_attr(
    state: dict[str, str], wrapper: WinixDeviceWrapper
) -> dict[str, StateType]:
    """Get operating hours."""

    return {
        ATTR_FILTER_REPLACEMENT_DATE: wrapper.device_stub.filter_replace_date,
        ATTR_OPERATING_HOURS: state.get(ATTR_FILTER_HOUR),
    }


@dataclass(frozen=True, kw_only=True)
class WinixSensorEntityDescription(SensorEntityDescription):
    """Describe Winix sensor entity."""

    value_fn: Callable[[dict[str, str], WinixDeviceWrapper], StateType] | None = None
    extra_state_attributes_fn: (
        Callable[[dict[str, str], WinixDeviceWrapper], dict[str, StateType]] | None
    ) = None
    exists_fn: Callable[[WinixDeviceWrapper], bool] = field(default=lambda _: True)


SENSOR_DESCRIPTIONS: tuple[WinixSensorEntityDescription, ...] = (
    WinixSensorEntityDescription(
        key=SENSOR_FILTER_LIFE,
        translation_key="filter_life",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=get_filter_life,
        exists_fn=lambda device: device.is_air_purifier,
        extra_state_attributes_fn=get_operating_time_attr,
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Winix sensors."""
    manager = entry.runtime_data

    entities = []

    for wrapper in manager.get_device_wrappers():
        sensors = manager.models.get_sensors(wrapper.device_stub.model_id)

        # A model profile lists every sensor the model can have, but some units
        # leave attributes out of their payload (e.g. AM90 sends S07 but not S08
        # or S14). Skip those, unless there was no payload to judge by.
        if raw_state := wrapper.get_raw_state():
            sensors = [sensor for sensor in sensors if sensor.attr_id in raw_state]

        entities.extend(
            [WinixIntegerSensor(wrapper, manager, sensor) for sensor in sensors]
        )

        entities.extend(
            [
                WinixSensor(wrapper, manager, description)
                for description in SENSOR_DESCRIPTIONS
                if description.exists_fn(wrapper)
            ]
        )

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


class WinixIntegerSensor(WinixSensor):
    """Representation of a Winix Purifier sensor with integer value."""

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        sensor_info: SensorInfo,
    ) -> None:
        """Initialize the sensor."""

        if isinstance(sensor_info, EnumSensorInfo):
            super().__init__(
                wrapper,
                coordinator,
                description=WinixSensorEntityDescription(
                    device_class=SensorDeviceClass.ENUM,
                    key=sensor_info.key,
                    translation_key=sensor_info.key,
                ),
            )

            self._attr_options = list(sensor_info.enum_values.keys())
        else:
            super().__init__(
                wrapper,
                coordinator,
                description=WinixSensorEntityDescription(
                    device_class=sensor_info.device_class,
                    state_class=SensorStateClass.MEASUREMENT,
                    key=sensor_info.key,
                    translation_key=sensor_info.key,
                    native_unit_of_measurement=sensor_info.native_unit_of_measurement,
                ),
            )

        self._attribute_id = sensor_info.attr_id
        LOGGER.debug(
            "%s (%s): added sensor %s on attribute %s",
            wrapper.device_stub.alias,
            wrapper.device_stub.model_id,
            sensor_info.key,
            sensor_info.attr_id,
        )

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        state = self.device_wrapper.get_raw_state()
        if state is None:
            return None

        value = None if state is None else state.get(self._attribute_id)
        return None if value is None else round(float(value))
