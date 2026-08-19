"""Tests for Winix helpers component."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.winix.const import DEFAULT_FILTER_MAX_LIFE_HOURS
from custom_components.winix.helpers import Helpers


@pytest.fixture
def mock_client():
    """Create a mock aiohttp ClientSession."""
    return AsyncMock()


class TestGetModelsFilterMaxLife:
    """Tests for Helpers.get_models_filter_max_life method."""

    async def test_get_models_filter_max_life_single_model(self, mock_client):
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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

    async def test_get_models_filter_max_life_multiple_models(self, mock_client):
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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

    async def test_get_models_filter_max_life_uppercase_conversion(self, mock_client):
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
        self, mock_client
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
        self, mock_client
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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

    async def test_get_models_filter_max_life_empty_model_group_list(self, mock_client):
        """Test with empty modelGroupInfoList."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {"modelGroupInfoList": []}

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
        self, mock_client
    ):
        """Test with missing modelGroupInfoList key."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {}

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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

    async def test_get_models_filter_max_life_empty_model_info_list(self, mock_client):
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
        self, mock_client
    ):
        """Test that the POST request is made with correct parameters."""
        # Arrange
        access_token = "test_access_token"
        uuid = "test_uuid"

        response_data = {"modelGroupInfoList": []}

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
        self, mock_client
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

        encrypted_response = json.dumps(response_data).encode()

        mock_response = AsyncMock()
        mock_response.read = AsyncMock(return_value=encrypted_response)
        mock_client.post = AsyncMock(return_value=mock_response)

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
