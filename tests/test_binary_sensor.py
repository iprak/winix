"""Tests for Winix Binary Sensor entity (dehumidifier water tank)."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    WinixBinarySensor,
    async_setup_entry,
)
from custom_components.winix.const import WINIX_DOMAIN
from homeassistant.core import HomeAssistant


def _mock_dehumidifier_wrapper(index: int = 0) -> MagicMock:
    """Return a MagicMock device_wrapper configured as a dehumidifier."""
    wrapper = MagicMock()
    wrapper.device_stub.mac = f"aabbccddee{index:02x}"
    wrapper.device_stub.alias = f"Dehumidifier{index}"
    wrapper.device_stub.model = "modelX"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_dehumidifier = True
    return wrapper


def _mock_purifier_wrapper() -> MagicMock:
    """Return a MagicMock device_wrapper configured as an air purifier."""
    wrapper = MagicMock()
    wrapper.is_dehumidifier = False
    return wrapper


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def test_setup_platform_adds_water_tank_for_dehumidifiers(
    hass: HomeAssistant,
) -> None:
    """Binary sensor is created only for dehumidifier wrappers."""
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
    # Only the dehumidifier should receive a water tank sensor
    assert len(entities) == 1
    assert isinstance(entities[0], WinixBinarySensor)


async def test_setup_platform_multiple_dehumidifiers(hass: HomeAssistant) -> None:
    """One water tank binary sensor is created per dehumidifier."""
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
    """No binary sensors are added when there are no dehumidifiers."""
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
    """unique_id and entity_description are properly set."""
    wrapper = _mock_dehumidifier_wrapper()
    description = BINARY_SENSOR_DESCRIPTIONS[0]  # water_tank

    sensor = WinixBinarySensor(wrapper, Mock(), description)

    assert sensor.unique_id is not None
    assert "water_tank" in sensor.unique_id
    assert sensor.entity_description is description


# ---------------------------------------------------------------------------
# is_on (water tank full/detached = problem)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("is_water_tank_available", "expected_is_on"),
    [
        (True, False),   # tank available (not full, not detached) -> no problem
        (False, True),   # tank full or detached -> problem reported
    ],
)
def test_water_tank_is_on(is_water_tank_available: bool, expected_is_on: bool) -> None:
    """is_on is True when the water tank is full or detached (not available)."""
    wrapper = _mock_dehumidifier_wrapper()
    type(wrapper).is_water_tank_available = is_water_tank_available

    description = BINARY_SENSOR_DESCRIPTIONS[0]  # water_tank
    sensor = WinixBinarySensor(wrapper, Mock(), description)

    assert sensor.is_on == expected_is_on
