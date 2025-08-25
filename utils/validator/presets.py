"""
预定义的验证函数
"""
import re
import pandas as pd
import numpy as np
from typing import Any, List, Optional, Union, Dict, Tuple
from datetime import datetime, date
from .models import ValidationError


def validate_stock_code(code: str) -> bool:
    """验证股票代码格式"""
    if not isinstance(code, str):
        return False
    a_stock_pattern = r"^(00|30|60|68)\d{4}(\.SH|\.SZ)$"
    hk_stock_pattern = r"^\d{5}\.HK$"
    us_stock_pattern = r"^[A-Z]{1,5}$"
    return any(re.match(p, code) for p in [a_stock_pattern, hk_stock_pattern, us_stock_pattern])


def validate_date_range(start_date: Union[str, datetime, date], end_date: Union[str, datetime, date]) -> bool:
    """验证日期范围"""
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        return start_dt <= end_dt
    except Exception:
        return False


def validate_numeric_data(
    value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None, allow_nan: bool = False
) -> bool:
    """验证数值数据"""
    try:
        if pd.isna(value):
            return allow_nan
        num_val = float(value)
        if np.isnan(num_val):
            return allow_nan
        if min_val is not None and num_val < min_val:
            return False
        if max_val is not None and num_val > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def validate_dataframe_schema(
    df: pd.DataFrame, required_columns: List[str], column_types: Optional[Dict[str, type]] = None
) -> Tuple[bool, List[str]]:
    """验证DataFrame结构"""
    errors = []
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"缺少必需列: {missing_columns}")

    if column_types:
        for col, expected_type in column_types.items():
            if col in df.columns:
                dtype = df[col].dtype
                if expected_type == str and dtype != "object":
                    errors.append(f"列 '{col}' 类型应为字符串")
                elif expected_type in [int, float] and not pd.api.types.is_numeric_dtype(dtype):
                    errors.append(f"列 '{col}' 类型应为数值")
                elif expected_type == datetime and not pd.api.types.is_datetime64_any_dtype(dtype):
                    errors.append(f"列 '{col}' 类型应为日期时间")
    return not errors, errors


def validate_financial_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证财务数据"""
    errors = []
    if "symbol" in data and not validate_stock_code(data["symbol"]):
        errors.append(f"无效的股票代码: {data['symbol']}")

    financial_metrics = [
        "pe_ratio", "pb_ratio", "roe", "debt_ratio", "revenue_growth",
        "profit_growth", "current_ratio", "gross_margin",
    ]
    for metric in financial_metrics:
        if metric in data:
            value = data[metric]
            if not validate_numeric_data(value, allow_nan=True):
                errors.append(f"无效的财务指标 {metric}: {value}")
                continue
            if metric in ["pe_ratio", "pb_ratio"] and value is not None and value <= 0:
                errors.append(f"{metric} 应大于0: {value}")
            elif metric == "debt_ratio" and value is not None and not (0 <= value <= 1):
                errors.append(f"负债率应在0-1之间: {value}")
            elif metric in ["roe", "gross_margin"] and value is not None and not (-100 <= value <= 100):
                errors.append(f"{metric} 应在-100%到100%之间: {value}")
    return not errors, errors
