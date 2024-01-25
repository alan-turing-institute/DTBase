import os

from pydantic import BaseModel, Field

from dtbase.models.utils.config import read_config

_config_file_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "config_arima.ini"
)
_defaults = read_config(_config_file_path, "arima")


class ConfigArima(BaseModel):
    hours_forecast: int = Field(
        default=_defaults["hours_forecast"], validate_default=True
    )
    arima_order: tuple[int, int, int] = Field(
        default=_defaults["arima_order"], validate_default=True
    )
    seasonal_order: tuple[int, int, int, int] = Field(
        default=_defaults["seasonal_order"], validate_default=True
    )
    trend: str | list[int] | None = Field(
        default=_defaults["trend"], validate_default=True
    )
    alpha: float = Field(default=_defaults["alpha"], validate_default=True)
    perform_cv: bool = Field(default=_defaults["perform_cv"], validate_default=True)
    cv_refit: bool = Field(default=_defaults["cv_refit"], validate_default=True)
