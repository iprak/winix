"""Tests for Winix Select entities."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.const import WINIX_DOMAIN
from custom_components.winix.select import (
    SELECT_DESCRIPTIONS,
    WinixSelectEntity,
    async_setup_entry,
)
from homeassistant.core import HomeAssistant

from .common import build_fake_manager  # noqa: TID251

# Descriptions by key for convenient lookup
_DESC_BY_KEY = {d.key: d for d in SELECT_DESCRIPTIONS}
BRIGHTNESS_DESC = _DESC_BY_KEY["brightness_level"]
FAN_SPEED_DESC = _DESC_BY_KEY["fan_speed"]


def _mock_dehumidifier_wrapper() -> MagicMock:
    wrapper = MagicMock()
    wrapper.device_stub.mac = "aabbccddeeff"
    wrapper.device_stub.alias = "Dehumidifier1"
    wrapper.device_stub.model = "modelX"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_dehumidifier = True
    wrapper.features.supports_brightness_level = False
    wrapper.async_set_speed = AsyncMock(return_value=True)
    return wrapper


def _mock_purifier_wrapper() -> MagicMock:
    wrapper = MagicMock()
    wrapper.device_stub.mac = "aabbccddeeff"
    wrapper.device_stub.alias = "Purifier1"
    wrapper.device_stub.model = "modelY"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_dehumidifier = False
    wrapper.features.supports_brightness_level = True
    wrapper.async_set_brightness_level = AsyncMock(return_value=True)
    wrapper.is_on = True
    return wrapper


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def test_setup_creates_fan_speed_for_dehumidifier(hass: HomeAssistant) -> None:
    """fan_speed select is created for dehumidifier wrappers; brightness for AP."""
    manager = MagicMock()
    manager.get_device_wrappers = Mock(
        return_value=[_mock_dehumidifier_wrapper(), _mock_purifier_wrapper()]
    )
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id1")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    entities = async_add_entities.call_args[0][0]
    keys = [e.entity_description.key for e in entities]
    assert "fan_speed" in keys
    assert "brightness_level" in keys


# ---------------------------------------------------------------------------
# available -- brightness_level uses available_fn (is_on)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("is_on", "expected_available"),
    [
        (True, True),
        (False, False),
    ],
)
def test_brightness_available_follows_is_on(is_on, expected_available) -> None:
    """brightness_level entity is available only when device is on."""
    wrapper = _mock_purifier_wrapper()
    wrapper.is_on = is_on
    wrapper.get_state = Mock(return_value={})

    entity = WinixSelectEntity(wrapper, Mock(), BRIGHTNESS_DESC)

    assert entity.available == expected_available


# ---------------------------------------------------------------------------
# available -- fan_speed falls back to base WinixEntity.available
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected_available"),
    [
        ({}, True),   # state present -> available regardless of power
        (None, False),  # state None -> unavailable
    ],
)
def test_fan_speed_available_follows_state(state, expected_available) -> None:
    """fan_speed entity is available whenever state is not None (power-agnostic)."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=state)

    entity = WinixSelectEntity(wrapper, Mock(), FAN_SPEED_DESC)

    assert entity.available == expected_available


# ---------------------------------------------------------------------------
# async_select_option -- no coordinator refresh
# ---------------------------------------------------------------------------


async def test_async_select_option_no_coordinator_refresh(hass: HomeAssistant) -> None:
    """Selecting an option must NOT trigger coordinator.async_request_refresh."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={"airflow": "high"})

    coordinator = build_fake_manager(1)
    entity = WinixSelectEntity(wrapper, coordinator, FAN_SPEED_DESC)
    entity.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    entity.entity_id = entity.unique_id

    await entity.async_select_option("low")

    coordinator.async_request_refresh.assert_not_called()
    wrapper.async_set_speed.assert_called_once_with("low")
