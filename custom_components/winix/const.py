"""Constants for the Winix C545 Air Purifier component."""

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

ATTR_POWER_ON_VALUE = "on"

# The service name is the partial name of the method in WinixPurifier
SERVICE_PLASMAWAVE_ON = "plasmawave_on"
SERVICE_PLASMAWAVE_OFF = "plasmawave_off"
SERVICE_REFRESH_ACCESS = "refresh_access"


SERVICES = [
    SERVICE_PLASMAWAVE_ON,
    SERVICE_PLASMAWAVE_OFF,
]

SPEED_OFF = "off"
SPEED_AUTO = "auto"
SPEED_LOW = "low"
SPEED_MEDIUM = "medium"
SPEED_HIGH = "high"
SPEED_TURBO = "turbo"
SPEED_SLEEP = "sleep"
SPEED_LIST = [
    SPEED_OFF,
    SPEED_AUTO,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH,
    SPEED_TURBO,
    SPEED_SLEEP,
]
