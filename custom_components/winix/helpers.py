"""The Winix Air Purifier component."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from http import HTTPStatus

import aiohttp
from winix import WinixAccount, auth

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_FILTER_ALARM_DURATION,
    DEFAULT_POST_TIMEOUT,
    LOGGER,
    WINIX_DOMAIN,
)
from .device_wrapper import MyWinixDeviceStub


class Helpers:
    """Utility helper class."""

    @staticmethod
    def send_notification(
        hass: HomeAssistant, notification_id: str, title: str, message: str
    ) -> None:
        """Display a persistent notification."""
        hass.async_create_task(
            hass.services.async_call(
                domain="persistent_notification",
                service="create",
                service_data={
                    "title": title,
                    "message": message,
                    "notification_id": f"{WINIX_DOMAIN}.{notification_id}",
                },
            )
        )

    @staticmethod
    async def async_login(
        hass: HomeAssistant, username: str, password: str
    ) -> auth.WinixAuthResponse:
        """Log in asynchronously."""

        return await hass.async_add_executor_job(Helpers.login, username, password)

    @staticmethod
    def login(username: str, password: str) -> auth.WinixAuthResponse:
        """Log in synchronously."""

        try:
            response = auth.login(username, password)
        except Exception as err:  # pylint: disable=broad-except
            raise WinixException.from_aws_exception(err) from err

        access_token = response.access_token
        account = WinixAccount(access_token)

        # The next 2 operations can raise generic or botocore exceptions
        try:
            account.register_user(username)
            account.check_access_token()
        except Exception as err:  # pylint: disable=broad-except
            raise WinixException.from_winix_exception(err) from err

        expires_at = (datetime.now() + timedelta(seconds=3600)).timestamp()
        LOGGER.debug("Login successful, token expires %d", expires_at)
        return response

    @staticmethod
    async def async_refresh_auth(
        hass: HomeAssistant, response: auth.WinixAuthResponse
    ) -> auth.WinixAuthResponse:
        """Refresh authentication.

        Raises WinixException.
        """

        def _refresh(response: auth.WinixAuthResponse) -> auth.WinixAuthResponse:
            LOGGER.debug("Attempting re-authentication")

            try:
                reponse = auth.refresh(
                    user_id=response.user_id, refresh_token=response.refresh_token
                )
            except Exception as err:  # pylint: disable=broad-except
                raise WinixException.from_aws_exception(err) from err

            account = WinixAccount(response.access_token)
            LOGGER.debug("Attempting access token check")

            try:
                account.check_access_token()
            except Exception as err:  # pylint: disable=broad-except
                raise WinixException.from_winix_exception(err) from err

            LOGGER.debug("Re-authentication successful")
            return reponse

        return await hass.async_add_executor_job(_refresh, response)

    @staticmethod
    async def get_filter_alarm_duration(
        client: aiohttp.ClientSession,
        access_token: str,
        uuid: str,
        device_id: str,
    ) -> int:
        """Get filter change duration reminder in hours.

        Raises WinixException.
        """

        resp = await client.post(
            "https://us.mobile.winix-iot.com/getFilterAlarmInfo",
            json={
                "accessToken": access_token,
                "uuid": uuid,
                "deviceId": device_id,
            },
            timeout=DEFAULT_POST_TIMEOUT,
        )

        if resp.status != HTTPStatus.OK:
            raise WinixException(
                {
                    "message": "Failed to get filterAlarmInfo.",
                }
            )

        response_json = await resp.json()

        # Sample json
        # {'resultCode': '200', 'resultMessage': 'SUCCESS', 'filterUsageAlarm': 9}
        LOGGER.debug(f"getFilterAlarmInfo: {response_json}")

        # Fall back to 9 months if filter alram has been turned off in mobile app in which case we receive this:
        # {'resultCode': '200', 'resultMessage': 'SUCCESS', 'filterUsageAlarm': 0}
        value = int(response_json["filterUsageAlarm"])

        if value == 0:
            value = DEFAULT_FILTER_ALARM_DURATION
        return value * 30 * 24

    @staticmethod
    async def get_device_stubs(
        client: aiohttp.ClientSession, access_token: str, uuid: str
    ) -> list[MyWinixDeviceStub]:
        """Get device list.

        Raises WinixException.
        """

        # Modified from https://github.com/hfern/winix to support additional attributes.

        # com.google.gson.k kVar = new com.google.gson.k();
        # kVar.p("accessToken", deviceMainActivity2.f2938o);
        # kVar.p("uuid", Common.w(deviceMainActivity2.f2934k));
        # new com.winix.smartiot.util.o0(deviceMainActivity2.f2934k, "https://us.mobile.winix-iot.com/getDeviceInfoList", kVar).a(new TypeToken<g4.v>() {
        #  // from class: com.winix.smartiot.activity.DeviceMainActivity.9
        # }, new com.winix.smartiot.activity.d(deviceMainActivity2, 4));

        resp = await client.post(
            "https://us.mobile.winix-iot.com/getDeviceInfoList",
            json={
                "accessToken": access_token,
                "uuid": uuid,
            },
            timeout=DEFAULT_POST_TIMEOUT,
        )

        response_json = await resp.json()

        if resp.status != HTTPStatus.OK:
            err_data = response_json
            result_code = err_data.get("resultCode")
            result_message = err_data.get("resultMessage")

            raise WinixException(
                {
                    "message": f"Failed to get device list (code-{result_code}). {result_message}.",
                    "result_code": result_code,
                    "result_message": result_message,
                }
            )

        return [
            MyWinixDeviceStub(
                id=item.get("deviceId"),
                mac=item.get("mac"),
                alias=item.get("deviceAlias"),
                location_code=item.get("deviceLocCode"),
                filter_replace_date=item.get("filterReplaceDate"),
                model=item.get("modelName"),
                sw_version=item.get("mcuVer"),
            )
            for item in response_json["deviceInfoList"]
        ]


class WinixException(Exception):
    """Wiinx related operation exception."""

    result_code: str = ""
    """Error code."""
    result_message: str = ""
    """Error code message."""

    def __init__(self, values: dict) -> None:
        """Create instance of WinixException."""

        if values:
            super().__init__(values.get("message", "Unknown error"))
            self.result_code: str = values.get("result_code", "")
            self.result_message: str = values.get("result_message", "")
        else:
            super().__init__("Unknown error")

    @staticmethod
    def from_winix_exception(err: Exception) -> WinixException:
        """Build exception for Winix library operation."""
        return WinixException(WinixException.parse_winix_exception(err))

    @staticmethod
    def from_aws_exception(err: Exception) -> WinixException:
        """Build exception for AWS operation."""
        return WinixException(WinixException.parse_aws_exception(err))

    @staticmethod
    def parse_winix_exception(err: Exception) -> Mapping[str, str]:
        """Parse Winix library exception message."""

        message = str(err)
        if message.find(":") == -1:
            return {"message": message}

        pcs = message.partition(":")
        if pcs[0].rfind("(") == -1:
            return {"message": message}

        pcs2 = pcs[0].rpartition("(")
        return {
            "message": message,
            "result_code": pcs2[2].rstrip(")"),
            "result_message": pcs[2],
        }

    @staticmethod
    def parse_aws_exception(err: Exception) -> Mapping[str, str]:
        """Parse AWS operation exception."""
        message = str(err)

        # https://stackoverflow.com/questions/60703127/how-to-catch-botocore-errorfactory-usernotfoundexception
        try:
            response = err.response
            if response:
                return {
                    "message": message,
                    "result_code": response.get("Error", {}).get("Code"),
                }

        except AttributeError:
            return {"message": message}
        else:
            return None
