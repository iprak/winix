"""Support for Winix select entities."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.select import (
    ENTITY_ID_FORMAT,
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import ATTR_AIRFLOW, DEHUMIDIFIER_FAN_SPEEDS, LOGGER
from .device_wrapper import WinixDeviceWrapper
from .driver import BrightnessLevel
from .manager import WinixEntity, WinixManager


@dataclass(frozen=True, kw_only=True)
class WinixSelectEntityDescription(SelectEntityDescription):
    """A class that describes custom select entities."""

    exists_fn: Callable[[WinixDeviceWrapper], bool]
    current_option_fn: Callable[[WinixDeviceWrapper], str]
    select_option_fn: Callable[[WinixDeviceWrapper, str], Coroutine[Any, Any, Any]]
    available_fn: Callable[[WinixDeviceWrapper], bool] | None = None


def format_brightness_level(value: int | None) -> str:
    """Format numeric brightness level into select option."""
    return None if value is None else f"{value} %"


def parse_brightness_level(value: str) -> int:
    """Parse brightness level into integer equivalent."""
    if value:
        value = value[:-1]  # Remove %
        return int(value)

    return 0


BRIGHTNESS_OPTIONS = [format_brightness_level(e.value) for e in BrightnessLevel]

SELECT_DESCRIPTIONS: Final[tuple[WinixSelectEntityDescription, ...]] = (
    WinixSelectEntityDescription(
        current_option_fn=lambda device: format_brightness_level(
            device.brightness_level
        ),
        exists_fn=lambda device: device.features.supports_brightness_level,
        icon="mdi:brightness-6",
        key="brightness_level",
        name="Brightness Level",
        options=BRIGHTNESS_OPTIONS,
        select_option_fn=lambda device, value: device.async_set_brightness_level(
            parse_brightness_level(value)
        ),
        available_fn=lambda device: device.is_on,
    ),
    WinixSelectEntityDescription(
        current_option_fn=lambda device: (device.get_state() or {}).get(ATTR_AIRFLOW),
        exists_fn=lambda device: device.is_dehumidifier,
        icon="mdi:fan",
        key="fan_speed",
        name="Fan Speed",
        options=DEHUMIDIFIER_FAN_SPEEDS,
        select_option_fn=lambda device, value: device.async_set_speed(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up select platform."""

    manager = entry.runtime_data

    entities = [
        WinixSelectEntity(wrapper, manager, description)
        for description in SELECT_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s select entities", len(entities))


class WinixSelectEntity(WinixEntity, SelectEntity):
    """Winix select entity class."""

    entity_description: WinixSelectEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WinixSelectEntityDescription,
    ) -> None:
        """Initialize the select."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = ENTITY_ID_FORMAT.format(
            f"{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def current_option(self) -> str | None:
        """Return the entity value."""
        return self.entity_description.current_option_fn(self.device_wrapper)

    async def async_select_option(self, option: str) -> None:
        """Set the entity value."""
        await self.entity_description.select_option_fn(self.device_wrapper, option)
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if self.entity_description.available_fn is not None:
            return self.entity_description.available_fn(self.device_wrapper)
        return super().available
