"""Tests for Winix Dehumidifier entity."""

from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.const import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_TARGET_HUMIDITY,
    DEHUMIDIFIER_HUMIDITY_STEP,
    DEHUMIDIFIER_MAX_HUMIDITY,
    DEHUMIDIFIER_MIN_HUMIDITY,
    DEHUMIDIFIER_MODES,
    MODE_AUTO,
    MODE_CLOTHES,
    MODE_CONTINUOUS,
    MODE_MANUAL,
    MODE_QUIET,
    MODE_SHOES,
    OFF_VALUE,
    ON_VALUE,
    WINIX_DOMAIN,
)
from custom_components.winix.humidifier import WinixDehumidifier, async_setup_entry
from homeassistant.components.humidifier import (
    HumidifierAction,
    HumidifierEntityFeature,
)
from homeassistant.core import HomeAssistant

from .common import build_fake_manager  # noqa: TID251


def build_dehumidifier(
    hass: HomeAssistant, device_wrapper: Mock
) -> WinixDehumidifier:
    """Return an initialized WinixDehumidifier instance."""
    device = WinixDehumidifier(device_wrapper, build_fake_manager(1))
    device.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    device.entity_id = device.unique_id
    return device


def _mock_dehumidifier_wrapper() -> Mock:
    """Return a MagicMock device_wrapper configured for dehumidifier tests."""
    wrapper = MagicMock()
    wrapper.device_stub.mac = "aabbccddeeff"
    wrapper.device_stub.alias = "Dehumidifier1"
    wrapper.device_stub.model = "modelX"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_dehumidifier = True
    # Default cached flags to off; individual tests override as needed.
    wrapper.is_on = False
    wrapper.is_auto_dry = False
    wrapper.async_turn_on = AsyncMock()
    wrapper.async_turn_off = AsyncMock()
    wrapper.async_set_humidity = AsyncMock()
    wrapper.async_set_mode = AsyncMock()
    return wrapper


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def test_setup_platform_adds_only_dehumidifiers(hass: HomeAssistant) -> None:
    """Only wrappers where is_dehumidifier=True should be added."""
    dehumidifier_wrapper = MagicMock()
    dehumidifier_wrapper.device_stub.mac = "aabbccddeeff"
    dehumidifier_wrapper.device_stub.alias = "Dehumidifier"
    dehumidifier_wrapper.device_stub.model = "X"
    dehumidifier_wrapper.device_stub.sw_version = "1"
    dehumidifier_wrapper.is_dehumidifier = True

    purifier_wrapper = MagicMock()
    purifier_wrapper.is_dehumidifier = False

    manager = MagicMock()
    manager.get_device_wrappers = Mock(
        return_value=[dehumidifier_wrapper, purifier_wrapper]
    )
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id1")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WinixDehumidifier)


# ---------------------------------------------------------------------------
# Construction & static attributes
# ---------------------------------------------------------------------------


def test_construction(hass: HomeAssistant) -> None:
    """Test entity construction and static attributes."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = WinixDehumidifier(wrapper, Mock())

    assert device.unique_id is not None
    assert device.name is None  # primary entity
    assert device.supported_features == HumidifierEntityFeature.MODES
    assert device.min_humidity == DEHUMIDIFIER_MIN_HUMIDITY
    assert device.max_humidity == DEHUMIDIFIER_MAX_HUMIDITY
    assert device.target_humidity_step == DEHUMIDIFIER_HUMIDITY_STEP
    assert device.available_modes == DEHUMIDIFIER_MODES
    assert device.device_info is not None


def test_available_modes_contains_all_modes() -> None:
    """Ensure all expected modes are listed."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = WinixDehumidifier(wrapper, Mock())

    assert set(device.available_modes) == {
        MODE_AUTO,
        MODE_MANUAL,
        MODE_CLOTHES,
        MODE_SHOES,
        MODE_QUIET,
        MODE_CONTINUOUS,
    }


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


def test_available_when_state_is_not_none() -> None:
    """Entity is available when get_state returns a dict."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = WinixDehumidifier(wrapper, Mock())
    assert device.available


def test_unavailable_when_state_is_none() -> None:
    """Entity is unavailable when get_state returns None."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=None)

    device = WinixDehumidifier(wrapper, Mock())
    assert not device.available


# ---------------------------------------------------------------------------
# is_on
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("is_on_flag", "is_auto_dry_flag", "expected"),
    [
        (True, False, True),    # ON
        (False, True, True),    # auto-dry / idle
        (False, False, False),  # off (or before first refresh)
    ],
)
def test_is_on(is_on_flag, is_auto_dry_flag, expected) -> None:
    """is_on combines wrapper.is_on and wrapper.is_auto_dry cached flags."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.is_on = is_on_flag
    wrapper.is_auto_dry = is_auto_dry_flag

    device = WinixDehumidifier(wrapper, Mock())
    assert device.is_on == expected


# ---------------------------------------------------------------------------
# action
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("is_on_flag", "is_auto_dry_flag", "expected_action"),
    [
        (True, False, HumidifierAction.DRYING),
        (False, True, HumidifierAction.IDLE),
        (False, False, HumidifierAction.OFF),
    ],
)
def test_action(is_on_flag, is_auto_dry_flag, expected_action) -> None:
    """Action maps cached flags to HumidifierAction."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.is_on = is_on_flag
    wrapper.is_auto_dry = is_auto_dry_flag
    wrapper.get_state = Mock(return_value={})

    device = WinixDehumidifier(wrapper, Mock())
    assert device.action == expected_action


