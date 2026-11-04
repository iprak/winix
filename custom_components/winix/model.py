"""Winix model metadata classes."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Final

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    UnitOfDensity,
    UnitOfPower,
)

from .const import (
    DEFAULT_FILTER_MAX_LIFE_HOURS,
    OVERRIDE_FILTER_MAX_LIFE_HOURS,
    SENSOR_PM25,
    SENSOR_POWER_CONSUMPTION,
)


@dataclass(slots=True)
class SensorInfo:
    """Sensor metadata."""

    attr_id: str
    key: str
    device_class: str | None
    native_unit_of_measurement: str | None = None


@dataclass(slots=True)
class EnumSensorInfo(SensorInfo):
    """Enum sensor metadata."""

    enum_values: dict[int, str] | None = None


@dataclass(slots=True)
class FilterInfo:
    """Replacement filter metadata."""

    filter_seq: int | None = None
    filter_name_en: str | None = None
    filter_max_life: int | None = None
    filter_shape: str | None = None
    filter_buy_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FilterInfo:
        """Create a FilterInfo object from raw API data."""
        return cls(
            filter_seq=data.get("filterSeq"),
            filter_name_en=data.get("filterNameEn"),
            filter_max_life=data.get("filterMaxLife"),
            filter_shape=data.get("filterShape"),
            filter_buy_url=data.get("filterBuyUrl"),
        )


@dataclass(slots=True)
class ModelInfo:
    """Detailed model metadata for a single product variant."""

    model_id: str | None = None
    model_name: str | None = None
    filter_info: int = DEFAULT_FILTER_MAX_LIFE_HOURS
    sensor_info_list: list[SensorInfo] = field(default_factory=list)


@dataclass(slots=True)
class SensorData:
    """Static sensor metadata for a device model."""

    key: str
    attr_id: str
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None


@dataclass(slots=True)
class EnumSensorData:
    """Static enum type sensor metadata for a device model."""

    key: str
    attr_id: str
    enum_values: str


_GOOD_FAIR_POOR_VERYPOOR = "01:Good/02:Fair/03:Poor/04:Very Poor"

# dust_level_10 level and values are 01, 02 or 03. Using level (S05) instead of value.
# This is used by T500_AU, ZEROS_EU, T500_EU, ZEROS_GB, T500_GB, ZEROS_ID, T500_ID, TOWER_Q, ZEROS_TW, T500_TW
# PRIMEKOR/MASTERKOR also uses the same attribute with 1-4 range. Using the 1-4 range


class ModelSensor(Enum):
    """Sensor definitions referenced by model profiles."""

    PM1_LEVEL_S01 = auto()
    PM1_S02 = auto()
    PM25_LEVEL_S03 = auto()
    PM25_S04 = auto()
    PM10_LEVEL_S05 = auto()
    PM10_S06 = auto()
    GAS_SENSOR_LEVEL_S07 = auto()
    GAS_SENSOR_S08 = auto()
    AMBIENT_BRIGHTNESS_S14 = auto()
    RPM_S15 = auto()
    CO2_S17 = auto()
    AIR_PURIFICATION_INDEX_S18 = auto()

    INDOOR_TEMPERATURE_S01 = auto()
    OUTDOOR_TEMPERATURE_S02 = auto()
    INDOOR_FAN_SPEED_S03 = auto()
    OUTDOOR_FAN_SPEED_S04 = auto()
    CURRENT_COMPRESSOR_SPEED_S05 = auto()
    POWER_CONSUMPTION_S06 = auto()


_MODEL_INFO_SENSOR_DATA: Final[dict[ModelSensor, EnumSensorData | SensorData]] = {
    # Some models expose Good/Fair/Poor (1,2,3).
    # This extended declaration will be backwards compatible with those cases.
    # We can potentially use SensorDeviceClass.PM1, PM10, PN25 and VOLATILE_ORGANIC_COMPOUNDS for GAS_SENSOR_S08.
    # SensorDeviceClass needs to be paired with the unit otheriwse HA generates warnings and I am unsure of the
    # actual value at this point. So not using SensorDeviceClass for now.
    ModelSensor.PM1_LEVEL_S01: EnumSensorData(
        "pm1_0_level", "S01", _GOOD_FAIR_POOR_VERYPOOR
    ),
    ModelSensor.PM1_S02: SensorData(
        "pm1_0",
        "S02",
        SensorDeviceClass.PM1,
        UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
    ),
    ModelSensor.PM25_LEVEL_S03: EnumSensorData(
        "pm2_5_level", "S03", _GOOD_FAIR_POOR_VERYPOOR
    ),
    ModelSensor.PM25_S04: SensorData(
        SENSOR_PM25,
        "S04",
        SensorDeviceClass.PM25,
        UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
    ),
    ModelSensor.PM10_LEVEL_S05: EnumSensorData(
        "pm10_level", "S05", _GOOD_FAIR_POOR_VERYPOOR
    ),
    ModelSensor.PM10_S06: SensorData(
        "pm10",
        "S06",
        SensorDeviceClass.PM10,
        UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
    ),
    # Enum declaration similar to PM1_LEVEL_S01
    ModelSensor.GAS_SENSOR_LEVEL_S07: EnumSensorData(
        "gas_sensor_level", "S07", _GOOD_FAIR_POOR_VERYPOOR
    ),
    ModelSensor.GAS_SENSOR_S08: SensorData("gas_sensor", "S08"),
    ModelSensor.AMBIENT_BRIGHTNESS_S14: SensorData("ambient_brightness", "S14"),
    ModelSensor.RPM_S15: SensorData("rpm", "S15"),
    # Currently there is no class for CO2 in SensorDeviceClass
    ModelSensor.CO2_S17: SensorData("co2", "S17"),
    ModelSensor.AIR_PURIFICATION_INDEX_S18: SensorData(
        "air_purification_index", "S18", None, PERCENTAGE
    ),
    # Not sure what temperature unit is being returned, not using SensorDeviceClass.TEMPERATURE for now
    ModelSensor.INDOOR_TEMPERATURE_S01: SensorData("indoor_temperature", "S01"),
    ModelSensor.OUTDOOR_TEMPERATURE_S02: SensorData("outdoor_temperature", "S02"),
    # Unit can be defined without device_class
    ModelSensor.INDOOR_FAN_SPEED_S03: SensorData(
        "indoor_fan_speed", "S03", None, REVOLUTIONS_PER_MINUTE
    ),
    ModelSensor.OUTDOOR_FAN_SPEED_S04: SensorData(
        "outdoor_fan_speed", "S04", None, REVOLUTIONS_PER_MINUTE
    ),
    ModelSensor.CURRENT_COMPRESSOR_SPEED_S05: SensorData(
        "current_compressor_speed", "S05"
    ),
    ModelSensor.POWER_CONSUMPTION_S06: SensorData(
        SENSOR_POWER_CONSUMPTION,
        "S06",
        # "00:--W/01:17W/02:20W/03:23W/04:26W/05:30W/06:34W/07:39W/08:56W/20:170W/21:178W/22:185W/23:193W/24:200W/25:208W/26:215W/27:223W/28:230W/29:239W/30:247W/31:256W/32:263W/33:273W/34:282W/35:235W/36:301W/37:310W/38:245W/39:329W/40:338W/41:346W/42:265W/43:364W/44:373W/45:275W/46:392W/47:402W/48:412W/49:425W/50:437W/51:449W/52:460W/53:472W/54:484W/55:496W/56:508W/57:520W/58:531W/59:544W/60:557W/61:569W/62:582W/63:595W/64:607W/65:618W/66:630W/67:648W/68:667W/69:686W/70:703W/71:719W/72:736W/73:757W/74:779W/75:801W/76:823W/77:844W/78:867W",
        SensorDeviceClass.POWER,
        UnitOfPower.WATT,
    ),
}


class ModelSensorProfile(Enum):
    """Sensor profiles referenced by model definitions."""

    T500_AU = (
        ModelSensor.PM10_LEVEL_S05,
        ModelSensor.PM10_S06,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )
    C610_AU = (
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )
    T800_AU = (
        ModelSensor.PM25_LEVEL_S03,
        ModelSensor.PM25_S04,
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )
    MODEL_5520_AU = (
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
        ModelSensor.RPM_S15,
    )
    C710_US = (
        ModelSensor.PM25_LEVEL_S03,
        ModelSensor.PM25_S04,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
        ModelSensor.AIR_PURIFICATION_INDEX_S18,
    )
    T800_US = (
        ModelSensor.PM25_LEVEL_S03,
        ModelSensor.PM25_S04,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )
    T1000_PPS = (
        ModelSensor.PM25_LEVEL_S03,
        ModelSensor.PM25_S04,
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
        ModelSensor.CO2_S17,
    )
    X24_KR = ()
    AC101 = (
        ModelSensor.INDOOR_TEMPERATURE_S01,
        ModelSensor.OUTDOOR_TEMPERATURE_S02,
        ModelSensor.INDOOR_FAN_SPEED_S03,
        ModelSensor.OUTDOOR_FAN_SPEED_S04,
        ModelSensor.CURRENT_COMPRESSOR_SPEED_S05,
        ModelSensor.POWER_CONSUMPTION_S06,
    )
    PRIMEKOR = (
        ModelSensor.PM1_LEVEL_S01,
        ModelSensor.PM1_S02,
        ModelSensor.PM25_LEVEL_S03,
        ModelSensor.PM25_S04,
        ModelSensor.PM10_LEVEL_S05,
        ModelSensor.PM10_S06,
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )
    AZPUEU = (
        ModelSensor.PM10_LEVEL_S05,
        ModelSensor.PM10_S06,
        ModelSensor.GAS_SENSOR_LEVEL_S07,
        ModelSensor.GAS_SENSOR_S08,
        ModelSensor.AMBIENT_BRIGHTNESS_S14,
    )


MODEL_INFO_DATA: tuple[tuple[str, str, ModelSensorProfile], ...] = (
    ("t500_au", "WXAP500", ModelSensorProfile.T500_AU),
    ("c610_au", "WXAP600", ModelSensorProfile.C610_AU),
    ("t800_au", "WXAP800", ModelSensorProfile.T800_AU),
    ("t1000_au", "T1000", ModelSensorProfile.T800_AU),
    ("5520_au", "5520", ModelSensorProfile.MODEL_5520_AU),
    ("c5_au", "C545", ModelSensorProfile.C610_AU),
    ("c710_us", "C710", ModelSensorProfile.C710_US),
    ("a400_us", "AT40", ModelSensorProfile.C610_AU),
    ("5530_us", "5530", ModelSensorProfile.MODEL_5520_AU),
    ("5520_us", "5520", ModelSensorProfile.MODEL_5520_AU),
    ("5510_us", "5510", ModelSensorProfile.MODEL_5520_AU),
    ("c610_us", "C610", ModelSensorProfile.C610_AU),
    ("c545", "C545", ModelSensorProfile.C610_AU),
    ("c909", "C909", ModelSensorProfile.C610_AU),
    ("t800_us", "T810/T830", ModelSensorProfile.T800_US),
    ("t500_us", "T500", ModelSensorProfile.C610_AU),
    ("9800", "9800", ModelSensorProfile.C610_AU),
    ("azsuus", "AM90", ModelSensorProfile.C610_AU),
    ("zeros_eu", "AZSU350-JWE", ModelSensorProfile.T500_AU),
    ("t500_eu", "T500", ModelSensorProfile.T500_AU),
    ("t800_eu", "T800", ModelSensorProfile.T800_US),
    ("zeros_gb", "AZSU350-JWB", ModelSensorProfile.T500_AU),
    ("t500_gb", "AT5U207-NWB", ModelSensorProfile.T500_AU),
    ("t800_gb", "AT8U457-NWB", ModelSensorProfile.T800_US),
    ("zeros_id", "AZSU357-NWN", ModelSensorProfile.T500_AU),
    ("t500_id", "AT5U207-NWI", ModelSensorProfile.T500_AU),
    ("t800_id", "ZERO 360", ModelSensorProfile.T800_AU),
    ("c5_id", "AC5U360-NWN", ModelSensorProfile.C610_AU),
    ("t800_jp", "T800_JP", ModelSensorProfile.T800_US),
    ("t500_jp", "AT5U207-NWJ", ModelSensorProfile.C610_AU),
    ("t1000_pps", "TOWER PRIME+ CAS(B)", ModelSensorProfile.T1000_PPS),
    ("t1000_kr", "TOWER PRIME+", ModelSensorProfile.T800_AU),
    ("primekor", "TOWER PRIME", ModelSensorProfile.PRIMEKOR),
    ("masterkor", "MASTER(S)", ModelSensorProfile.PRIMEKOR),
    ("xqlaser", "ATX****-IWK", ModelSensorProfile.T800_AU),
    ("xq20", "ATX****-JWK", ModelSensorProfile.T800_AU),
    ("xq", "ATX****-HWK/AGX***", ModelSensorProfile.T800_AU),
    ("tower_q", "TOWER Q", ModelSensorProfile.T500_AU),
    ("azpueu", "ZERO+", ModelSensorProfile.AZPUEU),
    ("titan", "TITAN", ModelSensorProfile.AZPUEU),
    ("x24_kr", "DXW*24*-***", ModelSensorProfile.X24_KR),
    ("x22_kr", "DXW*22*-***", ModelSensorProfile.X24_KR),
    ("x21_kr", "DXW*21*-***", ModelSensorProfile.X24_KR),
    ("x20_kr", "DXW*20*-***", ModelSensorProfile.X24_KR),
    ("jp19m", "DXJ*193-***", ModelSensorProfile.X24_KR),
    ("ac101", "EW**067-P*K", ModelSensorProfile.AC101),
    ("ac100", "EW**067-M*K", ModelSensorProfile.AC101),
    ("zeros_tw", "AZSU337-NWT", ModelSensorProfile.T500_AU),
    ("t500_tw", "威小淨", ModelSensorProfile.T500_AU),
    ("t800_tw", "T800", ModelSensorProfile.T800_AU),
    ("c5", "C5", ModelSensorProfile.C610_AU),
    ("x19ac", "DX18L", ModelSensorProfile.X24_KR),
    ("x17ac", "DX16L", ModelSensorProfile.X24_KR),
    ("towerxq_wa", "TOWER XQ", ModelSensorProfile.T800_AU),
    ("xqpro_wa", "XQ PRO", ModelSensorProfile.T800_AU),
    ("xlc", "XLC", ModelSensorProfile.C610_AU),
    ("hera", "HR1000", ModelSensorProfile.AZPUEU),
    ("nk105", "NK105", ModelSensorProfile.C610_AU),
    ("t1", "T1", ModelSensorProfile.AZPUEU),
)

_MODELS_FILTER_OVERRIDE: set[str] = {
    "azsuus",
    "xqlaser",
    "xq20",
    "xq",
    "tower_q",
    "azpueu",
    "titan",
    "x24_kr",
    "x22_kr",
    "x21_kr",
    "x20_kr",
    "jp19m",
    "ac101",
    "ac100",
    "x19ac",
    "x17ac",
    "towerxq_wa",
    "xqpro_wa",
    "xlc",
    "hera",
    "nk105",
    "t1",
}


class ModelsInfo:
    """List of Winix model info returned by the API."""

    _models: dict[str, ModelInfo] | None = None

    def __init__(self) -> None:
        """Initialize the model info list."""
        super().__init__()

        self._models = {}

        for (
            model_id,
            model_name,
            sensor_profile,
        ) in MODEL_INFO_DATA:
            sensor_info_list: list[SensorInfo] = []
            for sensor in sensor_profile.value:
                sensor_data = _MODEL_INFO_SENSOR_DATA[sensor]
                if not sensor_data:
                    continue

                enum_values: dict[int, str] = {}

                if isinstance(sensor_data, EnumSensorData) and sensor_data.enum_values:
                    for value in sensor_data.enum_values.split("/"):
                        if ":" in value:
                            enum_value, enum_name = value.split(":", 1)
                            enum_values[int(enum_value)] = enum_name

                if enum_values:
                    sensor_info_list.append(
                        # Enum type sensor can't have DeviceClass or units
                        EnumSensorInfo(
                            sensor_data.attr_id,
                            sensor_data.key,
                            None,
                            None,
                            enum_values,
                        )
                    )
                else:
                    sensor_info_list.append(
                        SensorInfo(
                            sensor_data.attr_id,
                            sensor_data.key,
                            sensor_data.device_class,
                            sensor_data.native_unit_of_measurement,
                        )
                    )

            self._models[model_id] = ModelInfo(
                model_id=model_id,
                model_name=model_name,
                filter_info=(
                    OVERRIDE_FILTER_MAX_LIFE_HOURS
                    if model_id in _MODELS_FILTER_OVERRIDE
                    else DEFAULT_FILTER_MAX_LIFE_HOURS
                ),
                sensor_info_list=sensor_info_list,
            )

    def get_filter_max_life(self, model_id) -> int:
        """Get the filter max life for the specified model."""

        model = self._models.get(model_id.casefold())
        return model.filter_info if model else DEFAULT_FILTER_MAX_LIFE_HOURS

    def get_sensors(self, model_id) -> list[SensorInfo]:
        """Get sensors for the specified model."""

        model = self._models.get(model_id.casefold())
        return model.sensor_info_list if model else []
