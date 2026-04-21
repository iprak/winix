"""The WinixDriver component."""

from __future__ import annotations

from enum import Enum, unique

import aiohttp

from homeassistant.exceptions import HomeAssistantError

from .const import (
    AIR_QUALITY_FAIR,
    AIR_QUALITY_GOOD,
    AIR_QUALITY_POOR,
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    AIRFLOW_MEDIUM,
    AIRFLOW_SLEEP,
    AIRFLOW_TURBO,
    ATTR_AIR_AQI,
    ATTR_AIR_QUALITY,
    ATTR_AIR_QVALUE,
    ATTR_AIRFLOW,
    ATTR_AMBIENT_LIGHT,
    ATTR_BRIGHTNESS_LEVEL,
    ATTR_CHILD_LOCK,
    ATTR_CURRENT_HUMIDITY,
    ATTR_FILTER_HOUR,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_PM25,
    ATTR_POWER,
    ATTR_TARGET_HUMIDITY,
    ATTR_TIMER,
    ATTR_UV_SANITIZE,
    ATTR_WATER_TANK,
    AUTO_DRY_VALUE,
    LOGGER,
    MODE_AUTO,
    MODE_CLOTHES,
    MODE_CONTINUOUS,
    MODE_MANUAL,
    MODE_QUIET,
    MODE_SHOES,
    OFF_VALUE,
    ON_VALUE,
)

# Modified from https://github.com/hfern/winix to support async operations


class WinixTransientError(HomeAssistantError):
    """Raised for transient network errors that may resolve on retry."""


@unique
class BrightnessLevel(Enum):
    """Brightness levels."""

    Level0 = 0
    Level1 = 30
    Level2 = 70
    Level3 = 100


class WinixDriver:
    """Base Winix driver."""

    # pylint: disable=line-too-long
    CTRL_URL = "https://us.api.winix-iot.com/common/control/devices/{deviceid}/{identityid}/{attribute}:{value}"
    STATE_URL = "https://us.api.winix-iot.com/common/event/sttus/devices/{deviceid}"

    category_keys: dict[str, str] | None = None
    state_keys: dict[str, dict[str, str]] | None = None

    def __init__(
        self, device_id: str, client: aiohttp.ClientSession, identity_id: str
    ) -> None:
        """Create an instance of WinixDriver."""
        self.device_id = device_id
        self._client = client
        self._identity_id = identity_id

    async def _rpc_attr(self, attr: str, value: str) -> None:
        """Make a raw API call with the given attribute code and value."""
        LOGGER.debug("_rpc_attr attribute=%s, value=%s", attr, value)

        try:
            response = await self._client.get(
                self.CTRL_URL.format(
                    deviceid=self.device_id,
                    identityid=self._identity_id,
                    attribute=attr,
                    value=value,
                )
            )
            response.raise_for_status()
            raw_resp = await response.text()
            LOGGER.debug("_rpc_attr response=%s", raw_resp)
        except aiohttp.ClientResponseError as err:
            raise HomeAssistantError(
                f"Failed to download data: HTTP {err.status}"
            ) from err
        except aiohttp.ClientError as err:
            raise HomeAssistantError(f"Error communicating with Winix: {err}") from err
        except TimeoutError as err:
            raise HomeAssistantError("Timeout communicating with Winix") from err

    async def control(self, category: str, state_key: str) -> None:
        """Control the device using semantic category/state names."""
        await self._rpc_attr(
            self.category_keys[category],
            self.state_keys[category][state_key],
        )

    async def get_state(self) -> dict[str, str | int]:
        """Get device state.

        This raises HomeAssistantError on communication errors, but returns an empty dict if the response is successfully received but doesn't contain expected data.
        This allows callers to handle missing data without crashing.
        """

        try:
            response = await self._client.get(
                self.STATE_URL.format(deviceid=self.device_id)
            )
            response.raise_for_status()
            json = await response.json()
        except aiohttp.ClientResponseError as err:
            raise WinixTransientError(
                f"Failed to download data: HTTP {err.status}"
            ) from err
        except aiohttp.ClientError as err:
            raise WinixTransientError(f"Error communicating with Winix: {err}") from err
        except TimeoutError as err:
            raise WinixTransientError("Timeout communicating with Winix") from err

        # pylint: disable=pointless-string-statement
        """
        {
            'statusCode': 200,
            'headers': {'resultCode': 'S100', 'resultMessage': ''},
            'body': {
                'deviceId': '847207352CE0_364yr8i989', 'totalCnt': 1,
                'data': [
                    {
                        'apiNo': 'A210', 'apiGroup': '001', 'deviceGroup': 'Air01', 'modelId': 'C545',
                        'attributes': {'A02': '0', 'A03': '01', 'A04': '01', 'A05': '01', 'A07': '0', 'A21': '1257', 'S07': '01', 'S08': '74', 'S14': '121'},
                        'rssi': '-55', 'creationTime': 1673449200634, 'utcDatetime': '2023-01-11 15:00:00', 'utcTimestamp': 1673449200
                    }
                ]
            }
        }

        Another sample from https://github.com/iprak/winix/issues/98
        {'statusCode': 200, 'headers': {'resultCode': 'S100', 'resultMessage': 'no data'}, 'body': {}}
        """

        headers = json.get("headers", {})
        if headers.get("resultMessage") == "no data":
            LOGGER.info("No data received")
            return {}

        output = {}

        try:
            LOGGER.debug(json)
            payload = json["body"]["data"][0]["attributes"]
        except Exception as err:  # pylint: disable=broad-except # noqa: BLE001
            LOGGER.error("Error parsing response json, received %s", json, exc_info=err)

            # Return empty object so that callers don't crash (#37)
            return output

        for payload_key, attribute in payload.items():
            for category, local_key in self.category_keys.items():
                if payload_key == local_key:
                    # pylint: disable=consider-iterating-dictionary
                    if category in self.state_keys:
                        for value_key, value in self.state_keys[category].items():
                            if attribute == value:
                                output[category] = value_key
                    elif attribute:
                        try:
                            output[category] = int(attribute)
                        except ValueError:
                            continue

        return output


