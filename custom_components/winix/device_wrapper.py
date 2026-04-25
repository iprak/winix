"""The Winix Air Purifier component."""

from __future__ import annotations

import dataclasses

import aiohttp

from .const import (
    AIRFLOW_LOW,
    AIRFLOW_SLEEP,
    ATTR_AIRFLOW,
    ATTR_BRIGHTNESS_LEVEL,
    ATTR_CHILD_LOCK,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    ATTR_TARGET_HUMIDITY,
    ATTR_TIMER,
    ATTR_UV_SANITIZE,
    ATTR_WATER_TANK,
    AUTO_DRY_VALUE,
    MODE_AUTO,
    MODE_MANUAL,
    OFF_VALUE,
    ON_VALUE,
    PRESET_MODE_AUTO,
    PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA_OFF,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
    Features,
    NumericPresetModes,
)
from .driver import AirPurifierDriver, DehumidifierDriver


@dataclasses.dataclass
class MyWinixDeviceStub:
    """Winix device information."""

    id: str
    mac: str
    alias: str
    location_code: str
    filter_replace_date: str
    model: str
    sw_version: str
    product_group: str


def _select_driver(
    device_stub: MyWinixDeviceStub,
    client: aiohttp.ClientSession,
    identity_id: str,
) -> AirPurifierDriver | DehumidifierDriver:
    """Return the driver that matches the device's product group."""

    product_group = (device_stub.product_group or "").casefold()
    if product_group.startswith("air"):
        return AirPurifierDriver(device_stub.id, client, identity_id)
    elif product_group.startswith("deh"):
        return DehumidifierDriver(device_stub.id, client, identity_id)

    raise ValueError(
        f"Unsupported product_group '{device_stub.product_group}' for device {device_stub.alias}"
    )


