"""Tests for Winix helpers component."""

from http import HTTPStatus
import json
from unittest.mock import AsyncMock

import pytest


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
