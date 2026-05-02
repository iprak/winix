"""Tests for Winix Binary Sensor entities (dehumidifier water tank, auto-dry)."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    WinixBinarySensor,
    async_setup_entry,
)
from custom_components.winix.const import (
    BINARY_SENSOR_AUTO_DRY,
    BINARY_SENSOR_WATER_TANK,
    WINIX_DOMAIN,
)
from homeassistant.core import HomeAssistant

# Description lookup by key — robust to ordering changes.
_DESC_BY_KEY = {d.key: d for d in BINARY_SENSOR_DESCRIPTIONS}
WATER_TANK_DESC = _DESC_BY_KEY[BINARY_SENSOR_WATER_TANK]
AUTO_DRY_DESC = _DESC_BY_KEY[BINARY_SENSOR_AUTO_DRY]

# Number of binary sensors created per dehumidifier wrapper.
PER_DEHUMIDIFIER = len(BINARY_SENSOR_DESCRIPTIONS)


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


async def test_setup_platform_adds_sensors_for_dehumidifiers(
    hass: HomeAssistant,
) -> None:
    """All description-defined sensors are created for dehumidifier wrappers only."""
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
    assert len(entities) == PER_DEHUMIDIFIER
    keys = {e.entity_description.key for e in entities}
    assert keys == {BINARY_SENSOR_WATER_TANK, BINARY_SENSOR_AUTO_DRY}
    assert all(isinstance(e, WinixBinarySensor) for e in entities)


async def test_setup_platform_multiple_dehumidifiers(hass: HomeAssistant) -> None:
    """Each dehumidifier gets the full set of binary sensors."""
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
    assert len(entities) == PER_DEHUMIDIFIER * 2


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


@pytest.mark.parametrize(
    "description",
    [WATER_TANK_DESC, AUTO_DRY_DESC],
    ids=["water_tank", "auto_dry"],
)
def test_construction(description) -> None:
    """unique_id includes the description key; entity_description is set."""
    wrapper = _mock_dehumidifier_wrapper()

    sensor = WinixBinarySensor(wrapper, Mock(), description)

    assert sensor.unique_id is not None
    assert description.key in sensor.unique_id
    assert sensor.entity_description is description


# ---------------------------------------------------------------------------
# water_tank.is_on (full/detached = problem)
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
    wrapper.is_water_tank_available = is_water_tank_available

    sensor = WinixBinarySensor(wrapper, Mock(), WATER_TANK_DESC)

    assert sensor.is_on == expected_is_on


# ---------------------------------------------------------------------------
# auto_dry.is_on (running / not running)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("is_auto_dry", "expected_is_on"),
    [
        (True, True),    # device in auto-dry cycle
        (False, False),  # not in auto-dry
    ],
)
def test_auto_dry_is_on(is_auto_dry: bool, expected_is_on: bool) -> None:
    """is_on mirrors wrapper.is_auto_dry."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.is_auto_dry = is_auto_dry

    sensor = WinixBinarySensor(wrapper, Mock(), AUTO_DRY_DESC)

    assert sensor.is_on == expected_is_on
