"""Tests for Winix Air Conditioner climate entity."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.winix.climate import (
    FAN_MODE_TURBO,
    FAN_SPEEDS,
    SWING_OFF,
    SWING_ON,
    WinixAirConditioner,
    async_setup_entry,
)
from custom_components.winix.const import WINIX_DOMAIN
from homeassistant.components.climate import ClimateEntityFeature, HVACMode
from homeassistant.core import HomeAssistant

from .common import build_fake_manager  # noqa: TID251


def build_air_conditioner(
    hass: HomeAssistant, device_wrapper: Mock
) -> WinixAirConditioner:
    """Return an initialized WinixAirConditioner instance."""
    device = WinixAirConditioner(device_wrapper, build_fake_manager(1))
    device.add_to_platform_start(hass, MagicMock(platform_name="test-platform"), None)
    device.entity_id = device.unique_id
    return device


def _mock_ac_wrapper() -> Mock:
    """Return a MagicMock device_wrapper configured for air conditioner tests."""
    wrapper = MagicMock()
    wrapper.device_stub.mac = "aabbccddeeff"
    wrapper.device_stub.alias = "AirConditioner1"
    wrapper.device_stub.model = "AC100"
    wrapper.device_stub.sw_version = "1.0"
    wrapper.is_air_conditioner = True
    wrapper.ac_power_on = False
    wrapper.ac_mode = None
    wrapper.ac_target_temperature = None
    wrapper.ac_current_temperature = None
    wrapper.ac_fan_speed = None
    wrapper.ac_swing_on = False
    wrapper.ac_turbo_on = False
    wrapper.ac_power_consumption = None
    wrapper.async_ac_turn_on = AsyncMock()
    wrapper.async_ac_turn_off = AsyncMock()
    wrapper.async_ac_set_mode = AsyncMock()
    wrapper.async_ac_set_target_temperature = AsyncMock()
    wrapper.async_ac_set_fan_speed = AsyncMock()
    wrapper.async_ac_set_swing = AsyncMock()
    wrapper.async_ac_set_turbo = AsyncMock()
    return wrapper


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


async def test_setup_platform_adds_only_air_conditioners(hass: HomeAssistant) -> None:
    """Only wrappers where is_air_conditioner=True should be added."""
    ac_wrapper = MagicMock()
    ac_wrapper.device_stub.mac = "aabbccddeeff"
    ac_wrapper.device_stub.alias = "AirConditioner"
    ac_wrapper.device_stub.model = "AC100"
    ac_wrapper.device_stub.sw_version = "1"
    ac_wrapper.is_air_conditioner = True

    purifier_wrapper = MagicMock()
    purifier_wrapper.is_air_conditioner = False

    manager = MagicMock()
    manager.get_device_wrappers = Mock(return_value=[ac_wrapper, purifier_wrapper])
    manager.async_request_refresh = AsyncMock()

    config = MockConfigEntry(domain=WINIX_DOMAIN, data={}, entry_id="id1")
    config.runtime_data = manager
    async_add_entities = Mock()

    await async_setup_entry(hass, config, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], WinixAirConditioner)


# ---------------------------------------------------------------------------
# Construction & static attributes
# ---------------------------------------------------------------------------


def test_construction(hass: HomeAssistant) -> None:
    """Test entity construction and static attributes."""
    wrapper = _mock_ac_wrapper()

    device = WinixAirConditioner(wrapper, Mock())

    assert device.unique_id is not None
    assert device.min_temp == 18
    assert device.max_temp == 30
    assert set(device.hvac_modes) == {
        HVACMode.OFF,
        HVACMode.AUTO,
        HVACMode.COOL,
        HVACMode.FAN_ONLY,
        HVACMode.DRY,
    }
    assert device.fan_modes == [*FAN_SPEEDS, FAN_MODE_TURBO]
    assert device.swing_modes == [SWING_OFF, SWING_ON]
    assert (
        device.supported_features
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    assert device.device_info is not None


def test_hvac_modes_do_not_include_heat() -> None:
    """The unit has no heating capability, so HEAT must not be exposed."""
    wrapper = _mock_ac_wrapper()
    device = WinixAirConditioner(wrapper, Mock())

    assert HVACMode.HEAT not in device.hvac_modes


# ---------------------------------------------------------------------------
# hvac_mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("power_on", "mode", "expected"),
    [
        (False, "cool", HVACMode.OFF),  # powered off wins regardless of mode
        (True, "auto", HVACMode.AUTO),
        (True, "cool", HVACMode.COOL),
        (True, "fan_only", HVACMode.FAN_ONLY),
        (True, "dry", HVACMode.DRY),
        (True, "unknown-mode", HVACMode.OFF),  # unrecognized mode falls back to OFF
    ],
)
def test_hvac_mode(power_on, mode, expected) -> None:
    """hvac_mode derives from ac_power_on and ac_mode."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_power_on = power_on
    wrapper.ac_mode = mode

    device = WinixAirConditioner(wrapper, Mock())
    assert device.hvac_mode == expected


