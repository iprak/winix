"""Tests for Winix Number entity (dehumidifier timer)."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.const import ATTR_TIMER, WINIX_DOMAIN
from custom_components.winix.number import (
    NUMBER_DESCRIPTIONS,
    WinixNumberEntity,
    async_setup_entry,
)
from homeassistant.core import HomeAssistant

from .common import build_fake_manager  # noqa: TID251


def _mock_dehumidifier_wrapper(index: int = 0) -> MagicMock:
    """Return a MagicMock device_wrapper configured as a dehumidifier."""
    wrapper = MagicMock()
    wrapper.device_stub.mac = f"aabbccddee{index:02x}"
    wrapper.device_stub.alias = f"Dehumidifier{index}"
    wrapper.device_stub.model = "modelX"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_dehumidifier = True
    wrapper.async_set_timer = AsyncMock()
    return wrapper


def _mock_purifier_wrapper() -> MagicMock:
    """Return a MagicMock device_wrapper configured as an air purifier."""
    wrapper = MagicMock()
    wrapper.is_dehumidifier = False
    return wrapper


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def test_setup_platform_adds_timer_for_dehumidifiers(
    hass: HomeAssistant,
) -> None:
    """Timer entity is created only for dehumidifier wrappers."""
    manager = MagicMock()
    manager.get_device_wrappers = Mock(
        return_value=[_mock_dehumidifier_wrapper(0), _mock_purifier_wrapper()]
    )
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id1")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WinixNumberEntity)


async def test_setup_platform_multiple_dehumidifiers(hass: HomeAssistant) -> None:
    """One timer entity is created per dehumidifier."""
    manager = MagicMock()
    manager.get_device_wrappers = Mock(
        return_value=[_mock_dehumidifier_wrapper(0), _mock_dehumidifier_wrapper(1)]
    )
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id2")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 2


async def test_setup_platform_no_dehumidifiers(hass: HomeAssistant) -> None:
    """No number entities are added when there are no dehumidifiers."""
    manager = MagicMock()
    manager.get_device_wrappers = Mock(
        return_value=[_mock_purifier_wrapper(), _mock_purifier_wrapper()]
    )
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id3")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 0


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_construction() -> None:
    """unique_id and entity_description are properly set; ranges match spec."""
    wrapper = _mock_dehumidifier_wrapper()
    description = NUMBER_DESCRIPTIONS[0]  # timer

    entity = WinixNumberEntity(wrapper, Mock(), description)

    assert entity.unique_id is not None
    assert "timer" in entity.unique_id
    assert entity.entity_description is description
    assert entity.native_min_value == 0
    assert entity.native_max_value == 24
    assert entity.native_step == 1


# ---------------------------------------------------------------------------
# native_value
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({ATTR_TIMER: 0}, 0),
        ({ATTR_TIMER: 8}, 8),
        ({ATTR_TIMER: 24}, 24),
        ({}, None),
    ],
)
def test_native_value(state, expected) -> None:
    """native_value returns the timer value from device state."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=state)

    description = NUMBER_DESCRIPTIONS[0]  # timer
    entity = WinixNumberEntity(wrapper, Mock(), description)

    assert entity.native_value == expected


# ---------------------------------------------------------------------------
# async_set_native_value
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("hours", [0, 1, 8, 24])
async def test_async_set_native_value(hass: HomeAssistant, hours: int) -> None:
    """Setting a value delegates to async_set_timer with an integer argument."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={ATTR_TIMER: 0})

    description = NUMBER_DESCRIPTIONS[0]  # timer
    entity = WinixNumberEntity(wrapper, build_fake_manager(1), description)
    entity.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    entity.entity_id = entity.unique_id

    await entity.async_set_native_value(float(hours))

    wrapper.async_set_timer.assert_called_once_with(hours)
