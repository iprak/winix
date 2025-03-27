"""Support for Winix select entities."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import logging
from typing import Any, Final

from homeassistant.components.select import (
    DOMAIN as SELECT_DOMAIN,
    SelectEntity,
    SelectEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WINIX_DOMAIN
from .const import WINIX_DATA_COORDINATOR
from .device_wrapper import WinixDeviceWrapper
from .driver import BrightnessLevel
from .manager import WinixEntity, WinixManager

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class WinixSelectEntityDescription(SelectEntityDescription):
    """A class that describes custom select entities."""

    exists_fn: Callable[[WinixDeviceWrapper], bool]
    current_option_fn: Callable[[WinixDeviceWrapper], str]
    select_option_fn: Callable[[WinixDeviceWrapper, str], Coroutine[Any, Any, Any]]


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
        name="Brightness level",
        options=BRIGHTNESS_OPTIONS,
        select_option_fn=lambda device, value: device.async_set_brightness_level(
            parse_brightness_level(value)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up select platform."""

    data = hass.data[WINIX_DOMAIN][entry.entry_id]
    manager: WinixManager = data[WINIX_DATA_COORDINATOR]

    entities = [
        WinixSelectEntity(wrapper, manager, description)
        for description in SELECT_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    _LOGGER.info("Added %s selects", len(entities))


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

        self._attr_unique_id = (
            f"{SELECT_DOMAIN}.{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def current_option(self) -> str | None:
        """Return the entity value."""
        return self.entity_description.current_option_fn(self._wrapper)

    async def async_select_option(self, option: str) -> None:
        """Set the entity value."""
        if await self.entity_description.select_option_fn(self._wrapper, option):
            await self.coordinator.async_request_refresh()
