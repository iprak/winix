"""Test WinixDeviceWrapper component."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.winix.const import (
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    AIRFLOW_SLEEP,
    AIRFLOW_TURBO,
    ATTR_AIRFLOW,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    ATTR_TARGET_HUMIDITY,
    ATTR_TIMER,
    AUTO_DRY_VALUE,
    DEFAULT_FILTER_ALARM_DURATION_HOURS,
    MODE_AUTO,
    MODE_CONTINUOUS,
    MODE_MANUAL,
    OFF_VALUE,
    ON_VALUE,
    PRESET_MODE_AUTO,
    PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA_OFF,
    PRESET_MODE_SLEEP,
    NumericPresetModes,
)
from custom_components.winix.device_wrapper import WinixDeviceWrapper

from .common import build_mock_dehumidifier_wrapper, build_mock_wrapper  # noqa: TID251

AirPurifierDriver_TypeName = "custom_components.winix.driver.AirPurifierDriver"
DehumidifierDriver_TypeName = "custom_components.winix.driver.DehumidifierDriver"


@pytest.mark.parametrize(
    ("mock_state", "is_auto", "is_manual", "is_on", "is_plasma_on", "is_sleep"),
    [
        # On
        ({}, False, False, False, False, False),
        # On, plasma on
        ({ATTR_POWER: ON_VALUE}, False, False, True, False, False),
        (
            {ATTR_POWER: ON_VALUE, ATTR_PLASMA: ON_VALUE},
            False,
            False,
            True,
            True,
            False,
        ),
        # On, auto
        (
            {ATTR_POWER: ON_VALUE, ATTR_MODE: MODE_AUTO},
            True,
            False,
            True,
            False,
            False,
        ),
        # On, manual
        (
            {ATTR_POWER: ON_VALUE, ATTR_MODE: MODE_MANUAL},
            False,
            True,
            True,
            False,
            False,
        ),
        # On, sleep
        (
            {ATTR_POWER: ON_VALUE, ATTR_AIRFLOW: AIRFLOW_SLEEP},
            False,
            False,
            True,
            False,
            True,
        ),
    ],
)
async def test_wrapper_update(
    mock_state, is_auto, is_manual, is_on, is_plasma_on, is_sleep
) -> None:
    """Tests device wrapper states."""

    with patch(
        f"{AirPurifierDriver_TypeName}.get_state",
        AsyncMock(return_value=mock_state),
    ) as get_state:
        wrapper = build_mock_wrapper()
        await wrapper.update()
        assert get_state.call_count == 1
        assert wrapper.get_state() == mock_state

        assert wrapper.is_auto == is_auto
        assert wrapper.is_manual == is_manual
        assert wrapper.is_on == is_on
        assert wrapper.is_plasma_on == is_plasma_on
        assert wrapper.is_sleep == is_sleep


async def test_async_ensure_on() -> None:
    """Test ensuring device is on."""
    with patch(f"{AirPurifierDriver_TypeName}.turn_on") as turn_on:
        wrapper = build_mock_wrapper()
        assert not wrapper.is_on  # initially off

        await wrapper.async_ensure_on()
        assert wrapper.is_on
        assert turn_on.call_count == 1

        await wrapper.async_ensure_on()  # Test turning it on again
        assert turn_on.call_count == 1  # Should not do anything


async def test_async_turn_off() -> None:
    """Test turning off."""
    with (
        patch(f"{AirPurifierDriver_TypeName}.turn_on") as turn_on,
        patch(f"{AirPurifierDriver_TypeName}.turn_off") as turn_off,
    ):
        wrapper = build_mock_wrapper()
        assert not wrapper.is_on  # initially off

        await wrapper.async_ensure_on()
        assert wrapper.is_on
        assert turn_on.call_count == 1
        assert turn_off.call_count == 0

        await wrapper.async_ensure_on()  # Test turning it on again
        assert turn_on.call_count == 1  # Should not do anything
        assert turn_off.call_count == 0

        await wrapper.async_turn_off()  # Turn it off
        assert turn_on.call_count == 1
        assert turn_off.call_count == 1

        await wrapper.async_turn_off()  # Test turning it off agian

        assert turn_on.call_count == 1
        assert turn_off.call_count == 1  # Should not do anything


async def test_async_turn_on() -> None:
    """Test turning on."""
    wrapper = build_mock_wrapper()

    wrapper.async_ensure_on = AsyncMock()
    wrapper.async_set_mode = AsyncMock()

    await wrapper.async_turn_on()

    assert wrapper.async_ensure_on.call_count == 1
    wrapper.async_set_mode.assert_called_once_with(MODE_AUTO)


async def test_async_set_mode_auto() -> None:
    """Test setting auto mode."""

    # async_set_mode does not need the device to be turned on
    with patch(f"{AirPurifierDriver_TypeName}.auto") as auto:
        wrapper = build_mock_wrapper()

        await wrapper.async_set_mode(MODE_AUTO)
        assert auto.call_count == 1

        assert wrapper.is_auto
        assert not wrapper.is_manual
        assert not wrapper.is_plasma_on  # unchanged
        assert not wrapper.is_sleep
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_LOW

        await wrapper.async_set_mode(MODE_AUTO)  # Calling again should not do anything
        assert auto.call_count == 1


async def test_async_plasmawave_on_off() -> None:
    """Test turning plasmawave on."""

    # async_plasmawave does not need the device to be turned on
    with (
        patch(f"{AirPurifierDriver_TypeName}.plasmawave_on") as plasmawave_on,
        patch(f"{AirPurifierDriver_TypeName}.plasmawave_off") as plasmawave_off,
    ):
        wrapper = build_mock_wrapper()

        await wrapper.async_plasmawave_on()
        assert plasmawave_on.call_count == 1
        assert plasmawave_off.call_count == 0

        assert wrapper.is_plasma_on
        assert wrapper.get_state().get(ATTR_PLASMA) == ON_VALUE

        await wrapper.async_plasmawave_on()  # Calling again should not do anything
        assert plasmawave_on.call_count == 1
        assert plasmawave_off.call_count == 0

        await wrapper.async_plasmawave_off()  # Turn plasma off
        assert not wrapper.is_plasma_on
        assert wrapper.get_state().get(ATTR_PLASMA) == OFF_VALUE
        assert plasmawave_on.call_count == 1
        assert plasmawave_off.call_count == 1

        await wrapper.async_plasmawave_off()  # Calling again should not do anything
        assert plasmawave_on.call_count == 1
        assert plasmawave_off.call_count == 1


async def test_async_set_mode_manual() -> None:
    """Test setting manual mode."""

    # async_set_mode does not need the device to be turned on
    with patch(f"{AirPurifierDriver_TypeName}.manual") as manual:
        wrapper = build_mock_wrapper()

        await wrapper.async_set_mode(MODE_MANUAL)
        assert manual.call_count == 1

        assert not wrapper.is_auto
        assert wrapper.is_manual
        assert not wrapper.is_plasma_on  # unchanged
        assert not wrapper.is_sleep
        assert wrapper.get_state().get(ATTR_MODE) == MODE_MANUAL
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_LOW

        await wrapper.async_set_mode(MODE_MANUAL)  # Calling again should not do anything
        assert manual.call_count == 1


async def test_async_set_mode_unsupported() -> None:
    """Unsupported mode values should be ignored without raising."""

    with (
        patch(f"{AirPurifierDriver_TypeName}.auto") as auto,
        patch(f"{AirPurifierDriver_TypeName}.manual") as manual,
    ):
        wrapper = build_mock_wrapper()

        await wrapper.async_set_mode("not-a-real-mode")

        assert auto.call_count == 0
        assert manual.call_count == 0
        assert not wrapper.is_auto
        assert not wrapper.is_manual


async def test_async_sleep() -> None:
    """Test setting sleep mode."""

    # async_sleep does not need the device to be turned on
    with patch(f"{AirPurifierDriver_TypeName}.sleep") as sleep:
        wrapper = build_mock_wrapper()

        await wrapper.async_sleep()
        assert sleep.call_count == 1

        assert not wrapper.is_auto
        assert not wrapper.is_manual
        assert not wrapper.is_plasma_on
        assert wrapper.is_sleep
        assert wrapper.get_state().get(ATTR_MODE) == MODE_MANUAL
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_SLEEP

        await wrapper.async_sleep()  # Calling again should not do anything
        assert sleep.call_count == 1


async def test_async_set_speed() -> None:
    """Test setting fan speed."""

    with (
        patch(f"{AirPurifierDriver_TypeName}.turn_on"),
        patch(f"{AirPurifierDriver_TypeName}.manual"),
        patch(f"{AirPurifierDriver_TypeName}.high") as high_speed,
        patch(f"{AirPurifierDriver_TypeName}.low") as low_speed,
    ):
        wrapper = build_mock_wrapper()

        await wrapper.async_set_speed(AIRFLOW_LOW)
        assert high_speed.call_count == 0
        assert low_speed.call_count == 1
        assert wrapper.is_on
        assert not wrapper.is_auto
        assert wrapper.is_manual

        high_speed.reset_mock()
        low_speed.reset_mock()

        # Calling again at same speed still fires (guard removed; caller's responsibility)
        await wrapper.async_set_speed(AIRFLOW_LOW)
        assert high_speed.call_count == 0
        assert low_speed.call_count == 1
        assert wrapper.is_on
        assert not wrapper.is_auto
        assert wrapper.is_manual

        # Setting a different speed
        await wrapper.async_set_speed(AIRFLOW_HIGH)
        assert high_speed.call_count == 1
        assert low_speed.call_count == 1
        assert wrapper.is_on
        assert not wrapper.is_auto
        assert wrapper.is_manual


@pytest.mark.parametrize(
    ("preset_mode", "sleep", "auto", "manual", "plasmawave_off", "plasmawave_on"),
    [
        (PRESET_MODE_SLEEP, 1, 0, 0, 0, 0),
        (PRESET_MODE_AUTO, 0, 1, 0, 0, 1),
        (PRESET_MODE_AUTO_PLASMA_OFF, 0, 1, 0, 1, 0),
        (PRESET_MODE_MANUAL, 0, 0, 1, 0, 1),
        (PRESET_MODE_MANUAL_PLASMA_OFF, 0, 0, 1, 1, 0),
        (NumericPresetModes.PRESET_MODE_SLEEP, 1, 0, 0, 0, 0),
        (NumericPresetModes.PRESET_MODE_AUTO, 0, 1, 0, 0, 1),
        (NumericPresetModes.PRESET_MODE_AUTO_PLASMA_OFF, 0, 1, 0, 1, 0),
        (NumericPresetModes.PRESET_MODE_MANUAL, 0, 0, 1, 0, 1),
        (NumericPresetModes.PRESET_MODE_MANUAL_PLASMA_OFF, 0, 0, 1, 1, 0),
    ],
)
async def test_async_set_preset_mode(
    preset_mode, sleep, auto, manual, plasmawave_off, plasmawave_on
) -> None:
    """Test setting preset mode."""

    wrapper = build_mock_wrapper()

    wrapper.async_ensure_on = AsyncMock()
    wrapper.async_sleep = AsyncMock()
    wrapper.async_set_mode = AsyncMock()
    wrapper.async_plasmawave_off = AsyncMock()
    wrapper.async_plasmawave_on = AsyncMock()

    await wrapper.async_set_preset_mode(preset_mode)
    assert wrapper.async_ensure_on.call_count == 1

    assert wrapper.async_sleep.call_count == sleep
    assert wrapper.async_set_mode.call_count == auto + manual
    if auto:
        wrapper.async_set_mode.assert_called_once_with(MODE_AUTO)
    if manual:
        wrapper.async_set_mode.assert_called_once_with(MODE_MANUAL)
    assert wrapper.async_plasmawave_off.call_count == plasmawave_off
    assert wrapper.async_plasmawave_on.call_count == plasmawave_on


async def test_async_set_preset_mode_invalid() -> None:
    """Test invalid preset mode."""

    client = Mock()
    device_stub = Mock()

    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()

    wrapper = WinixDeviceWrapper(
        client,
        device_stub,
        DEFAULT_FILTER_ALARM_DURATION_HOURS,
        logger,
        "test_identity_id",
    )

    with pytest.raises(ValueError):
        await wrapper.async_set_preset_mode("INVALID_PRESET")


async def test_async_set_mode_dehumidifier() -> None:
    """Test setting the dehumidifier operating mode via the unified async_set_mode."""

    with patch(f"{DehumidifierDriver_TypeName}.set_mode") as set_mode:
        wrapper = build_mock_dehumidifier_wrapper()

        await wrapper.async_set_mode(MODE_AUTO)
        set_mode.assert_called_once_with(MODE_AUTO)
        assert wrapper.get_state().get(ATTR_MODE) == MODE_AUTO

        # Same value -> no-op
        await wrapper.async_set_mode(MODE_AUTO)
        assert set_mode.call_count == 1

        # New value -> sends command
        await wrapper.async_set_mode(MODE_CONTINUOUS)
        assert set_mode.call_count == 2
        assert wrapper.get_state().get(ATTR_MODE) == MODE_CONTINUOUS


async def test_async_set_mode_dehumidifier_unsupported() -> None:
    """Unsupported dehumidifier modes should be ignored without raising."""

    with patch(f"{DehumidifierDriver_TypeName}.set_mode") as set_mode:
        wrapper = build_mock_dehumidifier_wrapper()

        await wrapper.async_set_mode("not-a-real-mode")

        assert set_mode.call_count == 0
        assert wrapper.get_state().get(ATTR_MODE) is None


async def test_async_set_speed_dehumidifier() -> None:
    """Test setting the dehumidifier fan speed via the unified async_set_speed."""

    with patch(f"{DehumidifierDriver_TypeName}.set_fan_speed") as set_fan_speed:
        wrapper = build_mock_dehumidifier_wrapper()

        await wrapper.async_set_speed(AIRFLOW_HIGH)
        set_fan_speed.assert_called_once_with(AIRFLOW_HIGH)
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_HIGH

        # Same value -> no-op
        await wrapper.async_set_speed(AIRFLOW_HIGH)
        assert set_fan_speed.call_count == 1

        # New value -> sends command
        await wrapper.async_set_speed(AIRFLOW_TURBO)
        assert set_fan_speed.call_count == 2
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_TURBO


async def test_async_set_humidity() -> None:
    """Test setting the dehumidifier target humidity."""

    with patch(f"{DehumidifierDriver_TypeName}.set_humidity") as set_humidity:
        wrapper = build_mock_dehumidifier_wrapper()

        assert await wrapper.async_set_humidity(50) is True
        set_humidity.assert_called_once_with(50)
        assert wrapper.get_state().get(ATTR_TARGET_HUMIDITY) == 50

        # Same value -> no-op
        assert await wrapper.async_set_humidity(50) is False
        assert set_humidity.call_count == 1

        # New value -> sends command
        assert await wrapper.async_set_humidity(60) is True
        assert set_humidity.call_count == 2
        assert wrapper.get_state().get(ATTR_TARGET_HUMIDITY) == 60


async def test_async_set_timer() -> None:
    """Test setting the dehumidifier timer."""

    with patch(f"{DehumidifierDriver_TypeName}.set_timer") as set_timer:
        wrapper = build_mock_dehumidifier_wrapper()

        # First call should send the command
        assert await wrapper.async_set_timer(3) is True
        set_timer.assert_called_once_with(3)
        assert wrapper.get_state().get(ATTR_TIMER) == 3

        # Calling with the same value should be a no-op
        assert await wrapper.async_set_timer(3) is False
        assert set_timer.call_count == 1

        # A different value should send the command again
        assert await wrapper.async_set_timer(0) is True
        assert set_timer.call_count == 2
        assert wrapper.get_state().get(ATTR_TIMER) == 0


@pytest.mark.parametrize(
    ("power_value", "is_on", "is_auto_dry"),
    [
        (None, False, False),
        (OFF_VALUE, False, False),
        (ON_VALUE, True, False),
        (AUTO_DRY_VALUE, False, True),
    ],
)
async def test_dehumidifier_auto_dry_flag(
    power_value, is_on, is_auto_dry
) -> None:
    """Auto-dry power state is exposed as a dedicated flag."""

    mock_state = {ATTR_POWER: power_value} if power_value is not None else {}
    with patch(
        f"{DehumidifierDriver_TypeName}.get_state",
        AsyncMock(return_value=mock_state),
    ):
        wrapper = build_mock_dehumidifier_wrapper()
        await wrapper.update()

        assert wrapper.is_on is is_on
        assert wrapper.is_auto_dry is is_auto_dry
