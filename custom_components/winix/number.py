"""Winix number entities (e.g. dehumidifier timer)."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    DOMAIN as NUMBER_DOMAIN,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import ATTR_TIMER, LOGGER
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager


@dataclass(frozen=True, kw_only=True)
class WinixNumberEntityDescription(NumberEntityDescription):
    """Describe a Winix number entity."""

    exists_fn: Callable[[WinixDeviceWrapper], bool]
    value_fn: Callable[[WinixDeviceWrapper], float | None]
    set_value_fn: Callable[[WinixDeviceWrapper, float], Coroutine[Any, Any, None]]


NUMBER_DESCRIPTIONS: tuple[WinixNumberEntityDescription, ...] = (
    WinixNumberEntityDescription(
        key="timer",
        name="Timer",
        translation_key="timer",
        icon="mdi:timer-outline",
        native_min_value=0,
        native_max_value=24,
        native_step=1,
        mode=NumberMode.BOX,
        native_unit_of_measurement="h",
        exists_fn=lambda device: device.is_dehumidifier,
        value_fn=lambda device: (device.get_state() or {}).get(ATTR_TIMER),
        set_value_fn=lambda device, value: device.async_set_timer(int(value)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Winix number entities."""
    manager = entry.runtime_data

    entities = [
        WinixNumberEntity(wrapper, manager, description)
        for description in NUMBER_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s number entities", len(entities))


class WinixNumberEntity(WinixEntity, NumberEntity):
    """Winix number entity (e.g. timer)."""

    entity_description: WinixNumberEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WinixNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = (
            f"{NUMBER_DOMAIN}.{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.device_wrapper)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.entity_description.set_value_fn(self.device_wrapper, value)
        self.async_write_ha_state()
