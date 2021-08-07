"""Test WinixDeviceWrapper component."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.winix import WinixDeviceWrapper
from custom_components.winix.const import (
    AIRFLOW_HIGH,
    AIRFLOW_LOW,
    AIRFLOW_SLEEP,
    ATTR_AIRFLOW,
    ATTR_MODE,
    ATTR_PLASMA,
    ATTR_POWER,
    MODE_AUTO,
    MODE_MANUAL,
    OFF_VALUE,
    ON_VALUE,
    PRESET_MODE_AUTO,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA,
    PRESET_MODE_SLEEP,
)


def build_mock_wrapper() -> WinixDeviceWrapper:
    """Returns a mock WinixDeviceWrapper."""
    client = Mock()
    device_stub = Mock()

    logger = Mock()
    logger.debug = Mock()
    logger.warning = Mock()

    return WinixDeviceWrapper(client, device_stub, logger)


@pytest.mark.parametrize(
    "mock_state, is_auto, is_manual, is_on, is_plasma_on, is_sleep",
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
):
    """Tests WinixDeviceWrapper states."""

    with patch(
        "custom_components.winix.WinixDevice.get_state",
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


async def test_async_turn_on():
    with patch("custom_components.winix.WinixDevice.turn_on") as turn_on:
        wrapper = build_mock_wrapper()
        assert not wrapper.is_on  # initially off

        await wrapper.async_ensure_on()
        assert wrapper.is_on
        assert turn_on.call_count == 1

        await wrapper.async_ensure_on()  # Test turning it on again
        assert turn_on.call_count == 1  # Should not do anything


async def test_async_turn_off():
    with patch("custom_components.winix.WinixDevice.turn_on") as turn_on, patch(
        "custom_components.winix.WinixDevice.turn_off"
    ) as turn_off:
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


async def test_async_turn_on():
    wrapper = build_mock_wrapper()

    wrapper.async_ensure_on = AsyncMock()
    wrapper.async_auto = AsyncMock()

    await wrapper.async_turn_on()

    assert wrapper.async_ensure_on.call_count == 1
    assert wrapper.async_auto.call_count == 1


async def test_async_auto():
    # async_auto does not need the device to be turned on
    with patch("custom_components.winix.WinixDevice.auto") as auto:
        wrapper = build_mock_wrapper()

        await wrapper.async_auto()
        assert auto.call_count == 1

        assert wrapper.is_auto
        assert not wrapper.is_manual
        assert not wrapper.is_plasma_on  # unchanged
        assert not wrapper.is_sleep
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_LOW

        await wrapper.async_auto()  # Calling again should not do anything
        assert auto.call_count == 1


async def test_async_plasmawave_on_off():
    # async_plasmawave does not need the device to be turned on
    with patch(
        "custom_components.winix.WinixDevice.plasmawave_on"
    ) as plasmawave_on, patch(
        "custom_components.winix.WinixDevice.plasmawave_off"
    ) as plasmawave_off:
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


async def test_async_manual():
    # async_manual does not need the device to be turned on
    with patch("custom_components.winix.WinixDevice.manual") as manual:
        wrapper = build_mock_wrapper()

        await wrapper.async_manual()
        assert manual.call_count == 1

        assert not wrapper.is_auto
        assert wrapper.is_manual
        assert not wrapper.is_plasma_on  # unchanged
        assert not wrapper.is_sleep
        assert wrapper.get_state().get(ATTR_MODE) == MODE_MANUAL
        assert wrapper.get_state().get(ATTR_AIRFLOW) == AIRFLOW_LOW

        await wrapper.async_manual()  # Calling again should not do anything
        assert manual.call_count == 1


async def test_async_sleep():
    # async_sleep does not need the device to be turned on
    with patch("custom_components.winix.WinixDevice.sleep") as sleep:
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


async def test_async_set_speed():
    with patch("custom_components.winix.WinixDevice.turn_on"), patch(
        "custom_components.winix.WinixDevice.manual"
    ), patch("custom_components.winix.WinixDevice.high") as high_speed, patch(
        "custom_components.winix.WinixDevice.low"
    ) as low_speed:
        wrapper = build_mock_wrapper()

        await wrapper.async_set_speed(AIRFLOW_LOW)
        assert high_speed.call_count == 0
        assert low_speed.call_count == 1
        assert wrapper.is_on
        assert not wrapper.is_auto
        assert wrapper.is_manual

        # Calling again at same speed does nothing
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
    "preset_mode, sleep, auto, manual, plasmawave_off, plasmawave_on",
    [
        (PRESET_MODE_SLEEP, 1, 0, 0, 0, 0),
        (PRESET_MODE_AUTO, 0, 1, 0, 0, 0),
        (PRESET_MODE_MANUAL, 0, 0, 1, 1, 0),
        (PRESET_MODE_MANUAL_PLASMA, 0, 0, 1, 0, 1),
    ],
)
async def test_async_set_preset_mode(
    preset_mode, sleep, auto, manual, plasmawave_off, plasmawave_on
):
    wrapper = build_mock_wrapper()

    wrapper.async_ensure_on = AsyncMock()
    wrapper.async_sleep = AsyncMock()
    wrapper.async_auto = AsyncMock()
    wrapper.async_manual = AsyncMock()
    wrapper.async_plasmawave_off = AsyncMock()
    wrapper.async_plasmawave_on = AsyncMock()

    await wrapper.async_set_preset_mode(preset_mode)
    assert wrapper.async_ensure_on.call_count == 1

    assert wrapper.async_sleep.call_count == sleep
    assert wrapper.async_auto.call_count == auto
    assert wrapper.async_manual.call_count == manual
    assert wrapper.async_plasmawave_off.call_count == plasmawave_off
    assert wrapper.async_plasmawave_on.call_count == plasmawave_on


async def test_async_set_preset_mode_invalid():
    wrapper = build_mock_wrapper()

    await wrapper.async_set_preset_mode("INVALID_PRESET")
    wrapper._logger.warning.call_count == 1