class AirPurifierDriver(WinixDriver):
    """Winix Air Purifier driver."""

    # pylint: disable=line-too-long
    PARAM_URL = "https://us.api.winix-iot.com/common/event/param/devices/{deviceid}"

    category_keys = {
        ATTR_POWER: "A02",
        ATTR_MODE: "A03",
        ATTR_AIRFLOW: "A04",
        ATTR_AIR_AQI: "A05",
        ATTR_PLASMA: "A07",
        ATTR_CHILD_LOCK: "A08",
        ATTR_BRIGHTNESS_LEVEL: "A16",
        ATTR_FILTER_HOUR: "A21",
        ATTR_AIR_QUALITY: "S07",
        ATTR_AIR_QVALUE: "S08",
        ATTR_PM25: "S04",
        ATTR_AMBIENT_LIGHT: "S14",
    }

    state_keys = {
        ATTR_POWER: {OFF_VALUE: "0", ON_VALUE: "1"},
        ATTR_MODE: {MODE_AUTO: "01", MODE_MANUAL: "02"},
        ATTR_AIRFLOW: {
            AIRFLOW_LOW: "01",
            AIRFLOW_MEDIUM: "02",
            AIRFLOW_HIGH: "03",
            AIRFLOW_TURBO: "05",
            AIRFLOW_SLEEP: "06",
        },
        ATTR_CHILD_LOCK: {OFF_VALUE: "0", ON_VALUE: "1"},
        ATTR_PLASMA: {OFF_VALUE: "0", ON_VALUE: "1"},
        ATTR_AIR_QUALITY: {AIR_QUALITY_GOOD: "01", AIR_QUALITY_FAIR: "02", AIR_QUALITY_POOR: "03"},
    }

    async def turn_off(self) -> None:
        """Turn the device off."""
        await self.control(ATTR_POWER, OFF_VALUE)

    async def turn_on(self) -> None:
        """Turn the device on."""
        await self.control(ATTR_POWER, ON_VALUE)

    async def auto(self) -> None:
        """Set device in auto mode."""
        await self.control(ATTR_MODE, MODE_AUTO)

    async def manual(self) -> None:
        """Set device in manual mode."""
        await self.control(ATTR_MODE, MODE_MANUAL)

    async def child_lock_off(self) -> None:
        """Turn child lock off."""
        await self.control(ATTR_CHILD_LOCK, OFF_VALUE)

    async def child_lock_on(self) -> None:
        """Turn child lock on."""
        await self.control(ATTR_CHILD_LOCK, ON_VALUE)

    async def set_brightness_level(self, value: int) -> bool:
        """Set brightness level."""
        if not any(e.value == value for e in BrightnessLevel):
            return False

        await self._rpc_attr(self.category_keys[ATTR_BRIGHTNESS_LEVEL], str(value))
        return True

    async def plasmawave_off(self) -> None:
        """Turn plasmawave off."""
        await self.control(ATTR_PLASMA, OFF_VALUE)

    async def plasmawave_on(self) -> None:
        """Turn plasmawave on."""
        await self.control(ATTR_PLASMA, ON_VALUE)

    async def low(self) -> None:
        """Set speed low."""
        await self.control(ATTR_AIRFLOW, AIRFLOW_LOW)

    async def medium(self) -> None:
        """Set speed medium."""
        await self.control(ATTR_AIRFLOW, AIRFLOW_MEDIUM)

    async def high(self) -> None:
        """Set speed high."""
        await self.control(ATTR_AIRFLOW, AIRFLOW_HIGH)

    async def turbo(self) -> None:
        """Set speed turbo."""
        await self.control(ATTR_AIRFLOW, AIRFLOW_TURBO)

    async def sleep(self) -> None:
        """Set device in sleep mode."""
        await self.control(ATTR_AIRFLOW, AIRFLOW_SLEEP)

    async def get_filter_life(self) -> int | None:
        """Get the total filter life.

        Not called from get_state() — all devices seem to have a max
        9-month filter life, so polling this API is unnecessary.

        This raises HomeAssistantError on communication errors
        """
        try:
            response = await self._client.get(
                self.PARAM_URL.format(deviceid=self.device_id)
            )
            response.raise_for_status()
            json = await response.json()
        except aiohttp.ClientResponseError as err:
            raise HomeAssistantError(
                f"Failed to download data: HTTP {err.status}"
            ) from err
        except aiohttp.ClientError as err:
            raise HomeAssistantError(f"Error communicating with Winix: {err}") from err
        except TimeoutError as err:
            raise HomeAssistantError("Timeout communicating with Winix") from err

        # pylint: disable=pointless-string-statement
        """
        {
            'statusCode': 200, 'headers': {'resultCode': 'S100', 'resultMessage': ''},
            'body': {
                'deviceId': '847207352CE0_364yr8i989', 'totalCnt': 1,
                'data': [
                    {
                        'apiNo': 'A240', 'apiGroup': '004', 'modelId': 'C545', 'attributes': {'P01': '6480'}
                    }
                ]
            }
        }
        """

        headers = json.get("headers", {})
        if headers.get("resultMessage") == "no data":
            LOGGER.info("No filter life data received")
            return None

        try:
            attributes = json["body"]["data"][0]["attributes"]
            if attributes:
                return int(attributes["P01"])
        except Exception:  # pylint: disable=broad-except # noqa: BLE001
            return None


