"""Support for Winix switches."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, Final

from homeassistant.components.switch import (
    ENTITY_ID_FORMAT,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import LOGGER
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager


@dataclass(frozen=True, kw_only=True)
class WinixSwitchEntityDescription(SwitchEntityDescription):
    """A class that describes custom switch entities."""

    is_on: Callable[[WinixDeviceWrapper], bool]
    exists_fn: Callable[[WinixDeviceWrapper], bool]
    on_fn: Callable[[WinixDeviceWrapper], Coroutine[Any, Any, bool]]
    off_fn: Callable[[WinixDeviceWrapper], Coroutine[Any, Any, bool]]


SWITCH_DESCRIPTIONS: Final[tuple[WinixSwitchEntityDescription, ...]] = (
    WinixSwitchEntityDescription(
        key="child_lock",
        is_on=lambda device: device.is_child_lock_on,
        exists_fn=lambda device: device.features.supports_child_lock,
        name="Child Lock",
        on_fn=lambda device: device.async_child_lock_on(),
        off_fn=lambda device: device.async_child_lock_off(),
    ),
    WinixSwitchEntityDescription(
        key="uv_sanitize",
        is_on=lambda device: device.is_uv_sanitize_on,
        exists_fn=lambda device: device.features.supports_uv_sanitize,
        name="UV Sanitize",
        on_fn=lambda device: device.async_uv_sanitize_on(),
        off_fn=lambda device: device.async_uv_sanitize_off(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up switch platform."""

    manager = entry.runtime_data

    entities = [
        WinixSwitchEntity(wrapper, manager, description)
        for description in SWITCH_DESCRIPTIONS
        for wrapper in manager.get_device_wrappers()
        if description.exists_fn(wrapper)
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s switches", len(entities))


class WinixSwitchEntity(WinixEntity, SwitchEntity):
    """Winix switch entity class."""

    entity_description: WinixSwitchEntityDescription

    def __init__(
        self,
        wrapper: WinixDeviceWrapper,
        coordinator: WinixManager,
        description: WinixSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(wrapper, coordinator)
        self.entity_description = description

        self._attr_unique_id = ENTITY_ID_FORMAT.format(
            f"{WINIX_DOMAIN}_{description.key.lower()}_{self._mac}"
        )

    @property
    def is_on(self) -> bool | None:
        """Return the switch state."""
        return self.entity_description.is_on(self.device_wrapper)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        if await self.entity_description.off_fn(self.device_wrapper):
            self.schedule_update_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        if await self.entity_description.on_fn(self.device_wrapper):
            self.schedule_update_ha_state()
