"""Tests for Winix component."""

from unittest.mock import MagicMock, Mock

from custom_components.winix import WinixManager
from custom_components.winix.WinixDeviceWrapper import WinixDeviceWrapper
from custom_components.winix.fan import WinixPurifier


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


def build_purifier(hass, device_wrapper: WinixDeviceWrapper) -> WinixPurifier:
    """Return a WinixPurifier instance."""

    device = WinixPurifier(device_wrapper)
    device.add_to_platform_start(hass, None, None)

    # Use unique_id as entity_id, this is required for async_update_ha_state
    device.entity_id = device.unique_id
    return device
