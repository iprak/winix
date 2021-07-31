"""The Winix C545 Air Purifier component."""


from typing import Dict

import aiohttp

from winix import WinixDeviceStub

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
    PRESET_MODES,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
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
        self.driver = WinixDevice(device_stub.id, client)
        self.info = device_stub
        self._state = None
        self._on = False
        self._auto = False
        self._manual = False
        self._plasma_on = False
        self._sleep = False
        self._logger = logger

    async def update(self) -> None:
        """Update the device data."""
        self._state = await self.driver.get_state()
        self._auto = self._manual = self._sleep = self._plasma_on = False

        self._on = self._state.get(ATTR_POWER) == ON_VALUE
        self._plasma_on = self._state[ATTR_PLASMA] == ON_VALUE

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
            await self.driver.turn_on()

    async def async_turn_on(self) -> None:
        """Turn on the purifier in Auto mode."""
        await self.async_ensure_on()
        await self.async_auto()

    async def async_turn_off(self) -> None:
        """Turn off the purifier."""
        if self._on:
            self._on = False

            self._logger.debug("%s: Turning off", self.info.alias)
            await self.driver.turn_off()

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
            await self.driver.auto()

    async def async_plasmawave_on(self) -> None:
        """Turn on plasma wave."""

        if not self._plasma_on:
            self._plasma_on = True
            self._state[ATTR_PLASMA] = ON_VALUE

            self._logger.debug("%s: Turning plasmawave on", self.info.alias)
            await self.driver.plasmawave_on()

    async def async_plasmawave_off(self) -> None:
        """Turn off plasma wave."""

        if self._plasma_on:
            self._plasma_on = False
            self._state[ATTR_PLASMA] = OFF_VALUE

            self._logger.debug("%s: Turning plasmawave off", self.info.alias)
            await self.driver.plasmawave_off()

    async def async_manual(self) -> None:
        """
        Put the purifier in Manual mode with Low airflow.
        Plasma state is left unchanged.
        """

        if not self._manual:
            self._manual = True
            self._auto = False
            self._sleep = False
            self._state[ATTR_MODE] = MODE_MANUAL
            self._state[
                ATTR_AIRFLOW
            ] = AIRFLOW_LOW  # Something other than AIRFLOW_SLEEP

            self._logger.debug("%s: Setting manual mode", self.info.alias)
            await self.driver.manual()

    async def async_sleep(self) -> None:
        """
        Turn the purifier in Manual mode with Sleep airflow.
        Plasma state is left unchanged.
        """

        if not self._sleep:
            self._sleep = True
            self._auto = False
            self._manual = False
            self._state[ATTR_AIRFLOW] = AIRFLOW_SLEEP
            self._state[ATTR_MODE] = MODE_MANUAL

            self._logger.debug("%s: Setting sleep mode", self.info.alias)
            await self.driver.sleep()

    async def async_set_speed(self, speed) -> None:
        """Turn the purifier on, put it in Manual mode and set the speed."""

        if self._state[ATTR_AIRFLOW] != speed:
            self._state[ATTR_AIRFLOW] = speed

            # Setting speed requires the fan to be in manual mode
            await self.async_ensure_on()
            await self.async_manual()

            self._logger.debug("%s: Updated speed to '%s'", self.info.alias, speed)
            await getattr(self.driver, speed)()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Turn the purifier on and put it in the new preset mode."""

        if not preset_mode in PRESET_MODES:
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


# Modified from https://github.com/hfern/winix to support async operations
class WinixDevice:
    """WinixDevice driver."""

    CTRL_URL = "https://us.api.winix-iot.com/common/control/devices/{deviceid}/A211/{attribute}:{value}"
    STATE_URL = "https://us.api.winix-iot.com/common/event/sttus/devices/{deviceid}"

    category_keys = {
        "power": "A02",
        "mode": "A03",
        "airflow": "A04",
        "aqi": "A05",
        "plasma": "A07",
        "filter_hour": "A21",
        "air_quality": "S07",
        "air_qvalue": "S08",
        "ambient_light": "S14",
    }

    state_keys = {
        "power": {"off": "0", "on": "1"},
        "mode": {"auto": "01", "manual": "02"},
        "airflow": {
            "low": "01",
            "medium": "02",
            "high": "03",
            "turbo": "05",
            "sleep": "06",
        },
        "plasma": {"off": "0", "on": "1"},
        "air_quality": {"good": "01", "fair": "02", "poor": "03"},
    }

    def __init__(self, device_id: str, client: aiohttp.ClientSession):
        """Create an instance of WinixDevice."""
        self.device_id = device_id
        self._client = client

    async def turn_off(self):
        """Turn the device off."""
        await self._rpc_attr(
            self.category_keys["power"], self.state_keys["power"]["off"]
        )

    async def turn_on(self):
        """Turn the device on."""
        await self._rpc_attr(
            self.category_keys["power"], self.state_keys["power"]["on"]
        )

    async def auto(self):
        """Set device in auto mode."""
        await self._rpc_attr(
            self.category_keys["mode"], self.state_keys["mode"]["auto"]
        )

    async def manual(self):
        """Set device in manual mode."""
        await self._rpc_attr(
            self.category_keys["mode"], self.state_keys["mode"]["manual"]
        )

    async def plasmawave_off(self):
        """Turn plasmawave off."""
        await self._rpc_attr(
            self.category_keys["plasma"], self.state_keys["plasma"]["off"]
        )

    async def plasmawave_on(self):
        """Turn plasmawave on."""
        await self._rpc_attr(
            self.category_keys["plasma"], self.state_keys["plasma"]["on"]
        )

    async def low(self):
        """Set speed low."""
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["low"]
        )

    async def medium(self):
        """Set speed medium."""
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["medium"]
        )

    async def high(self):
        """Set speed high."""
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["high"]
        )

    async def turbo(self):
        """Set speed turbo."""
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["turbo"]
        )

    async def sleep(self):
        """Set device in sleep mode."""
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["sleep"]
        )

    async def _rpc_attr(self, attr: str, value: str):
        await self._client.get(
            self.CTRL_URL.format(deviceid=self.device_id, attribute=attr, value=value)
        )
        # requests.get(
        #     self.CTRL_URL.format(deviceid=self.id, attribute=attr, value=value)
        # )

    async def get_state(self) -> Dict[str, str]:
        """Get device state."""
        response = await self._client.get(
            self.STATE_URL.format(deviceid=self.device_id)
        )
        json = await response.json()
        payload = json["body"]["data"][0]["attributes"]
        # r = requests.get(self.STATE_URL.format(deviceid=self.id))
        # payload = r.json()["body"]["data"][0]["attributes"]

        output = dict()
        for (payload_key, attribute) in payload.items():
            for (category, local_key) in self.category_keys.items():
                if payload_key == local_key:
                    if category in self.state_keys.keys():
                        for (value_key, value) in self.state_keys[category].items():
                            if attribute == value:
                                output[category] = value_key
                    else:
                        output[category] = int(attribute)

        return output