# ---------------------------------------------------------------------------
# current_temperature / target_temperature
# ---------------------------------------------------------------------------


def test_current_and_target_temperature() -> None:
    """Temperatures are read straight from the wrapper."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_current_temperature = 26
    wrapper.ac_target_temperature = 24

    device = WinixAirConditioner(wrapper, Mock())
    assert device.current_temperature == 26
    assert device.target_temperature == 24


# ---------------------------------------------------------------------------
# fan_mode
# ---------------------------------------------------------------------------


def test_fan_mode_turbo_takes_priority() -> None:
    """fan_mode reports 'turbo' whenever turbo is on, regardless of fan speed."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_turbo_on = True
    wrapper.ac_fan_speed = 3

    device = WinixAirConditioner(wrapper, Mock())
    assert device.fan_mode == FAN_MODE_TURBO


@pytest.mark.parametrize("speed", [1, 2, 3, 4, 5])
def test_fan_mode_reports_speed(speed) -> None:
    """fan_mode reports the numeric speed when turbo is off."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_turbo_on = False
    wrapper.ac_fan_speed = speed

    device = WinixAirConditioner(wrapper, Mock())
    assert device.fan_mode == str(speed)


def test_fan_mode_none_when_speed_unknown() -> None:
    """fan_mode is None when no fan speed has been reported yet."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_turbo_on = False
    wrapper.ac_fan_speed = None

    device = WinixAirConditioner(wrapper, Mock())
    assert device.fan_mode is None


# ---------------------------------------------------------------------------
# swing_mode / extra_state_attributes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("swing_on", "expected"), [(True, SWING_ON), (False, SWING_OFF)]
)
def test_swing_mode(swing_on, expected) -> None:
    """swing_mode reflects ac_swing_on."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_swing_on = swing_on

    device = WinixAirConditioner(wrapper, Mock())
    assert device.swing_mode == expected


def test_extra_state_attributes_exposes_power_consumption() -> None:
    """power_consumption_w attribute is exposed for convenience."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_power_consumption = 512

    device = WinixAirConditioner(wrapper, Mock())
    assert device.extra_state_attributes == {"power_consumption_w": 512}


# ---------------------------------------------------------------------------
# async_set_hvac_mode
# ---------------------------------------------------------------------------


async def test_async_set_hvac_mode_off(hass: HomeAssistant) -> None:
    """Setting HVACMode.OFF turns the unit off without touching mode."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_power_on = True

    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_hvac_mode(HVACMode.OFF)

    wrapper.async_ac_turn_off.assert_called_once()
    wrapper.async_ac_set_mode.assert_not_called()
    refresh.assert_called_once()


async def test_async_set_hvac_mode_turns_on_if_needed(hass: HomeAssistant) -> None:
    """Setting a non-OFF mode while powered off also turns the unit on first."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_power_on = False

    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_hvac_mode(HVACMode.COOL)

    wrapper.async_ac_turn_on.assert_called_once()
    wrapper.async_ac_set_mode.assert_called_once_with("cool")
    refresh.assert_called_once()


async def test_async_set_hvac_mode_skips_turn_on_when_already_on(
    hass: HomeAssistant,
) -> None:
    """Setting a non-OFF mode while already powered on does not re-send power-on."""
    wrapper = _mock_ac_wrapper()
    wrapper.ac_power_on = True

    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh"):
        await device.async_set_hvac_mode(HVACMode.DRY)

    wrapper.async_ac_turn_on.assert_not_called()
    wrapper.async_ac_set_mode.assert_called_once_with("dry")


