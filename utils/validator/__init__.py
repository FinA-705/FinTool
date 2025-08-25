"""
数据验证模块
"""
from .models import ValidationError, ValidationType, ValidationRule
from .core import DataValidator
from .presets import (
    validate_stock_code,
    validate_date_range,
    validate_numeric_data,
    validate_dataframe_schema,
    validate_financial_data,
)
from .helpers import (
    ensure_valid_stock_code,
    ensure_valid_date_range,
    ensure_numeric_range,
)

__all__ = [
    "ValidationError",
    "ValidationType",
    "ValidationRule",
    "DataValidator",
    "validate_stock_code",
    "validate_date_range",
    "validate_numeric_data",
    "validate_dataframe_schema",
    "validate_financial_data",
    "ensure_valid_stock_code",
    "ensure_valid_date_range",
    "ensure_numeric_range",
]
