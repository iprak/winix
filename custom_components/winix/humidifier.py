"""Winix Dehumidifier entity."""

from __future__ import annotations

from typing import Any

from homeassistant.components.humidifier import (
    DOMAIN as HUMIDIFIER_DOMAIN,
    HumidifierAction,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_MODE,
    ATTR_TARGET_HUMIDITY,
    DEHUMIDIFIER_HUMIDITY_STEP,
    DEHUMIDIFIER_MAX_HUMIDITY,
    DEHUMIDIFIER_MIN_HUMIDITY,
    DEHUMIDIFIER_MODES,
    LOGGER,
)
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Winix dehumidifier entities."""
    manager = entry.runtime_data
    entities = [
        WinixDehumidifier(wrapper, manager)
        for wrapper in manager.get_device_wrappers()
        if wrapper.is_dehumidifier
    ]
    async_add_entities(entities)
    LOGGER.info("Added %s dehumidifiers", len(entities))


class WinixDehumidifier(WinixEntity, HumidifierEntity):
    """Representation of a Winix Dehumidifier."""

    # https://developers.home-assistant.io/docs/core/entity/humidifier/
    _attr_supported_features = HumidifierEntityFeature.MODES

    _attr_min_humidity = DEHUMIDIFIER_MIN_HUMIDITY
    _attr_max_humidity = DEHUMIDIFIER_MAX_HUMIDITY
    _attr_target_humidity_step = DEHUMIDIFIER_HUMIDITY_STEP

    _attr_translation_key = "dehumidifier"

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the dehumidifier entity."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = f"{HUMIDIFIER_DOMAIN}.{WINIX_DOMAIN}_{self._mac}"

    @property
    def name(self) -> str | None:
        """Return None so this is treated as the primary device entity."""
        return None

    @property
    def available_modes(self) -> list[str]:
        """Return the list of available modes."""
        return DEHUMIDIFIER_MODES

    @property
    def mode(self) -> str | None:
        """Return the current operating mode."""
        state = self.device_wrapper.get_state()
        if state is None:
            return None
        return state.get(ATTR_MODE)

    @property
    def is_on(self) -> bool:
        """Return True if the dehumidifier is on (including auto-dry/idle)."""
        return self.device_wrapper.is_on or self.device_wrapper.is_auto_dry

    @property
    def action(self) -> HumidifierAction | None:
        """Return the current action."""
        if self.device_wrapper.get_state() is None:
            return None
        if self.device_wrapper.is_on:
            return HumidifierAction.DRYING
        if self.device_wrapper.is_auto_dry:
            return HumidifierAction.IDLE
        return HumidifierAction.OFF

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        state = self.device_wrapper.get_state()
        if state is None:
            return None
        value = state.get(ATTR_CURRENT_HUMIDITY)
        return int(value) if value is not None else None

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity."""
        state = self.device_wrapper.get_state()
        if state is None:
            return None
        value = state.get(ATTR_TARGET_HUMIDITY)
        return int(value) if value is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the dehumidifier on."""
        await self.device_wrapper.async_turn_on()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the dehumidifier off."""
        await self.device_wrapper.async_turn_off()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set target humidity, rounding to nearest 5 % step and clamping to valid range."""
        humidity = round(humidity / DEHUMIDIFIER_HUMIDITY_STEP) * DEHUMIDIFIER_HUMIDITY_STEP
        humidity = max(DEHUMIDIFIER_MIN_HUMIDITY, min(DEHUMIDIFIER_MAX_HUMIDITY, humidity))
        await self.device_wrapper.async_set_humidity(humidity)
        self.async_write_ha_state()

    async def async_set_mode(self, mode: str) -> None:
        """Set operating mode. Wrapper validates against driver-supported modes."""
        await self.device_wrapper.async_set_mode(mode)
        self.async_write_ha_state()
