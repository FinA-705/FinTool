"""
便捷的验证函数，用于快速检查和抛出异常
"""
from typing import Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
from .presets import validate_stock_code, validate_date_range, validate_numeric_data
from .models import ValidationError


def ensure_valid_stock_code(code: str) -> str:
    """确保股票代码有效，否则抛出异常"""
    if not validate_stock_code(code):
        raise ValidationError(f"无效的股票代码: {code}")
    return code


def ensure_valid_date_range(
    start_date: Union[str, datetime], end_date: Union[str, datetime]
) -> Tuple[datetime, datetime]:
    """确保日期范围有效，否则抛出异常"""
    if not validate_date_range(start_date, end_date):
        raise ValidationError(f"无效的日期范围: {start_date} 到 {end_date}")
    return pd.to_datetime(start_date), pd.to_datetime(end_date)


def ensure_numeric_range(
    value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None
) -> float:
    """确保数值在指定范围内，否则抛出异常"""
    if not validate_numeric_data(value, min_val, max_val):
        range_str = f"[{min_val}, {max_val}]"
        raise ValidationError(f"数值 {value} 不在有效范围 {range_str} 内")
    return float(value)
