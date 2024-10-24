"""The WinixDriver component."""

from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Modified from https://github.com/hfern/winix to support async operations


class WinixDriver:
    """WinixDevice driver."""

    # pylint: disable=line-too-long
    CTRL_URL = "https://us.api.winix-iot.com/common/control/devices/{deviceid}/A211/{attribute}:{value}"
    STATE_URL = "https://us.api.winix-iot.com/common/event/sttus/devices/{deviceid}"
    PARAM_URL = "https://us.api.winix-iot.com/common/event/param/devices/{deviceid}"
    CONNECTED_STATUS_URL = (
        "https://us.api.winix-iot.com/common/event/connsttus/devices/{deviceid}"
    )

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

    def __init__(self, device_id: str, client: aiohttp.ClientSession) -> None:
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
        _LOGGER.debug("_rpc_attr attribute=%s, value=%s", attr, value)
        resp = await self._client.get(
            self.CTRL_URL.format(deviceid=self.device_id, attribute=attr, value=value),
            raise_for_status=True,
        )
        raw_resp = await resp.text()
        _LOGGER.debug("_rpc_attr response=%s", raw_resp)

    async def get_filter_life(self) -> int | None:
        """Get the total filter life."""
        response = await self._client.get(
            self.PARAM_URL.format(deviceid=self.device_id)
        )
        json = await response.json()

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

        try:
            attributes = json["body"]["data"][0]["attributes"]
            if attributes:
                return int(attributes["P01"])
        except Exception:  # pylint: disable=broad-except # noqa: BLE001
            return None

    async def get_state(self) -> dict[str, str]:
        """Get device state."""

        # All devices seem to have max 9 months filter life so don't need to call this API.
        # await self.get_filter_life()

        response = await self._client.get(
            self.STATE_URL.format(deviceid=self.device_id)
        )
        json = await response.json()

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
        """

        output = {}

        try:
            _LOGGER.debug(json)
            payload = json["body"]["data"][0]["attributes"]
        except Exception as err:  # pylint: disable=broad-except # noqa: BLE001
            _LOGGER.error(
                "Error parsing response json, received %s", json, exc_info=err
            )

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
                    else:
                        output[category] = int(attribute)

        return output
