"""Winix Binary Sensor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import BINARY_SENSOR_WATER_TANK, LOGGER
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager


@dataclass(frozen=True, kw_only=True)
class WinixBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe a Winix binary sensor entity."""

    is_on: Callable[[WinixDeviceWrapper], bool]
    exists_fn: Callable[[WinixDeviceWrapper], bool] = lambda _: True


BINARY_SENSOR_DESCRIPTIONS: tuple[WinixBinarySensorEntityDescription, ...] = (
    WinixBinarySensorEntityDescription(
        key=BINARY_SENSOR_WATER_TANK,
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:water-outline",
        name="Water Tank",
        translation_key="water_tank",
        is_on=lambda device: not device.is_water_tank_available,
        exists_fn=lambda device: device.is_dehumidifier,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Winix binary sensors."""
    manager = entry.runtime_data

    entities = [
        WinixBinarySensor(wrapper, manager, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s binary sensors", len(entities))


class WinixBinarySensor(WinixEntity, BinarySensorEntity):
    """Representation of a Winix binary sensor."""

    entity_description: WinixBinarySensorEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WinixBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = (
            f"{BINARY_SENSOR_DOMAIN}.{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.entity_description.is_on(self.device_wrapper)
