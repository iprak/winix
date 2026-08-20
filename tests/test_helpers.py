"""Tests for Winix helpers component."""

from http import HTTPStatus
import json
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.winix.const import (
    DEFAULT_FILTER_MAX_LIFE_HOURS,
    DEFAUT_MODEL_FILTER_MAX_LIFE,
)
from custom_components.winix.helpers import Helpers


@pytest.fixture
def mock_client():
    """Create a mock aiohttp ClientSession."""
    return AsyncMock()


@pytest.fixture
def configure_mock_response(mock_client):
    """Configure the client with an encrypted model filter response."""

    def _configure(response_data, status=HTTPStatus.OK):
        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)
        return mock_response

    return _configure


class TestGetModelsFilterMaxLife:
    """Tests for Helpers.get_models_filter_max_life method."""

    async def test_get_models_filter_max_life_single_model(
        self, mock_client, configure_mock_response
    ):
        """Test getting filter max life with a single model."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 5000,
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {"c545": 5000}
        mock_client.post.assert_called_once()

    async def test_get_models_filter_max_life_multiple_models(
        self, mock_client, configure_mock_response
    ):
        """Test getting filter max life with multiple models across groups."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 5000,
                                }
                            ],
                        },
                        {
                            "modelId": "c635",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 6000,
                                }
                            ],
                        },
                    ]
                },
                {
                    "modelInfoList": [
                        {
                            "modelId": "a401",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 7200,
                                }
                            ],
                        }
                    ]
                },
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {"c545": 5000, "c635": 6000, "a401": 7200}

    async def test_get_models_filter_max_life_uppercase_conversion(
        self, mock_client, configure_mock_response
    ):
        """Test that model IDs are converted to uppercase."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 5000,
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert "c545" in result
        assert "C545" not in result

    async def test_get_models_filter_max_life_missing_filter_info_uses_default(
        self, mock_client, configure_mock_response
    ):
        """Test that missing filterInfoList uses default filter max life."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": None,
                        }
                    ]
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {"c545": DEFAULT_FILTER_MAX_LIFE_HOURS}

    async def test_get_models_filter_max_life_missing_filter_max_life_uses_default(
        self, mock_client, configure_mock_response
    ):
        """Test that missing filterMaxLife property uses default."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": [
                                {
                                    # filterMaxLife is missing
                                }
                            ],
                        }
                    ]
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {"c545": DEFAULT_FILTER_MAX_LIFE_HOURS}

    async def test_get_models_filter_max_life_empty_model_group_list(
        self, mock_client, configure_mock_response
    ):
        """Test with empty modelGroupInfoList."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {"modelGroupInfoList": []}

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {}

    async def test_get_models_filter_max_life_missing_model_group_info_list(
        self, mock_client, configure_mock_response
    ):
        """Test with missing modelGroupInfoList key."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {}

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            # Act
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {}

    async def test_get_models_filter_max_life_empty_model_info_list(
        self, mock_client, configure_mock_response
    ):
        """Test with empty modelInfoList in a group."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [],
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {}

    async def test_get_models_filter_max_life_calls_post_with_correct_params(
        self, mock_client, configure_mock_response
    ):
        """Test that the POST request is made with correct parameters."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {"modelGroupInfoList": []}

        configure_mock_response(response_data)

        with (
            patch.object(
                Helpers, "encrypt", return_value=b"encrypted_data"
            ) as mock_encrypt,
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            await Helpers.get_models_filter_max_life(mock_client, access_token, uuid)

        # Assert
        mock_client.post.assert_called_once_with(
            "https://us.mobile.winix-iot.com/getAllModelGroupInfoList",
            headers={
                "Content-Type": "application/octet-stream",
                "Accept": "application/octet-stream",
            },
            data=b"encrypted_data",
            timeout=5,
        )

        mock_encrypt.assert_called_once_with(
            {"accessToken": access_token, "uuid": uuid}
        )

    async def test_get_models_filter_max_life_mixed_models_with_and_without_filters(
        self, mock_client, configure_mock_response
    ):
        """Test handling of models with and without filter info."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {
            "modelGroupInfoList": [
                {
                    "modelInfoList": [
                        {
                            "modelId": "c545",
                            "filterInfoList": [
                                {
                                    "filterMaxLife": 5000,
                                }
                            ],
                        },
                        {
                            "modelId": "c635",
                            # No filterInfoList
                        },
                    ]
                }
            ]
        }

        configure_mock_response(response_data)

        with (
            patch.object(Helpers, "encrypt", return_value=b"encrypted_data"),
            patch.object(
                Helpers, "decrypt", return_value=json.dumps(response_data).encode()
            ),
        ):
            result = await Helpers.get_models_filter_max_life(
                mock_client, access_token, uuid
            )

        # Assert
        assert result == {
            "c545": 5000,
            "c635": DEFAULT_FILTER_MAX_LIFE_HOURS,
        }

    async def test_get_models_filter_max_life_request_timeout_uses_defaults(
        self, mock_client
    ):
        """Test that a request timeout uses default model filter lifetimes."""
        mock_client.post = AsyncMock(side_effect=TimeoutError("request timed out"))

        result = await Helpers.get_models_filter_max_life(
            mock_client, "test_access_token", "test_uuid"
        )

        assert result == DEFAUT_MODEL_FILTER_MAX_LIFE

    async def test_get_models_filter_max_life_http_error_uses_defaults(
        self, mock_client, configure_mock_response
    ):
        """Test that a non-200 response uses default model filter lifetimes."""
        mock_response = configure_mock_response(
            {}, status=HTTPStatus.SERVICE_UNAVAILABLE
        )

        result = await Helpers.get_models_filter_max_life(
            mock_client, "test_access_token", "test_uuid"
        )

        assert result == DEFAUT_MODEL_FILTER_MAX_LIFE
        mock_response.read.assert_not_awaited()