class DehumidifierDriver(WinixDriver):
    """Winix Dehumidifier driver."""

    category_keys = {
        ATTR_POWER: "D02",
        ATTR_MODE: "D03",
        ATTR_AIRFLOW: "D04",
        ATTR_TARGET_HUMIDITY: "D05",
        ATTR_CHILD_LOCK: "D08",
        ATTR_CURRENT_HUMIDITY: "D10",
        ATTR_WATER_TANK: "D11",
        ATTR_UV_SANITIZE: "D13",
        ATTR_TIMER: "D15",
    }

    state_keys = {
        ATTR_POWER: {
            OFF_VALUE: "0",
            ON_VALUE: "1",
            AUTO_DRY_VALUE: "2",
        },
        ATTR_MODE: {
            MODE_AUTO: "01",
            MODE_MANUAL: "02",
            MODE_CLOTHES: "03",
            MODE_SHOES: "04",
            MODE_QUIET: "05",
            MODE_CONTINUOUS: "06",
        },
        ATTR_AIRFLOW: {
            AIRFLOW_HIGH: "01",
            AIRFLOW_LOW: "02",
            AIRFLOW_TURBO: "03",
        },
        ATTR_CHILD_LOCK: {
            OFF_VALUE: "0",
            ON_VALUE: "1",
        },
        ATTR_WATER_TANK: {
            OFF_VALUE: "0",  # not full and tank attached
            ON_VALUE: "1",  # full or tank detached
        },
        ATTR_UV_SANITIZE: {
            OFF_VALUE: "0",
            ON_VALUE: "1",
        },
    }

    async def turn_on(self) -> None:
        """Turn the device on."""
        await self.control(ATTR_POWER, ON_VALUE)

    async def turn_off(self) -> None:
        """Turn the device off."""
        await self.control(ATTR_POWER, OFF_VALUE)

    async def set_mode(self, mode: str) -> None:
        """Set operating mode."""
        await self.control(ATTR_MODE, mode)

    async def set_fan_speed(self, speed: str) -> None:
        """Set fan speed."""
        await self.control(ATTR_AIRFLOW, speed)

    async def set_humidity(self, humidity: int) -> None:
        """Set target humidity."""
        await self._rpc_attr(self.category_keys[ATTR_TARGET_HUMIDITY], str(humidity))

    async def child_lock_off(self) -> None:
        """Turn child lock off."""
        await self.control(ATTR_CHILD_LOCK, OFF_VALUE)

    async def child_lock_on(self) -> None:
        """Turn child lock on."""
        await self.control(ATTR_CHILD_LOCK, ON_VALUE)

    async def uv_sanitize_off(self) -> None:
        """Turn UV sanitize off."""
        await self.control(ATTR_UV_SANITIZE, OFF_VALUE)

    async def uv_sanitize_on(self) -> None:
        """Turn UV sanitize on."""
        await self.control(ATTR_UV_SANITIZE, ON_VALUE)

    async def set_timer(self, hours: int) -> None:
        """Set timer in hours (0 to disable)."""
        await self._rpc_attr(self.category_keys[ATTR_TIMER], str(hours))
