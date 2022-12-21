"""The Winix Air Purifier component."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from homeassistant.core import HomeAssistant
import requests

from custom_components.winix.device_wrapper import MyWinixDeviceStub
from winix import WinixAccount, auth

from .const import WINIX_DOMAIN

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """API exception occurred when fail to authenticate."""

    def __init__(self, error_code: str):
        """Create instance of AuthenticationError."""
        self.error_code = error_code
        super().__init__(self.error_code)


class Helpers:
    """Utility helper class."""

    cognito_idp = boto3.client(
        "cognito-idp",
        config=Config(signature_version=UNSIGNED),
        region_name="us-east-1",
    )

    @staticmethod
    def get_aws_error_code(err) -> str | None:
        """Parse error code from AWS exception."""

        if not err:
            return None

        # https://stackoverflow.com/questions/60703127/how-to-catch-botocore-errorfactory-usernotfoundexception
        try:
            response = err.response
            if response:
                return response.get("Error", {}).get("Code")
            return None
        except AttributeError:
            return None

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
        """Log in."""
        return await hass.async_add_executor_job(Helpers._login, username, password)

    @staticmethod
    async def async_refresh_auth(
        hass: HomeAssistant, response: auth.WinixAuthResponse
    ) -> auth.WinixAuthResponse:
        """Refresh authentication."""

        return await hass.async_add_executor_job(
            Helpers._refresh,
            response,
        )

    @staticmethod
    async def async_get_device_stubs(hass: HomeAssistant, access_token: str):
        """Get device list."""
        return await hass.async_add_executor_job(
            Helpers._get_device_stubs, access_token
        )

    @staticmethod
    def _login(username: str, password: str) -> auth.WinixAuthResponse:
        """Log in."""

        try:
            response = auth.login(username, password)

            # The next 3 operations can raise generic or botocore exceptions
            access_token = response.access_token
            account = WinixAccount(access_token)
            account.register_user(username)
            account.check_access_token()

        except Exception as err:  # pylint: disable=broad-except
            code = Helpers.get_aws_error_code(err)
            raise AuthenticationError(code) from err

        expires_at = (datetime.now() + timedelta(seconds=3600)).timestamp()
        _LOGGER.info("Token expires %d", expires_at)

        return response

    @staticmethod
    def _refresh(response: auth.WinixAuthResponse) -> auth.WinixAuthResponse:
        """Refresh authentication."""

        try:
            reponse = auth.refresh(
                user_id=response.user_id, refresh_token=response.refresh_token
            )
            account = WinixAccount(response.access_token)
            account.check_access_token()
            return reponse

        except Exception as err:  # pylint: disable=broad-except
            code = Helpers.get_aws_error_code(err)
            raise AuthenticationError(code) from err

    @staticmethod
    def _get_device_stubs(access_token: str):
        """
        Get device list.

        Modified from https://github.com/hfern/winix to support extraction of additional attributes.
        """

        resp = requests.post(
            "https://us.mobile.winix-iot.com/getDeviceInfoList",
            json={
                "accessToken": access_token,
                "uuid": WinixAccount(access_token).get_uuid(),
            },
            timeout=5,
        )

        if resp.status_code != 200:
            raise Exception(
                f"Error while performing RPC checkAccessToken ({resp.status_code}): {resp.text}"
            )

        return [
            MyWinixDeviceStub(
                id=d["deviceId"],
                mac=d["mac"],
                alias=d["deviceAlias"],
                location_code=d["deviceLocCode"],
                filter_replace_date=d["filterReplaceDate"],
                model=d["modelName"],
                sw_version=d["mcuVer"],
            )
            for d in resp.json()["deviceInfoList"]
        ]
