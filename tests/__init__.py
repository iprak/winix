"""Tests for Winix component."""

from unittest.mock import MagicMock, Mock

from custom_components.winix import WinixManager
from custom_components.winix.WinixDeviceWrapper import WinixDeviceWrapper


def build_mock_wrapper() -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""
    client = Mock()
    device_stub = Mock()

    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()

    return WinixDeviceWrapper(client, device_stub, logger)


def build_fake_manager(wrapper_count) -> WinixManager:
    """Return a mocked WinixManager instance."""
    wrappers = []

    # Prepare fake wrappers
    for x in range(0, wrapper_count):
        wrappers.append(build_mock_wrapper())

    manager = MagicMock()
    manager.get_device_wrappers = Mock(return_value=wrappers)
    return manager
