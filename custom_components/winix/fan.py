"""Winix Air Purifier Device."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.fan import (
    DOMAIN as FAN_DOMAIN,
    FanEntity,
    FanEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import (
    ATTR_AIRFLOW,
    ATTR_FILTER_REPLACEMENT_DATE,
    ATTR_LOCATION,
    ATTR_POWER,
    FAN_SERVICES,
    ORDERED_NAMED_FAN_SPEEDS,
    PRESET_MODE_AUTO,
    PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA_OFF,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
    WINIX_DATA_COORDINATOR,
    WINIX_DATA_KEY,
    WINIX_DOMAIN,
)
from .device_wrapper import WinixDeviceWrapper
from .manager import WinixEntity, WinixManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Winix air purifiers."""
    data = hass.data[WINIX_DOMAIN][entry.entry_id]
    manager: WinixManager = data[WINIX_DATA_COORDINATOR]
    entities = [
        WinixPurifier(wrapper, manager) for wrapper in manager.get_device_wrappers()
    ]
    data[WINIX_DATA_KEY] = entities
    async_add_entities(entities)

    async def async_service_handler(service_call):
        """Service handler."""
        method = "async_" + service_call.service
        _LOGGER.debug("Service '%s' invoked", service_call.service)

        # The defined services do not accept any additional parameters
        params = {}

        entity_ids = service_call.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                entity
                for entity in data[WINIX_DATA_KEY]
                if entity.entity_id in entity_ids
            ]
        else:
            devices = data[WINIX_DATA_KEY]

        state_update_tasks = []
        for device in devices:
            if not hasattr(device, method):
                continue

            await getattr(device, method)(**params)
            state_update_tasks.append(
                asyncio.create_task(device.async_update_ha_state(True))
            )

        if state_update_tasks:
            # Update device states in HA
            await asyncio.wait(state_update_tasks)

    for service in FAN_SERVICES:
        hass.services.async_register(
            WINIX_DOMAIN,
            service,
            async_service_handler,
            schema=vol.Schema({ATTR_ENTITY_ID: cv.entity_ids}),
        )

    _LOGGER.info("Added %s Winix fans", len(entities))


class WinixPurifier(WinixEntity, FanEntity):
    """Representation of a Winix Purifier entity."""

    # https://developers.home-assistant.io/docs/core/entity/fan/
    _attr_supported_features = (
        FanEntityFeature.PRESET_MODE
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, wrapper: WinixDeviceWrapper, coordinator: WinixManager) -> None:
        """Initialize the entity."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = f"{FAN_DOMAIN}.{WINIX_DOMAIN}_{self._mac}"

    @property
    def name(self) -> str | None:
        """Entity Name.

        Returning None, since this is the primary entity.
        """
        return None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        attributes = {}
        state = self._wrapper.get_state()

        if state is not None:
            # The power attribute is the entity state, so skip it
            attributes = {
                key: value for key, value in state.items() if key != ATTR_POWER
            }

        attributes[ATTR_LOCATION] = self._wrapper.device_stub.location_code
        attributes[ATTR_FILTER_REPLACEMENT_DATE] = (
            self._wrapper.device_stub.filter_replace_date
        )

        return attributes

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self._wrapper.is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        state = self._wrapper.get_state()
        if state is None:
            return None
        if self._wrapper.is_sleep or self._wrapper.is_auto:
            return None
        if state.get(ATTR_AIRFLOW) is None:
            return None

        return ordered_list_item_to_percentage(
            ORDERED_NAMED_FAN_SPEEDS, state.get(ATTR_AIRFLOW)
        )

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite."""
        state = self._wrapper.get_state()
        if state is None:
            return None
        if self._wrapper.is_sleep:
            return PRESET_MODE_SLEEP
        if self._wrapper.is_auto:
            return (
                PRESET_MODE_AUTO
                if self._wrapper.is_plasma_on
                else PRESET_MODE_AUTO_PLASMA_OFF
            )
        if self._wrapper.is_manual:
            return (
                PRESET_MODE_MANUAL
                if self._wrapper.is_plasma_on
                else PRESET_MODE_MANUAL_PLASMA_OFF
            )

        return None

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes."""
        return PRESET_MODES

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return ORDERED_NAMED_FAN_SPEEDS

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            await self.async_turn_off()
        else:
            await self._wrapper.async_set_speed(
                percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
            )

        self.async_write_ha_state()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        # pylint: disable=unused-argument
        """Turn on the purifier."""

        if percentage:
            await self.async_set_percentage(percentage)
        if preset_mode:
            await self._wrapper.async_set_preset_mode(preset_mode)
        else:
            await self._wrapper.async_turn_on()

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the purifier."""
        await self._wrapper.async_turn_off()
        self.async_write_ha_state()

    async def async_plasmawave_on(self) -> None:
        """Turn on plasma wave."""
        await self._wrapper.async_plasmawave_on()
        self.async_write_ha_state()

    async def async_plasmawave_off(self) -> None:
        """Turn off plasma wave."""
        await self._wrapper.async_plasmawave_off()
        self.async_write_ha_state()

    async def async_plasmawave_toggle(self) -> None:
        """Toggle plasma wave."""

        if self._wrapper.is_plasma_on:
            await self._wrapper.async_plasmawave_off()
        else:
            await self._wrapper.async_plasmawave_on()

        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        await self._wrapper.async_set_preset_mode(preset_mode)
        self.async_write_ha_state()