async def test_async_set_hvac_mode_unsupported_is_ignored(hass: HomeAssistant) -> None:
    """An unsupported HVAC mode logs an error and does nothing else."""
    wrapper = _mock_ac_wrapper()

    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_hvac_mode(HVACMode.HEAT)

    wrapper.async_ac_turn_on.assert_not_called()
    wrapper.async_ac_turn_off.assert_not_called()
    wrapper.async_ac_set_mode.assert_not_called()
    refresh.assert_not_called()


# ---------------------------------------------------------------------------
# async_turn_on / async_turn_off
# ---------------------------------------------------------------------------


async def test_async_turn_on(hass: HomeAssistant) -> None:
    """Turn on delegates to device_wrapper and schedules a refresh."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_turn_on()

    wrapper.async_ac_turn_on.assert_called_once()
    refresh.assert_called_once()


async def test_async_turn_off(hass: HomeAssistant) -> None:
    """Turn off delegates to device_wrapper and schedules a refresh."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_turn_off()

    wrapper.async_ac_turn_off.assert_called_once()
    refresh.assert_called_once()


# ---------------------------------------------------------------------------
# async_set_temperature
# ---------------------------------------------------------------------------


async def test_async_set_temperature(hass: HomeAssistant) -> None:
    """Setting temperature delegates to device_wrapper and schedules a refresh."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_temperature(temperature=22)

    wrapper.async_ac_set_target_temperature.assert_called_once_with(22)
    refresh.assert_called_once()


async def test_async_set_temperature_ignores_missing_value(
    hass: HomeAssistant,
) -> None:
    """No-op when ATTR_TEMPERATURE is absent from kwargs."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_temperature(humidity=50)

    wrapper.async_ac_set_target_temperature.assert_not_called()
    refresh.assert_not_called()


# ---------------------------------------------------------------------------
# async_set_fan_mode
# ---------------------------------------------------------------------------


async def test_async_set_fan_mode_turbo(hass: HomeAssistant) -> None:
    """Setting fan_mode to 'turbo' delegates to async_ac_set_turbo."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_fan_mode(FAN_MODE_TURBO)

    wrapper.async_ac_set_turbo.assert_called_once_with(True)
    wrapper.async_ac_set_fan_speed.assert_not_called()
    refresh.assert_called_once()


@pytest.mark.parametrize("speed", FAN_SPEEDS)
async def test_async_set_fan_mode_speed(hass: HomeAssistant, speed) -> None:
    """Setting fan_mode to a numeric speed delegates to async_ac_set_fan_speed."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_fan_mode(speed)

    wrapper.async_ac_set_fan_speed.assert_called_once_with(int(speed))
    refresh.assert_called_once()


async def test_async_set_fan_mode_unsupported_is_ignored(hass: HomeAssistant) -> None:
    """An unsupported fan_mode logs an error and does nothing else."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_fan_mode("not-a-real-speed")

    wrapper.async_ac_set_fan_speed.assert_not_called()
    wrapper.async_ac_set_turbo.assert_not_called()
    refresh.assert_not_called()


# ---------------------------------------------------------------------------
# async_set_swing_mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("swing_mode", "expected"), [(SWING_ON, True), (SWING_OFF, False)]
)
async def test_async_set_swing_mode(hass: HomeAssistant, swing_mode, expected) -> None:
    """Setting swing_mode delegates to device_wrapper and schedules a refresh."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with patch.object(device, "_async_write_state_and_schedule_refresh") as refresh:
        await device.async_set_swing_mode(swing_mode)

    wrapper.async_ac_set_swing.assert_called_once_with(expected)
    refresh.assert_called_once()


# ---------------------------------------------------------------------------
# _async_write_state_and_schedule_refresh
# ---------------------------------------------------------------------------


async def test_write_state_schedules_delayed_refresh(hass: HomeAssistant) -> None:
    """The helper writes state immediately and schedules a delayed coordinator refresh."""
    wrapper = _mock_ac_wrapper()
    device = build_air_conditioner(hass, wrapper)

    with (
        patch.object(device, "async_write_ha_state") as write_state,
        patch(
            "custom_components.winix.climate.async_call_later"
        ) as call_later,
    ):
        device._async_write_state_and_schedule_refresh()  # noqa: SLF001

    write_state.assert_called_once()
    call_later.assert_called_once()
    # Second positional arg is the delay in seconds.
    assert call_later.call_args[0][1] == 4
