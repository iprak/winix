"""The Winix C545 Air Purifier component."""

from typing import Dict

import aiohttp

from winix import WinixDeviceStub

from .WinixDriver import WinixDriver
from .const import (
    AIRFLOW_LOW,
    AIRFLOW_SLEEP,
    ATTR_AIRFLOW,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    MODE_AUTO,
    MODE_MANUAL,
    OFF_VALUE,
    ON_VALUE,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
    PRESET_MODES,
)


class WinixDeviceWrapper:
    """Representation of the Winix device data."""

    def __init__(
        self,
        client: aiohttp.ClientSession,
        device_stub: WinixDeviceStub,
        logger,
    ):
        """Initialize the wrapper."""
        self._driver = WinixDriver(device_stub.id, client)

        # Start as empty object in case fan was operated before it got updated
        self._state = {}

        self._on = False
        self._auto = False
        self._manual = False
        self._plasma_on = False
        self._sleep = False
        self._logger = logger

        self.info = device_stub

    async def update(self) -> None:
        """Update the device data."""
        self._state = await self._driver.get_state()
        self._auto = self._manual = self._sleep = self._plasma_on = False

        self._on = self._state.get(ATTR_POWER) == ON_VALUE
        self._plasma_on = self._state.get(ATTR_PLASMA) == ON_VALUE

        # Sleep: airflow=sleep, mode can be manual
        # Auto: mode=auto, airflow can be anything
        # Low: manual+low

        if self._state.get(ATTR_MODE) == MODE_AUTO:
            self._auto = True
            self._manual = False
        elif self._state.get(ATTR_MODE) == MODE_MANUAL:
            self._auto = False
            self._manual = True

        if self._state.get(ATTR_AIRFLOW) == AIRFLOW_SLEEP:
            self._sleep = True

        self._logger.debug(
            "%s: updated on=%s, auto=%s, manual=%s, sleep=%s, airflow=%s, plasma=%s",
            self.info.alias,
            self._on,
            self._auto,
            self._manual,
            self._sleep,
            self._state.get(ATTR_AIRFLOW),
            self._plasma_on,
        )

    def get_state(self) -> Dict[str, str]:
        """Return the device data."""
        return self._state

    @property
    def is_on(self) -> bool:
        """Return if the purifier is on."""
        return self._on

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

    async def async_ensure_on(self) -> None:
        """Turn on the purifier."""
        if not self._on:
            self._on = True

            self._logger.debug("%s: Turning on", self.info.alias)
            await self._driver.turn_on()

    async def async_turn_on(self) -> None:
        """Turn on the purifier in Auto mode."""
        await self.async_ensure_on()
        await self.async_auto()

    async def async_turn_off(self) -> None:
        """Turn off the purifier."""
        if self._on:
            self._on = False

            self._logger.debug("%s: Turning off", self.info.alias)
            await self._driver.turn_off()

    async def async_auto(self) -> None:
        """
        Put the purifier in Auto mode with Low airflow.

        Plasma state is left unchanged. The Winix server seems to sometimes
        turns it on for Auto mode.
        """

        if not self._auto:
            self._auto = True
            self._manual = False
            self._sleep = False
            self._state[ATTR_MODE] = MODE_AUTO
            self._state[
                ATTR_AIRFLOW
            ] = AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP

            self._logger.debug("%s: Setting auto mode", self.info.alias)
            await self._driver.auto()

    async def async_plasmawave_on(self) -> None:
        """Turn on plasma wave."""

        if not self._plasma_on:
            self._plasma_on = True
            self._state[ATTR_PLASMA] = ON_VALUE

            self._logger.debug("%s: Turning plasmawave on", self.info.alias)
            await self._driver.plasmawave_on()

    async def async_plasmawave_off(self) -> None:
        """Turn off plasma wave."""

        if self._plasma_on:
            self._plasma_on = False
            self._state[ATTR_PLASMA] = OFF_VALUE

            self._logger.debug("%s: Turning plasmawave off", self.info.alias)
            await self._driver.plasmawave_off()

    async def async_manual(self) -> None:
        """Put the purifier in Manual mode with Low airflow. Plasma state is left unchanged."""

        if not self._manual:
            self._manual = True
            self._auto = False
            self._sleep = False
            self._state[ATTR_MODE] = MODE_MANUAL
            self._state[
                ATTR_AIRFLOW
            ] = AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP

            self._logger.debug("%s: Setting manual mode", self.info.alias)
            await self._driver.manual()

    async def async_sleep(self) -> None:
        """Turn the purifier in Manual mode with Sleep airflow. Plasma state is left unchanged."""

        if not self._sleep:
            self._sleep = True
            self._auto = False
            self._manual = False
            self._state[ATTR_AIRFLOW] = AIRFLOW_SLEEP
            self._state[ATTR_MODE] = MODE_MANUAL

            self._logger.debug("%s: Setting sleep mode", self.info.alias)
            await self._driver.sleep()

    async def async_set_speed(self, speed) -> None:
        """Turn the purifier on, put it in Manual mode and set the speed."""

        if self._state.get(ATTR_AIRFLOW) != speed:
            self._state[ATTR_AIRFLOW] = speed

            # Setting speed requires the fan to be in manual mode
            await self.async_ensure_on()
            await self.async_manual()

            self._logger.debug("%s: Updated speed to '%s'", self.info.alias, speed)
            await getattr(self._driver, speed)()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Turn the purifier on and put it in the new preset mode."""

        if preset_mode not in PRESET_MODES:
            self._logger.warning("'%s'is an invalid preset mode", preset_mode)
            return

        await self.async_ensure_on()

        if preset_mode == PRESET_MODE_SLEEP:
            await self.async_sleep()
        elif preset_mode == PRESET_MODE_AUTO:
            await self.async_auto()
        elif preset_mode == PRESET_MODE_MANUAL:
            await self.async_manual()
            await self.async_plasmawave_off()
        elif preset_mode == PRESET_MODE_MANUAL_PLASMA:
            await self.async_manual()
            await self.async_plasmawave_on()
