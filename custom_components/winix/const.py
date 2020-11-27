"""Constants for the Winix component."""

DOMAIN = "winix"

WINIX_CONFIG_FILE = "winix.json"
WINIX_DATA_KEY = "fan_winix_air_purifier"

ATTR_AIRFLOW = "airflow"
ATTR_FILTER_REPLACEMENT_DATE = "filter_replace_date"
ATTR_LOCATION = "location"
ATTR_MODE = "mode"
ATTR_PLASMA = "plasma"
ATTR_POWER = "power"

ATTR_POWER_ON_VALUE = "on"

# The service name is the method name in WinixPurifier
SERVICE_AUTO = "auto"
SERVICE_MANUAL = "manual"
SERVICE_PLASMAWAVE_ON = "plasmawave_on"
SERVICE_PLASMAWAVE_OFF = "plasmawave_off"
SERVICE_DELETE_CONFIG = "delete_config"
SERVICE_REFRESH_CONFIG = "refresh_config"


SERVICES = [
    SERVICE_AUTO,
    SERVICE_MANUAL,
    SERVICE_PLASMAWAVE_ON,
    SERVICE_PLASMAWAVE_OFF,
]

SPEED_OFF = "off"
SPEED_LOW = "low"
SPEED_MEDIUM = "medium"
SPEED_HIGH = "high"
SPEED_TURBO = "turbo"
SPEED_SLEEP = "sleep"
SPEED_LIST = [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH, SPEED_TURBO, SPEED_SLEEP]
