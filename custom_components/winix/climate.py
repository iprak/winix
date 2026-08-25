"""Winix Air Conditioner climate entity (deviceGroup "Acn01", modelId "AC100")."""

from typing import Any

from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    ENTITY_ID_FORMAT,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WINIX_DOMAIN, WinixConfigEntry
from .const import (
    AC_MODE_AUTO,
    AC_MODE_COOL,
    AC_MODE_DEHUMIDIFICATION,
    AC_MODE_FAN_ONLY,
    LOGGER,
)
from .manager import WinixEntity, WinixManager

FAN_SPEEDS = ["1", "2", "3", "4", "5"]
FAN_MODE_TURBO = "turbo"
SWING_OFF = "off"
SWING_ON = "on"

_HVAC_MODE_TO_AC_MODE = {
    HVACMode.AUTO: AC_MODE_AUTO,
    HVACMode.COOL: AC_MODE_COOL,
    HVACMode.FAN_ONLY: AC_MODE_FAN_ONLY,
    HVACMode.DRY: AC_MODE_DEHUMIDIFICATION,
}
_AC_MODE_TO_HVAC_MODE = {v: k for k, v in _HVAC_MODE_TO_AC_MODE.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WinixConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Winix air conditioner climate entities."""
    manager = entry.runtime_data
    entities = [
        WinixAirConditioner(wrapper, manager)
        for wrapper in manager.get_device_wrappers()
        if wrapper.is_air_conditioner
    ]
    async_add_entities(entities)


class WinixAirConditioner(WinixEntity, ClimateEntity):
    """Representation of a Winix window/portable air conditioner."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_WHOLE
    _attr_target_temperature_step = 1
    _attr_min_temp = 18
    _attr_max_temp = 30
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.COOL,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
    ]
    _attr_fan_modes = [*FAN_SPEEDS, FAN_MODE_TURBO]
    _attr_swing_modes = [SWING_OFF, SWING_ON]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    _attr_translation_key = "air_conditioner"

    def __init__(self, wrapper, coordinator: WinixManager) -> None:
        """Initialize the climate entity."""
        super().__init__(wrapper, coordinator)
        self._attr_unique_id = ENTITY_ID_FORMAT.format(f"{WINIX_DOMAIN}_{self._mac}")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        if not self.device_wrapper.ac_power_on:
            return HVACMode.OFF
        return _AC_MODE_TO_HVAC_MODE.get(self.device_wrapper.ac_mode, HVACMode.OFF)

    @property
    def current_temperature(self) -> int | None:
        """Return current room temperature."""
        return self.device_wrapper.ac_current_temperature

    @property
    def target_temperature(self) -> int | None:
        """Return target temperature."""
        return self.device_wrapper.ac_target_temperature

    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode."""
        if self.device_wrapper.ac_turbo_on:
            return FAN_MODE_TURBO
        speed = self.device_wrapper.ac_fan_speed
        return str(speed) if speed is not None else None

    @property
    def swing_mode(self) -> str:
        """Return current swing mode."""
        return SWING_ON if self.device_wrapper.ac_swing_on else SWING_OFF

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {"is_drying": self.device_wrapper.ac_is_drying}

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self.device_wrapper.async_ac_turn_off()
            self._async_write_state_and_schedule_refresh()
            return

        ac_mode = _HVAC_MODE_TO_AC_MODE.get(hvac_mode)
        if ac_mode is None:
            LOGGER.error("Unsupported hvac_mode=%s", hvac_mode)
            return

        if not self.device_wrapper.ac_power_on:
            await self.device_wrapper.async_ac_turn_on()
        await self.device_wrapper.async_ac_set_mode(ac_mode)
        self._async_write_state_and_schedule_refresh()

    async def async_turn_on(self) -> None:
        """Turn the air conditioner on."""
        await self.device_wrapper.async_ac_turn_on()
        self._async_write_state_and_schedule_refresh()

    async def async_turn_off(self) -> None:
        """Turn the air conditioner off."""
        await self.device_wrapper.async_ac_turn_off()
        self._async_write_state_and_schedule_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        await self.device_wrapper.async_ac_set_target_temperature(int(temperature))
        self._async_write_state_and_schedule_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if fan_mode == FAN_MODE_TURBO:
            await self.device_wrapper.async_ac_set_turbo(True)
            self._async_write_state_and_schedule_refresh()
            return

        if fan_mode not in FAN_SPEEDS:
            LOGGER.error("Unsupported fan_mode=%s", fan_mode)
            return

        await self.device_wrapper.async_ac_set_fan_speed(int(fan_mode))
        self._async_write_state_and_schedule_refresh()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        await self.device_wrapper.async_ac_set_swing(swing_mode == SWING_ON)
        self._async_write_state_and_schedule_refresh()
