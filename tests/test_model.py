"""Tests for Winix API model definitions."""

import pytest

from custom_components.winix.const import (
    DEFAULT_FILTER_MAX_LIFE_HOURS,
    OVERRIDE_FILTER_MAX_LIFE_HOURS,
)
from custom_components.winix.model import EnumSensorData, ModelsInfo, SensorData


def test_sensor_data_creation_with_defaults() -> None:
    """SensorData optional metadata defaults to None."""
    sensor_data = SensorData(key="pm1", attr_id="S02")

    assert sensor_data.key == "pm1"
    assert sensor_data.attr_id == "S02"
    assert sensor_data.device_class is None


def test_enum_sensor_data_creation_with_defaults() -> None:
    """SensorData stores its provided metadata."""
    sensor_data = EnumSensorData(
        key="pm2_5_level", attr_id="S03", enum_values="01:Good/02:Fair"
    )

    assert sensor_data.key == "pm2_5_level"
    assert sensor_data.attr_id == "S03"
    assert sensor_data.enum_values == "01:Good/02:Fair"


@pytest.mark.parametrize(
    ("model_id", "expected_filter_life"),
    [
        ("t500_au", DEFAULT_FILTER_MAX_LIFE_HOURS),
        ("AZSUUS", OVERRIDE_FILTER_MAX_LIFE_HOURS),
    ],
)
def test_get_filter_max_life(model_id: str, expected_filter_life: int) -> None:
    """Get the default and overridden filter life for a model."""
    models = ModelsInfo()

    assert models.get_filter_max_life(model_id) == expected_filter_life


def test_get_sensors() -> None:
    """Get sensors for a known model, ignoring model ID case."""
    models = ModelsInfo()

    sensors = models.get_sensors("T500_AU")

    assert [(sensor.attr_id, sensor.key) for sensor in sensors] == [
        ("S05", "pm10_level"),
        ("S06", "pm10"),
        ("S14", "ambient_brightness"),
    ]


def test_get_sensors_for_unknown_model() -> None:
    """Return no sensors for an unknown model."""
    models = ModelsInfo()

    assert models.get_sensors("unknown_model") == []