class WinixDeviceWrapper:
    """Representation of the Winix device data."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        client: aiohttp.ClientSession,
        device_stub: MyWinixDeviceStub,
        filter_alarm_duration_hours: int,
        logger,
        identity_id: str,
    ) -> None:
        """Initialize the wrapper."""

        self._driver = _select_driver(device_stub, client, identity_id)

        # Start as empty object in case fan was operated before it got updated
        self._state = {}

        self._on = False
        self._auto = False
        self._manual = False
        self._plasma_on = False
        self._sleep = False
        self._logger = logger
        self._child_lock_on: bool | None = None
        self._brightness_level = None
        self._uv_sanitize: bool | None = None
        self._water_tank = False
        self._auto_dry = False
        self._filter_alarm_duration = filter_alarm_duration_hours

        self.device_stub = device_stub
        self._alias = device_stub.alias
        self._features = Features()

        logger.debug(
            "%s: created device with filter_alarm_duration=%d",
            self._alias,
            filter_alarm_duration_hours,
        )

    def update_features(self) -> None:
        """Update the supported features based on the current state."""
        self._features.supports_brightness_level = self.brightness_level is not None
        self._features.supports_child_lock = self.is_child_lock_on is not None
        self._features.supports_uv_sanitize = self.is_uv_sanitize_on is not None

    async def update(self) -> None:
        """Update the device data."""
        self._state = await self._driver.get_state()
        self._update_common_flags()
        if self.is_air_purifier:
            self._update_air_purifier_flags()
            self._logger.debug(
                "%s: updated on=%s, auto=%s, manual=%s, sleep=%s, "
                "airflow=%s, plasma=%s",
                self._alias,
                self._on,
                self._auto,
                self._manual,
                self._sleep,
                self._state.get(ATTR_AIRFLOW),
                self._plasma_on,
            )
        elif self.is_dehumidifier:
            self._update_dehumidifier_flags()
            self._logger.debug(
                "%s: updated on=%s, auto_dry=%s, mode=%s, airflow=%s, "
                "uv_sanitize=%s, water_tank=%s",
                self._alias,
                self._on,
                self._auto_dry,
                self._state.get(ATTR_MODE),
                self._state.get(ATTR_AIRFLOW),
                self._uv_sanitize,
                self._water_tank,
            )

    def _update_common_flags(self) -> None:
        """Refresh device-common flags from the latest state."""
        self._on = self._state.get(ATTR_POWER) == ON_VALUE
        self._plasma_on = self._state.get(ATTR_PLASMA) == ON_VALUE

        value = self._state.get(ATTR_CHILD_LOCK)
        self._child_lock_on = value == ON_VALUE if value is not None else None

        self._brightness_level = self._state.get(ATTR_BRIGHTNESS_LEVEL)

    def _update_air_purifier_flags(self) -> None:
        """Refresh air-purifier-only flags from the latest state."""
        self._auto = self._manual = self._sleep = False

        # Sleep: airflow=sleep, mode can be manual
        # Auto: mode=auto, airflow can be anything
        # Low: manual+low

        if self._state.get(ATTR_MODE) == MODE_AUTO:
            self._auto = True
        elif self._state.get(ATTR_MODE) == MODE_MANUAL:
            self._manual = True

        if self._state.get(ATTR_AIRFLOW) == AIRFLOW_SLEEP:
            self._sleep = True

    def _update_dehumidifier_flags(self) -> None:
        """Refresh dehumidifier-only flags from the latest state."""
        value = self._state.get(ATTR_UV_SANITIZE)
        self._uv_sanitize = value == ON_VALUE if value is not None else None
        self._water_tank = self._state.get(ATTR_WATER_TANK) == ON_VALUE
        self._auto_dry = self._state.get(ATTR_POWER) == AUTO_DRY_VALUE

    def get_state(self) -> dict[str, str]:
        """Return the device data."""
        return self._state

    @property
    def features(self) -> Features:
        """Return device features."""
        return self._features

    @property
    def is_air_purifier(self) -> bool:
        """Return True if this device is an air purifier."""
        return isinstance(self._driver, AirPurifierDriver)

    @property
    def is_dehumidifier(self) -> bool:
        """Return True if this device is a dehumidifier."""
        return isinstance(self._driver, DehumidifierDriver)

    @property
    def is_on(self) -> bool:
        """Return True if the device is powered on."""
        return self._on

    @property
    def is_auto_dry(self) -> bool:
        """Return True if the dehumidifier is in auto-dry power state."""
        return self._auto_dry

    @property
    def is_auto(self) -> bool:
        """Return if the purifier is in Auto mode."""
        return self._auto

    @property
    def is_manual(self) -> bool:
        """Return if the purifier is in Manual mode."""
        return self._manual

    @property
    def is_plasma_on(self) -> bool:
        """Return if plasma is on."""
        return self._plasma_on

    @property
    def is_sleep(self) -> bool:
        """Return if the purifier is in Sleep mode."""
        return self._sleep

    @property
    def filter_alarm_duration(self) -> int:
        """Filter change duration reminder in hours."""
        return self._filter_alarm_duration

    async def async_ensure_on(self) -> None:
        """Ensure the device is powered on."""
        if not self._on:
            self._on = True
            self._state[ATTR_POWER] = ON_VALUE

            self._logger.debug("%s => turned on", self._alias)
            await self._driver.turn_on()

    async def async_turn_on(self) -> None:
        """Turn on the device. Air purifiers enter Auto mode; other devices simply power on."""
        await self.async_ensure_on()
        if self.is_air_purifier:
            await self.async_set_mode(MODE_AUTO)

    async def async_turn_off(self) -> None:
        """Turn off the device."""
        if self._on:
            self._on = False
            # Dehumidifiers may transition to AUTO_DRY_VALUE instead;
            # next refresh reconciles.
            self._state[ATTR_POWER] = OFF_VALUE

            self._logger.debug("%s => turned off", self._alias)
            await self._driver.turn_off()

    async def async_set_mode(self, mode: str) -> None:
        """Set the operating mode. Accepts device-specific mode constants.

        Plasma state is left unchanged. The Winix server seems to sometimes
        turns it on for Auto mode.
        """

        if mode not in self._driver.state_keys[ATTR_MODE]:
            self._logger.error("%s => unsupported mode=%s", self._alias, mode)
            return

        if self.is_air_purifier:
            if mode == MODE_AUTO:
                if self._auto:
                    return
                self._auto = True
                self._manual = False
                self._sleep = False
                self._state[ATTR_MODE] = MODE_AUTO
                self._state[ATTR_AIRFLOW] = (
                    AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP
                )

                self._logger.debug("%s => set mode=auto", self._alias)
                await self._driver.auto()
            elif mode == MODE_MANUAL:
                if self._manual:
                    return
                self._manual = True
                self._auto = False
                self._sleep = False
                self._state[ATTR_MODE] = MODE_MANUAL
                self._state[ATTR_AIRFLOW] = (
                    AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP
                )

                self._logger.debug("%s => set mode=manual", self._alias)
                await self._driver.manual()
        elif self.is_dehumidifier:
            if self._state.get(ATTR_MODE) == mode:
                return
            await self._driver.set_mode(mode)
            self._state[ATTR_MODE] = mode

    async def async_plasmawave_on(self, force: bool = False) -> None:
        """Turn on plasma wave."""

        if force or not self._plasma_on:
            self._plasma_on = True
            self._state[ATTR_PLASMA] = ON_VALUE

            self._logger.debug("%s => set plasmawave=on", self._alias)
            await self._driver.plasmawave_on()

    async def async_plasmawave_off(self, force: bool = False) -> None:
        """Turn off plasma wave."""

        if force or self._plasma_on:
            self._plasma_on = False
            self._state[ATTR_PLASMA] = OFF_VALUE

            self._logger.debug("%s => set plasmawave=off", self._alias)
            await self._driver.plasmawave_off()

    @property
    def is_child_lock_on(self) -> bool | None:
        """Return if child lock is on."""
        return self._child_lock_on

    async def async_child_lock_on(self) -> bool:
        """Turn on child lock."""

        if not self._features.supports_child_lock or self._child_lock_on:
            return False

        await self._driver.child_lock_on()
        self._child_lock_on = True
        self._state[ATTR_CHILD_LOCK] = ON_VALUE
        return True

    async def async_child_lock_off(self) -> bool:
        """Turn off child lock."""

        if not self._features.supports_child_lock or not self._child_lock_on:
            return False

        await self._driver.child_lock_off()
        self._child_lock_on = False
        self._state[ATTR_CHILD_LOCK] = OFF_VALUE
        return True

    @property
    def brightness_level(self) -> int | None:
        """Return current brightness level."""
        return self._brightness_level

    async def async_set_brightness_level(self, value: int) -> bool:
        """Set brightness level."""

        if not self._features.supports_brightness_level or (
            self._brightness_level == value
        ):
            return False

        await self._driver.set_brightness_level(value)
        self._brightness_level = value
        self._state[ATTR_BRIGHTNESS_LEVEL] = value
        return True

    async def async_sleep(self) -> None:
        """Turn the purifier in Manual mode with Sleep airflow. Plasma state is left unchanged."""

        if not self._sleep:
            self._sleep = True
            self._auto = False
            self._manual = False
            self._state[ATTR_AIRFLOW] = AIRFLOW_SLEEP
            self._state[ATTR_MODE] = MODE_MANUAL

            self._logger.debug("%s => set mode=sleep", self._alias)
            await self._driver.sleep()

    async def async_set_speed(self, speed) -> None:
        """Set the device fan speed."""

        if self.is_air_purifier:
            self._state[ATTR_AIRFLOW] = speed

            # Setting speed requires the fan to be in manual mode
            await self.async_ensure_on()
            await self.async_set_mode(MODE_MANUAL)

            self._logger.debug("%s => set speed=%s", self._alias, speed)
            await getattr(self._driver, speed)()
        elif self.is_dehumidifier:
            if self._state.get(ATTR_AIRFLOW) == speed:
                return
            await self._driver.set_fan_speed(speed)
            self._state[ATTR_AIRFLOW] = speed

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Turn the purifier on and put it in the new preset mode."""

        preset_mode = preset_mode.strip()

        if preset_mode not in PRESET_MODES:
            values = [item.value for item in NumericPresetModes]

            # Convert the numeric preset mode to its corresponding key
            if preset_mode in values:
                index = int(preset_mode) - 1
                preset_mode = PRESET_MODES[index]
            else:
                raise ValueError(f"Invalid preset mode: {preset_mode}")

        await self.async_ensure_on()
        self._logger.debug("%s => set mode=%s", self._alias, preset_mode)

        if preset_mode == PRESET_MODE_SLEEP:
            await self.async_sleep()
        elif preset_mode == PRESET_MODE_AUTO:
            await self.async_set_mode(MODE_AUTO)
            await self.async_plasmawave_on()
        elif preset_mode == PRESET_MODE_AUTO_PLASMA_OFF:
            await self.async_set_mode(MODE_AUTO)
            await self.async_plasmawave_off(True)
        elif preset_mode == PRESET_MODE_MANUAL:
            await self.async_set_mode(MODE_MANUAL)
            await self.async_plasmawave_on()
        elif preset_mode == PRESET_MODE_MANUAL_PLASMA_OFF:
            await self.async_set_mode(MODE_MANUAL)
            await self.async_plasmawave_off(True)

    @property
    def is_uv_sanitize_on(self) -> bool | None:
        """Return if UV sanitize is on."""
        return self._uv_sanitize

    async def async_uv_sanitize_on(self) -> bool:
        """Turn on UV sanitize."""
        if not self._features.supports_uv_sanitize or self._uv_sanitize:
            return False
        await self._driver.uv_sanitize_on()
        self._uv_sanitize = True
        self._state[ATTR_UV_SANITIZE] = ON_VALUE
        return True

    async def async_uv_sanitize_off(self) -> bool:
        """Turn off UV sanitize."""
        if not self._features.supports_uv_sanitize or not self._uv_sanitize:
            return False
        await self._driver.uv_sanitize_off()
        self._uv_sanitize = False
        self._state[ATTR_UV_SANITIZE] = OFF_VALUE
        return True

    @property
    def is_water_tank_available(self) -> bool:
        """Return True if the water tank is not full and not detached."""
        return not self._water_tank

    async def async_set_humidity(self, humidity: int) -> bool:
        """Set the target humidity (35-70 %, 5 % steps)."""
        if self._state.get(ATTR_TARGET_HUMIDITY) == humidity:
            return False
        await self._driver.set_humidity(humidity)
        self._state[ATTR_TARGET_HUMIDITY] = humidity
        return True

    async def async_set_timer(self, hours: int) -> bool:
        """Set the dehumidifier timer (0 = off, 1-24 hours)."""
        if self._state.get(ATTR_TIMER) == hours:
            return False
        await self._driver.set_timer(hours)
        self._state[ATTR_TIMER] = hours
        return True
