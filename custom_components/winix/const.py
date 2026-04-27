"""Constants for the Winix C545 Air Purifier component."""

from enum import StrEnum, unique
import logging
from typing import Final

__min_ha_version__ = "2024.8"

LOGGER = logging.getLogger(__package__)

WINIX_DOMAIN: Final = "winix"

WINIX_NAME: Final = "Winix Purifier"
WINIX_AUTH_RESPONSE: Final = "WinixAuthResponse"
ATTR_AIRFLOW: Final = "airflow"
ATTR_AIR_AQI: Final = "aqi"
ATTR_AIR_QUALITY: Final = "air_quality"
ATTR_AIR_QVALUE: Final = "air_qvalue"
ATTR_PM25: Final = "pm2_5"
ATTR_FILTER_HOUR: Final = "filter_hour"
ATTR_FILTER_REPLACEMENT_DATE: Final = "filter_replace_date"
ATTR_FILTER_REPLACEMENT_CYCLE: Final = "filter_replacement_cycle"
ATTR_LOCATION: Final = "location"
ATTR_MODE: Final = "mode"
ATTR_PLASMA: Final = "plasma"
ATTR_POWER: Final = "power"
ATTR_LAST_BRIGHTNESS_LEVEL: Final = "last_brightness_level"
ATTR_BRIGHTNESS_LEVEL: Final = "brightness_level"
ATTR_CHILD_LOCK: Final = "child_lock"
ATTR_AMBIENT_LIGHT: Final = "ambient_light"
ATTR_TARGET_HUMIDITY: Final = "target_humidity"
ATTR_CURRENT_HUMIDITY: Final = "current_humidity"
ATTR_WATER_TANK: Final = "water_tank"
ATTR_UV_SANITIZE: Final = "uv_sanitize"
ATTR_TIMER: Final = "timer"

SENSOR_AIR_QVALUE: Final = "air_qvalue"
SENSOR_PM25: Final = "pm2_5"
SENSOR_AQI: Final = "aqi"
SENSOR_FILTER_LIFE: Final = "filter_life"

OFF_VALUE: Final = "off"
ON_VALUE: Final = "on"
AUTO_DRY_VALUE: Final = "auto-dry"

AIR_QUALITY_GOOD: Final = "good"
AIR_QUALITY_FAIR: Final = "fair"
AIR_QUALITY_POOR: Final = "poor"

# The service name is the partial name of the method in WinixPurifier
SERVICE_PLASMAWAVE_ON: Final = "plasmawave_on"
SERVICE_PLASMAWAVE_OFF: Final = "plasmawave_off"
SERVICE_PLASMAWAVE_TOGGLE: Final = "plasmawave_toggle"
SERVICE_REMOVE_STALE_ENTITIES: Final = "remove_stale_entities"
FAN_SERVICES: Final = [
    SERVICE_PLASMAWAVE_ON,
    SERVICE_PLASMAWAVE_OFF,
    SERVICE_PLASMAWAVE_TOGGLE,
]

# airflow can contain the special preset values of manual and sleep
# but we are not using those as fan speed.
AIRFLOW_LOW: Final = "low"
AIRFLOW_MEDIUM: Final = "medium"
AIRFLOW_HIGH: Final = "high"
AIRFLOW_TURBO: Final = "turbo"
AIRFLOW_SLEEP: Final = "sleep"

ORDERED_NAMED_FAN_SPEEDS: Final = [
    AIRFLOW_LOW,
    AIRFLOW_MEDIUM,
    AIRFLOW_HIGH,
    AIRFLOW_TURBO,
]

DEFAULT_FILTER_ALARM_DURATION: Final = 9  # 9 months
DEFAULT_FILTER_ALARM_DURATION_HOURS: Final = DEFAULT_FILTER_ALARM_DURATION * 24 * 30
DEFAULT_POST_TIMEOUT: Final = 5

# mode can contain the special preset value of manual.
MODE_AUTO: Final = "auto"
MODE_MANUAL: Final = "manual"
MODE_CLOTHES: Final = "clothes"
MODE_SHOES: Final = "shoes"
MODE_QUIET: Final = "quiet"
MODE_CONTINUOUS: Final = "continuous"

PRESET_MODE_AUTO: Final = "Auto"
PRESET_MODE_AUTO_PLASMA_OFF: Final = "Auto (PlasmaWave off)"
PRESET_MODE_MANUAL: Final = "Manual"
PRESET_MODE_MANUAL_PLASMA_OFF: Final = "Manual (PlasmaWave off)"
PRESET_MODE_SLEEP: Final = "Sleep"
PRESET_MODES: Final = [
    PRESET_MODE_AUTO,
    PRESET_MODE_AUTO_PLASMA_OFF,
    PRESET_MODE_MANUAL,
    PRESET_MODE_MANUAL_PLASMA_OFF,
    PRESET_MODE_SLEEP,
]


@unique
class NumericPresetModes(StrEnum):
    """Alternate numeric preset modes.

    The value correspond to the index in PRESET_MODES.
    """

    PRESET_MODE_AUTO = "1"
    PRESET_MODE_AUTO_PLASMA_OFF = "2"
    PRESET_MODE_MANUAL = "3"
    PRESET_MODE_MANUAL_PLASMA_OFF = "4"
    PRESET_MODE_SLEEP = "5"


class Features:
    """Additional Winix device features."""

    supports_brightness_level = False
    supports_child_lock = False
    supports_pm25 = False
    supports_uv_sanitize = False
