import datetime as dt
import os

from pydantic import BaseModel, Field

from dtbase.models.utils.config import read_config

_config_file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data_config.ini"
)
_data_defaults = read_config(_config_file_path, "data")
_sensor_defaults = read_config(_config_file_path, "sensors")
_others_defaults = read_config(_config_file_path, "others")


class ConfigData(BaseModel):
    num_days_training: int = Field(
        default=_data_defaults["num_days_training"], validate_default=True
    )
    mins_from_the_hour: int = Field(
        default=_data_defaults["mins_from_the_hour"], validate_default=True
    )
    time_delta: dt.timedelta = Field(
        default=_data_defaults["time_delta"], validate_default=True
    )
    window: int = Field(default=_data_defaults["window"], validate_default=True)
    predict_from_datetime: dt.datetime = Field(
        default=dt.datetime.now(), validate_default=True
    )


class ConfigSensors(BaseModel):
    include_sensors: list[str] = Field(
        default=_sensor_defaults["include_sensors"], validate_default=True
    )
    include_measures: list[tuple[str, str]] = Field(
        default=_sensor_defaults["include_measures"], validate_default=True
    )


class ConfigOthers(BaseModel):
    days_interval: int = Field(
        default=_others_defaults["days_interval"], validate_default=True
    )
    weekly_seasonality: bool = Field(
        default=_others_defaults["weekly_seasonality"], validate_default=True
    )
    farm_cycle_start: dt.time = Field(
        default=_others_defaults["farm_cycle_start"], validate_default=True
    )
