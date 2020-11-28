"""The Winix AirPurifier component."""

import logging
from typing import Dict

import aiohttp
import requests

from winix import WinixDeviceStub

from .const import (
    ATTR_AIRFLOW,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    ATTR_POWER_ON_VALUE,
    DOMAIN,
    SPEED_LIST,
    SPEED_AUTO,
    SPEED_SLEEP,
    SPEED_OFF,
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
        self.logger = logger

    async def update(self) -> None:
        """Update the device data."""
        self._state = await self.driver.get_state()
        self._on = self._state.get(ATTR_POWER) == ATTR_POWER_ON_VALUE

        self.logger.debug(
            "%s: updated, fan is %s",
            self.info.alias,
            ("on" if self._on else "off"),
        )

    def get_state(self) -> Dict[str, str]:
        """Return the device data."""
        return self._state

    def is_on(self) -> bool:
        """Return true if fan is on."""
        return self._on

    async def async_turn_on(self) -> None:
        """Turn the fan on."""
        self.logger.debug("Turning on")
        await self.driver.on()
        self._on = True

    async def async_turn_off(self) -> None:
        """Turn the purifier off."""
        self.logger.debug("Turning off")
        await self.driver.off()
        self._on = False

    async def async_ensure_on(self) -> None:
        """Turn on, if not on"""
        if not self._on:
            await self.async_turn_on()

    async def async_plasmawave_on(self) -> None:
        """Turn plasma wave on."""
        self.logger.debug("Turning plasmawave on")
        await self.async_ensure_on()
        await self.driver.plasmawave_on()
        self._state[ATTR_PLASMA] = "on"

    async def async_plasmawave_off(self) -> None:
        """Turn plasma wave off."""
        self.logger.debug("Turning plasmawave off")

        # Turning plasmawave off should not need to turn the fan on
        await self.driver.plasmawave_off()
        self._state[ATTR_PLASMA] = "off"

    async def async_auto(self) -> None:
        """Put the purifier in auto mode."""
        self.logger.debug("Setting auto mode")
        await self.async_ensure_on()
        await self.driver.auto()
        self._state[ATTR_MODE] = "auto"

    async def async_manual(self) -> None:
        """Put the purifier in manual mode."""
        self.logger.debug("Setting manual mode")
        await self.async_ensure_on()
        await self.driver.manual()
        self._state[ATTR_MODE] = "manual"

    async def async_set_speed(self, speed) -> None:
        if speed == SPEED_OFF:
            await self.async_turn_off()
        elif speed == SPEED_AUTO:
            await self.async_auto()
        elif speed in SPEED_LIST:
            # Setting speed requires the fan to be in manual mode
            await self.async_manual()

            self.logger.debug("Setting speed to '%s'", speed)
            await getattr(self.driver, speed)()
            self._state[ATTR_AIRFLOW] = speed
        else:
            self.logger.error("%s is an invalid speed option", speed)


# Modified from https://github.com/hfern/winix to support async operations
class WinixDevice:
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

    def __init__(self, id: str, client: aiohttp.ClientSession):
        self.id = id
        self._client = client

    async def off(self):
        await self._rpc_attr(
            self.category_keys["power"], self.state_keys["power"]["off"]
        )

    async def on(self):
        await self._rpc_attr(
            self.category_keys["power"], self.state_keys["power"]["on"]
        )

    async def auto(self):
        await self._rpc_attr(
            self.category_keys["mode"], self.state_keys["mode"]["auto"]
        )

    async def manual(self):
        await self._rpc_attr(
            self.category_keys["mode"], self.state_keys["mode"]["manual"]
        )

    async def plasmawave_off(self):
        await self._rpc_attr(
            self.category_keys["plasma"], self.state_keys["plasma"]["off"]
        )

    async def plasmawave_on(self):
        await self._rpc_attr(
            self.category_keys["plasma"], self.state_keys["plasma"]["on"]
        )

    async def low(self):
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["low"]
        )

    async def medium(self):
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["medium"]
        )

    async def high(self):
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["high"]
        )

    async def turbo(self):
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["turbo"]
        )

    async def sleep(self):
        await self._rpc_attr(
            self.category_keys["airflow"], self.state_keys["airflow"]["sleep"]
        )

    async def _rpc_attr(self, attr: str, value: str):
        await self._client.get(
            self.CTRL_URL.format(deviceid=self.id, attribute=attr, value=value)
        )
        # requests.get(
        #     self.CTRL_URL.format(deviceid=self.id, attribute=attr, value=value)
        # )

    async def get_state(self) -> Dict[str, str]:
        response = await self._client.get(self.STATE_URL.format(deviceid=self.id))
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