def test_action_returns_none_when_state_is_none() -> None:
    """Action is None when state is None."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=None)

    device = WinixDehumidifier(wrapper, Mock())
    assert device.action is None


# ---------------------------------------------------------------------------
# mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (None, None),
        ({}, None),
        ({ATTR_MODE: MODE_AUTO}, MODE_AUTO),
        ({ATTR_MODE: MODE_CLOTHES}, MODE_CLOTHES),
    ],
)
def test_mode(state, expected) -> None:
    """Mode returns the current mode from state."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=state)

    device = WinixDehumidifier(wrapper, Mock())
    assert device.mode == expected


# ---------------------------------------------------------------------------
# current_humidity / target_humidity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (None, None),
        ({}, None),
        ({ATTR_CURRENT_HUMIDITY: "55"}, 55),
        ({ATTR_CURRENT_HUMIDITY: "40"}, 40),
    ],
)
def test_current_humidity(state, expected) -> None:
    """current_humidity converts string value to int."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=state)

    device = WinixDehumidifier(wrapper, Mock())
    assert device.current_humidity == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (None, None),
        ({}, None),
        ({ATTR_TARGET_HUMIDITY: "50"}, 50),
        ({ATTR_TARGET_HUMIDITY: "70"}, 70),
    ],
)
def test_target_humidity(state, expected) -> None:
    """target_humidity converts string value to int."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value=state)

    device = WinixDehumidifier(wrapper, Mock())
    assert device.target_humidity == expected


# ---------------------------------------------------------------------------
# async_turn_on / async_turn_off
# ---------------------------------------------------------------------------


async def test_async_turn_on(hass: HomeAssistant) -> None:
    """Turn on delegates to device_wrapper and requests refresh."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={ATTR_POWER: OFF_VALUE})

    device = build_dehumidifier(hass, wrapper)

    await device.async_turn_on()

    wrapper.async_turn_on.assert_called_once()
    device.coordinator.async_request_refresh.assert_called_once()


async def test_async_turn_off(hass: HomeAssistant) -> None:
    """Turn off delegates to device_wrapper and requests refresh."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={ATTR_POWER: ON_VALUE})

    device = build_dehumidifier(hass, wrapper)

    await device.async_turn_off()

    wrapper.async_turn_off.assert_called_once()
    device.coordinator.async_request_refresh.assert_called_once()


# ---------------------------------------------------------------------------
# async_set_humidity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("humidity", [35, 40, 45, 50, 55, 60, 65, 70])
async def test_async_set_humidity_exact_steps(hass: HomeAssistant, humidity: int) -> None:
    """Exact 5-step values are passed through unchanged."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = build_dehumidifier(hass, wrapper)

    await device.async_set_humidity(humidity)

    wrapper.async_set_humidity.assert_called_once_with(humidity)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (34, 35),   # rounds up to min
        (37, 35),   # rounds down (7.4 -> 7 -> 35)
        (38, 40),   # rounds up (7.6 -> 8 -> 40)
        (57, 55),   # rounds down (11.4 -> 11 -> 55)
        (58, 60),   # rounds up (11.6 -> 12 -> 60)
        (71, 70),   # rounds down, then clamped to max
        (0, 35),    # rounds to 0, clamped to min
        (100, 70),  # rounds to 100, clamped to max
    ],
)
async def test_async_set_humidity_rounds_and_clamps(
    hass: HomeAssistant, raw: int, expected: int
) -> None:
    """Non-step or out-of-range values are rounded to nearest step then clamped."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = build_dehumidifier(hass, wrapper)

    await device.async_set_humidity(raw)

    wrapper.async_set_humidity.assert_called_once_with(expected)


# ---------------------------------------------------------------------------
# async_set_mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mode",
    [MODE_AUTO, MODE_MANUAL, MODE_CLOTHES, MODE_SHOES, MODE_QUIET, MODE_CONTINUOUS],
)
async def test_async_set_mode_valid(hass: HomeAssistant, mode: str) -> None:
    """Valid modes delegate to wrapper.async_set_mode without coordinator refresh."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = build_dehumidifier(hass, wrapper)

    await device.async_set_mode(mode)

    wrapper.async_set_mode.assert_called_once_with(mode)
    device.coordinator.async_request_refresh.assert_not_called()


async def test_async_set_mode_passes_through(hass: HomeAssistant) -> None:
    """Entity passes mode through; wrapper is responsible for validation."""
    wrapper = _mock_dehumidifier_wrapper()
    wrapper.get_state = Mock(return_value={})

    device = build_dehumidifier(hass, wrapper)

    await device.async_set_mode("turbo_dry")

    wrapper.async_set_mode.assert_called_once_with("turbo_dry")
