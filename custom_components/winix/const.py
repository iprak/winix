"""Constants for the Winix C545 Air Purifier component."""

from enum import Enum, unique

DOMAIN = "winix"

WINIX_CONFIG_FILE = "winix.json"
WINIX_DATA_KEY = "fan_winix_air_purifier"

ATTR_AIRFLOW = "airflow"
ATTR_FILTER_REPLACEMENT_DATE = "filter_replace_date"
ATTR_LOCATION = "location"
ATTR_MODE = "mode"
ATTR_PLASMA = "plasma"
ATTR_POWER = "power"
ATTR_AIR_QUALITY = "air_quality"
ATTR_AIR_QVALUE = "air_qvalue"

OFF_VALUE = "off"
ON_VALUE = "on"

# The service name is the partial name of the method in WinixPurifier
SERVICE_PLASMAWAVE_ON = "plasmawave_on"
SERVICE_PLASMAWAVE_OFF = "plasmawave_off"
SERVICE_PLASMAWAVE_TOGGLE = "plasmawave_toggle"
SERVICE_REFRESH_ACCESS = "refresh_access"
SERVICES = [
    SERVICE_PLASMAWAVE_ON,
    SERVICE_PLASMAWAVE_OFF,
    SERVICE_PLASMAWAVE_TOGGLE,
]

# airflow can contain the special preset values of manual and sleep
# but we are not using those as fan speed.
AIRFLOW_LOW = "low"
AIRFLOW_MEDIUM = "medium"
AIRFLOW_HIGH = "high"
AIRFLOW_TURBO = "turbo"
AIRFLOW_SLEEP = "sleep"

ORDERED_NAMED_FAN_SPEEDS = [
    AIRFLOW_LOW,
    AIRFLOW_MEDIUM,
    AIRFLOW_HIGH,
    AIRFLOW_TURBO,
]

# mode can contain the special preset value of manual.
MODE_AUTO = "auto"
MODE_MANUAL = "manual"

PRESET_MODE_AUTO = "Auto"
PRESET_MODE_AUTO_PLASMA_OFF = "Auto (PlasmaWave off)"
PRESET_MODE_MANUAL = "Manual"
PRESET_MODE_MANUAL_PLASMA_OFF = "Manual (PlasmaWave off)"
PRESET_MODE_SLEEP = "Sleep"
PRESET_MODES = [
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
