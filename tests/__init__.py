"""Tests for Winix component."""

from unittest.mock import MagicMock, Mock

from voluptuous.validators import Number

from custom_components.winix.device_wrapper import WinixDeviceWrapper
from custom_components.winix.fan import WinixPurifier
from custom_components.winix.manager import WinixManager


def build_mock_wrapper(index: Number = 0) -> WinixDeviceWrapper:
    """Return a mocked WinixDeviceWrapper instance."""
    client = Mock()

    device_stub = Mock()

    device_stub.mac = f"f190d35456d{index}"
    device_stub.alias = f"Purifier{index}"

    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()

    return WinixDeviceWrapper(client, device_stub, logger)


def build_fake_manager(wrapper_count) -> WinixManager:
    """Return a mocked WinixManager instance."""
    wrappers = []

    # Prepare fake wrappers
    for index in range(0, wrapper_count):
        wrappers.append(build_mock_wrapper(index))

    manager = MagicMock()
    manager.get_device_wrappers = Mock(return_value=wrappers)
    return manager


def build_purifier(hass, device_wrapper: WinixDeviceWrapper) -> WinixPurifier:
    """Return a WinixPurifier instance."""

    device = WinixPurifier(device_wrapper, Mock())
    device.add_to_platform_start(hass, None, None)

    # Use unique_id as entity_id, this is required for async_update_ha_state
    device.entity_id = device.unique_id
    return device
