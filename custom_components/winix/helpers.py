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

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .cloud import (
    MOBILE_APP_VERSION,
    MOBILE_MODEL,
    WinixAuthResponse,
    generate_uuid,
    login as cloud_login,
    refresh as cloud_refresh,
    resolve_identity_id,
)
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
        "osType": "android",
        "osVersion": "29",
        "mobileLang": "en",
        "appVersion": MOBILE_APP_VERSION,
        "mobileModel": MOBILE_MODEL,
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
    ) -> WinixAuthResponse:
        """Log in asynchronously."""

        return await hass.async_add_executor_job(Helpers.login, username, password)

    @staticmethod
    def login(username: str, password: str) -> WinixAuthResponse:
        """Log in synchronously."""

        try:
            response = cloud_login(username, password)
        except Exception as err:  # pylint: disable=broad-except
            raise WinixException.from_aws_exception(err) from err

        access_token = response.access_token
        uuid = generate_uuid(access_token)

        try:
            response.identity_id = resolve_identity_id(response.id_token)
            Helpers._register_user(
                access_token, uuid, username, response.identity_id
            )
            Helpers._init_session(access_token, uuid)
            Helpers._check_access_token(access_token, uuid, response.identity_id)
        except Exception as err:  # pylint: disable=broad-except
            raise WinixException.from_winix_exception(err) from err

        expires_at = response.expires_at or (
            datetime.now() + timedelta(seconds=3600)
        ).timestamp()
        LOGGER.debug("Login successful, token expires %.0f", expires_at)
        return response

    @staticmethod
    async def async_refresh_auth(
        hass: HomeAssistant, username: str, response: WinixAuthResponse
    ) -> WinixAuthResponse:
        """Refresh authentication.

        Raises WinixException.
        """

        def _refresh(username: str, response: WinixAuthResponse) -> WinixAuthResponse:
            LOGGER.debug("Attempting re-authentication")

            try:
                refreshed_response = cloud_refresh(
                    user_id=response.user_id, refresh_token=response.refresh_token
                )
            except Exception as err:  # pylint: disable=broad-except
                raise WinixException.from_aws_exception(err) from err

            uuid = generate_uuid(refreshed_response.access_token)
            LOGGER.debug("Attempting session re-establishment")

            try:
                refreshed_response.identity_id = resolve_identity_id(
                    refreshed_response.id_token
                )
                Helpers._register_user(
                    refreshed_response.access_token,
                    uuid,
                    username,
                    refreshed_response.identity_id,
                )
                Helpers._init_session(refreshed_response.access_token, uuid)
                Helpers._check_access_token(
                    refreshed_response.access_token,
                    uuid,
                    refreshed_response.identity_id,
                )
            except Exception as err:  # pylint: disable=broad-except
                raise WinixException.from_winix_exception(err) from err

            LOGGER.debug("Re-authentication successful")
            return refreshed_response

        return await hass.async_add_executor_job(_refresh, username, response)

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
    def _register_user(
        access_token: str, uuid: str, email: str, identity_id: str
    ) -> None:
        """Register the generated mobile identity with the Winix backend.

        Raises WinixException.
        """

        resp = requests.post(
            "https://us.mobile.winix-iot.com/registerUser",
            headers=HEADERS,
            data=Helpers.encrypt(
                Helpers._build_mobile_app_payload(
                    access_token, uuid, email=email, identityId=identity_id
                )
            ),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(binary_data)
        response_json = Helpers.json_loads(response_json_text)
        Helpers._ensure_mobile_success("registerUser", resp.status_code, response_json)

    @staticmethod
    def _init_session(access_token: str, uuid: str) -> None:
        """Initialize the Winix mobile session for the new cloud flow."""

        resp = requests.post(
            "https://us.mobile.winix-iot.com/init",
            headers=HEADERS,
            data=Helpers.encrypt(
                Helpers._build_mobile_app_payload(access_token, uuid, region="US")
            ),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(binary_data)
        response_json = Helpers.json_loads(response_json_text)
        Helpers._ensure_mobile_success("init", resp.status_code, response_json)

    @staticmethod
    def _check_access_token(access_token: str, uuid: str, identity_id: str) -> None:
        """Validate the access token with Winix cloud using current app metadata.

        Raises WinixException.
        """

        resp = requests.post(
            "https://us.mobile.winix-iot.com/checkAccessToken",
            headers=HEADERS,
            data=Helpers.encrypt(
                Helpers._build_mobile_app_payload(
                    access_token, uuid, identityId=identity_id
                )
            ),
            timeout=DEFAULT_POST_TIMEOUT,
        )

        binary_data = resp.content
        response_json_text = Helpers.decrypt(binary_data)
        response_json = Helpers.json_loads(response_json_text)
        Helpers._ensure_mobile_success(
            "checkAccessToken", resp.status_code, response_json
        )

    @staticmethod
    def _ensure_mobile_success(
        operation: str, status_code: int, response_json: dict[str, Any]
    ) -> None:
        """Validate the decrypted mobile API response."""

        result_code = str(response_json.get("resultCode", ""))
        result_message = response_json.get("resultMessage", "")

        if status_code == HTTPStatus.OK and (not result_code or result_code == "200"):
            return

        response_json["message"] = (
            f"Error while performing RPC {operation} ({status_code})"
        )
        response_json["result_code"] = result_code
        response_json["result_message"] = result_message
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

        LOGGER.debug(f"getFilterAlarmInfo: {response_json}")

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

        result_code = str(response_json.get("resultCode", "200"))
        result_message = response_json.get("resultMessage", "")
        if resp.status != HTTPStatus.OK or result_code != "200":
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


class WinixException(HomeAssistantError):
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
