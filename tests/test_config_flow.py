"""Test config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.winix.const import WINIX_DOMAIN
from custom_components.winix.helpers import WinixException
from homeassistant import data_entry_flow
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

TEST_USER_DATA = {
    CONF_USERNAME: "user_name",
    CONF_PASSWORD: "password",
}

LOGIN_AUTH_RESPONSE = {
    "user_id": "test_userid",
    "access_token": "AccessToken",
    "refresh_token": "RefreshToken",
    "id_token": "IdToken",
}


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_form(hass: HomeAssistant) -> None:
    """Test that form shows up."""

    result = await hass.config_entries.flow.async_init(
        WINIX_DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_invalid_user(hass: HomeAssistant) -> None:
    """Test user validation in form."""

    with patch(
        "custom_components.winix.Helpers.async_login",
        side_effect=WinixException(
            {"result_code": "UserNotFoundException", "message": "User not found"}
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            WINIX_DOMAIN, context={"source": SOURCE_USER}, data=TEST_USER_DATA
        )
        assert result["errors"]["base"] == "invalid_user"
        assert result["step_id"] == "user"
        assert result["type"] == data_entry_flow.FlowResultType.FORM


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_invalid_authentication(hass: HomeAssistant) -> None:
    """Test user authentication in form."""

    with patch(
        "custom_components.winix.Helpers.async_login",
        side_effect=WinixException(
            {"result_code": "failure", "message": "Authentication failed"}
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            WINIX_DOMAIN, context={"source": SOURCE_USER}, data=TEST_USER_DATA
        )

        assert result["errors"]["base"] == "invalid_auth"
        assert result["step_id"] == "user"
        assert result["type"] == data_entry_flow.FlowResultType.FORM


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_create_entry(hass: HomeAssistant) -> None:
    """Test that entry is created."""

    with patch(
        "custom_components.winix.Helpers.async_login",
        side_effect=AsyncMock(return_value=LOGIN_AUTH_RESPONSE),
    ):
        result = await hass.config_entries.flow.async_init(
            WINIX_DOMAIN, context={"source": SOURCE_USER}, data=TEST_USER_DATA
        )

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
