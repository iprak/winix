"""The Winix Air Purifier component."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from http import HTTPStatus
import json
from typing import Any

import aiohttp
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
from winix import WinixAccount, auth

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_FILTER_ALARM_DURATION,
    DEFAULT_POST_TIMEOUT,
    LOGGER,
    WINIX_DOMAIN,
)
from .device_wrapper import MyWinixDeviceStub

HEADERS = {
    "Content-Type": "application/octet-stream",
    "Accept": "application/octet-stream",
}


class Helpers:
    """Utility helper class."""

    # Key and IV used by the Winix mobile app for AES-256-CBC encryption/decryption.
    # See https://github.com/regaw-leinad/winix-api/blob/main/src/account/winix-crypto.ts
    _AES_KEY = bytes.fromhex(
        "84be38f854e320dd4a0a8c7fe0f3a9b84c288445916933fc222465bbd5a518d0"
    )
    _AES_IV = bytes.fromhex("dfd55f316e72e97b905f8739005c99a7")

    _MOBILE_APP_METADATA = {
        "cognitoClientSecretKey": auth.COGNITO_CLIENT_SECRET_KEY,
        "osType": "android",
        "osVersion": "29",
        "mobileLang": "en",
        "appVersion": "1.5.6",
        "mobileModel": "SM-G988B",
    }

    @staticmethod
    def json_loads(text: str) -> dict[str, Any]:
        """Safely load JSON from a string and return a dictionary."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def encrypt(payload: dict[str, Any]) -> str:
        """AES-256-CBC encrypt the payload and return the ciphertext as a string."""
        payload_text = json.dumps(payload)
        plaintext = payload_text.encode("utf-8")

        padded_plaintext = pad(plaintext, AES.block_size)

        cipher = AES.new(Helpers._AES_KEY, AES.MODE_CBC, Helpers._AES_IV)
        return cipher.encrypt(padded_plaintext)

    @staticmethod
    def decrypt(ciphertext: bytes) -> str:
        """AES-256-CBC decrypt the ciphertext and return the plaintext as a string."""

        cipher = AES.new(Helpers._AES_KEY, AES.MODE_CBC, Helpers._AES_IV)
        decrypted_padded_plaintext = cipher.decrypt(ciphertext)

        # Decrypt the data
        return unpad(decrypted_padded_plaintext, AES.block_size)

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
        uuid = WinixAccount(access_token).get_uuid()

        try:
            Helpers._register_user(access_token, uuid, username)
            Helpers._check_access_token(access_token, uuid)
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

            uuid = WinixAccount(reponse.access_token).get_uuid()
            LOGGER.debug("Attempting access token check")

            try:
                Helpers._check_access_token(reponse.access_token, uuid)
            except Exception as err:  # pylint: disable=broad-except
                raise WinixException.from_winix_exception(err) from err

            LOGGER.debug("Re-authentication successful")
            return reponse

        return await hass.async_add_executor_job(_refresh, response)

    @staticmethod
    def _build_mobile_app_payload(
        access_token: str, uuid: str, **kwargs
    ) -> dict[str, str]:
        """Build a payload that matches the current mobile app metadata."""

        return {
            "accessToken": access_token,
            "uuid": uuid,
            **Helpers._MOBILE_APP_METADATA,
            **kwargs,
        }

    @staticmethod
    def _check_access_token(access_token: str, uuid: str) -> None:
        """Validate the access token with Winix cloud using current app metadata.

        Raises WinixException.
        """

        resp = requests.post(
            "https://us.mobile.winix-iot.com/checkAccessToken",
            headers=HEADERS,
            data=Helpers.encrypt(Helpers._build_mobile_app_payload(access_token, uuid)),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(binary_data)
        response_json = Helpers.json_loads(response_json_text)

        if resp.status_code != HTTPStatus.OK:
            response_json["message"] = (
                f"Error while performing RPC checkAccessToken ({resp.status_code})"
            )
            raise WinixException(response_json)

    @staticmethod
    def _register_user(access_token: str, uuid: str, email: str) -> None:
        """Register the generated mobile identity with the Winix backend.

        Raises WinixException.
        """

        resp = requests.post(
            "https://us.mobile.winix-iot.com/registerUser",
            headers=HEADERS,
            data=Helpers.encrypt(
                Helpers._build_mobile_app_payload(access_token, uuid, email=email)
            ),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(binary_data)
        response_json = Helpers.json_loads(response_json_text)

        if resp.status_code != HTTPStatus.OK:
            response_json["message"] = (
                f"Error while performing RPC registerUser ({resp.status_code})"
            )
            raise WinixException(response_json)

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
            headers=HEADERS,
            data=Helpers.encrypt(
                {
                    "accessToken": access_token,
                    "uuid": uuid,
                }
            ),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(await binary_data.read())
        response_json = Helpers.json_loads(response_json_text)

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
