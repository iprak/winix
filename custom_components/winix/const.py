"""Constants for the Winix C545 Air Purifier component."""

from enum import Enum, unique
from typing import Final

__min_ha_version__ = "2024.8"

WINIX_DOMAIN: Final = "winix"

WINIX_NAME: Final = "Winix Purifier"
WINIX_DATA_KEY: Final = "fan_winix_air_purifier"
WINIX_DATA_COORDINATOR: Final = "coordinator"
WINIX_AUTH_RESPONSE: Final = "WinixAuthResponse"
WINIX_ACCESS_TOKEN_EXPIRATION: Final = "access_token_expiration"

ATTR_AIRFLOW: Final = "airflow"
ATTR_AIR_AQI: Final = "aqi"
ATTR_AIR_QUALITY: Final = "air_quality"
ATTR_AIR_QVALUE: Final = "air_qvalue"
ATTR_FILTER_HOUR: Final = "filter_hour"
ATTR_FILTER_REPLACEMENT_DATE: Final = "filter_replace_date"
ATTR_LOCATION: Final = "location"
ATTR_MODE: Final = "mode"
ATTR_PLASMA: Final = "plasma"
ATTR_POWER: Final = "power"

SENSOR_AIR_QVALUE: Final = "air_qvalue"
SENSOR_AQI: Final = "aqi"
SENSOR_FILTER_LIFE: Final = "filter_life"

OFF_VALUE: Final = "off"
ON_VALUE: Final = "on"

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

# mode can contain the special preset value of manual.
MODE_AUTO: Final = "auto"
MODE_MANUAL: Final = "manual"

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
class NumericPresetModes(str, Enum):
    """Alternate numeric preset modes.

    The value correspond to the index in PRESET_MODES.
    """

    PRESET_MODE_AUTO = "1"
    PRESET_MODE_AUTO_PLASMA_OFF = "2"
    PRESET_MODE_MANUAL = "3"
    PRESET_MODE_MANUAL_PLASMA_OFF = "4"
    PRESET_MODE_SLEEP = "5"
