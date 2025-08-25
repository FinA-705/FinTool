"""
单位转换模块

负责将不同数据源的数值单位标准化
"""

from typing import Dict, List, Optional, Any, Callable
import pandas as pd
import numpy as np
from enum import Enum
from .field_mapper import StandardFields


class Unit(Enum):
    """单位枚举"""

    # 货币单位
    YUAN = "yuan"  # 元
    WAN_YUAN = "wan_yuan"  # 万元
    YI_YUAN = "yi_yuan"  # 亿元
    USD = "usd"  # 美元
    HKD = "hkd"  # 港币

    # 股数单位
    SHARES = "shares"  # 股
    WAN_SHARES = "wan_shares"  # 万股
    YI_SHARES = "yi_shares"  # 亿股

    # 比率单位
    PERCENTAGE = "percentage"  # 百分比 (0-100)
    DECIMAL = "decimal"  # 小数 (0-1)

    # 其他
    COUNT = "count"  # 计数
    MULTIPLIER = "multiplier"  # 倍数


class UnitConverter:
    """单位转换器"""

    def __init__(self):
        self._conversion_rules = self._initialize_conversion_rules()
        self._field_units = self._initialize_field_units()

    def _initialize_conversion_rules(self) -> Dict[tuple, Callable]:
        """初始化单位转换规则"""
        return {
            # 货币转换
            (Unit.WAN_YUAN, Unit.YUAN): lambda x: x * 10000,
            (Unit.YI_YUAN, Unit.YUAN): lambda x: x * 100000000,
            (Unit.YI_YUAN, Unit.WAN_YUAN): lambda x: x * 10000,
            (Unit.YUAN, Unit.WAN_YUAN): lambda x: x / 10000,
            (Unit.YUAN, Unit.YI_YUAN): lambda x: x / 100000000,
            (Unit.WAN_YUAN, Unit.YI_YUAN): lambda x: x / 10000,
            # 股数转换
            (Unit.WAN_SHARES, Unit.SHARES): lambda x: x * 10000,
            (Unit.YI_SHARES, Unit.SHARES): lambda x: x * 100000000,
            (Unit.YI_SHARES, Unit.WAN_SHARES): lambda x: x * 10000,
            (Unit.SHARES, Unit.WAN_SHARES): lambda x: x / 10000,
            (Unit.SHARES, Unit.YI_SHARES): lambda x: x / 100000000,
            (Unit.WAN_SHARES, Unit.YI_SHARES): lambda x: x / 10000,
            # 比率转换
            (Unit.PERCENTAGE, Unit.DECIMAL): lambda x: x / 100,
            (Unit.DECIMAL, Unit.PERCENTAGE): lambda x: x * 100,
        }

    def _initialize_field_units(self) -> Dict[str, Dict[str, Unit]]:
        """初始化字段单位映射"""
        return {
            "tushare": {
                StandardFields.MARKET_CAP: Unit.WAN_YUAN,
                StandardFields.CIRCULATING_CAP: Unit.WAN_YUAN,
                StandardFields.TURNOVER: Unit.WAN_YUAN,
                StandardFields.TOTAL_SHARES: Unit.WAN_SHARES,
                StandardFields.FLOAT_SHARES: Unit.WAN_SHARES,
                StandardFields.VOLUME: Unit.SHARES,
                StandardFields.PE_RATIO: Unit.MULTIPLIER,
                StandardFields.PB_RATIO: Unit.MULTIPLIER,
                StandardFields.PS_RATIO: Unit.MULTIPLIER,
                StandardFields.ROE: Unit.PERCENTAGE,
                StandardFields.ROA: Unit.PERCENTAGE,
                StandardFields.DEBT_RATIO: Unit.PERCENTAGE,
            },
            "yfinance": {
                StandardFields.MARKET_CAP: Unit.USD,
                StandardFields.VOLUME: Unit.SHARES,
                StandardFields.PE_RATIO: Unit.MULTIPLIER,
                StandardFields.PB_RATIO: Unit.MULTIPLIER,
                StandardFields.PS_RATIO: Unit.MULTIPLIER,
            },
            "akshare": {
                StandardFields.MARKET_CAP: Unit.YI_YUAN,
                StandardFields.TURNOVER: Unit.WAN_YUAN,
                StandardFields.VOLUME: Unit.SHARES,
                StandardFields.PE_RATIO: Unit.MULTIPLIER,
                StandardFields.PB_RATIO: Unit.MULTIPLIER,
            },
        }

    def convert_value(self, value: Any, from_unit: Unit, to_unit: Unit) -> Any:
        """
        转换单个数值

        Args:
            value: 要转换的值
            from_unit: 源单位
            to_unit: 目标单位

        Returns:
            转换后的值
        """
        if pd.isna(value) or from_unit == to_unit:
            return value

        conversion_key = (from_unit, to_unit)
        if conversion_key not in self._conversion_rules:
            raise ValueError(f"不支持的单位转换: {from_unit} -> {to_unit}")

        converter = self._conversion_rules[conversion_key]

        try:
            return converter(float(value))
        except (ValueError, TypeError):
            return value

    def convert_column(
        self, data: pd.Series, from_unit: Unit, to_unit: Unit
    ) -> pd.Series:
        """
        转换整列数据

        Args:
            data: 要转换的数据列
            from_unit: 源单位
            to_unit: 目标单位

        Returns:
            转换后的数据列
        """
        if from_unit == to_unit:
            return data.copy()

        conversion_key = (from_unit, to_unit)
        if conversion_key not in self._conversion_rules:
            raise ValueError(f"不支持的单位转换: {from_unit} -> {to_unit}")

        converter = self._conversion_rules[conversion_key]
        result = data.copy()

        # 只转换数值类型的数据
        numeric_mask = pd.to_numeric(result, errors="coerce").notna()
        if numeric_mask.any():
            numeric_data = pd.to_numeric(result[numeric_mask], errors="coerce")
            result.loc[numeric_mask] = numeric_data.apply(converter)

        return result

    def standardize_units(
        self,
        data: pd.DataFrame,
        source: str,
        target_units: Optional[Dict[str, Unit]] = None,
    ) -> pd.DataFrame:
        """
        标准化数据框的单位

        Args:
            data: 要转换的数据框
            source: 数据源名称
            target_units: 目标单位映射，如果为None则使用默认标准单位

        Returns:
            单位标准化后的数据框
        """
        if source not in self._field_units:
            return data.copy()

        if target_units is None:
            target_units = self._get_default_target_units()

        result = data.copy()
        source_units = self._field_units[source]

        for field, source_unit in source_units.items():
            if field in result.columns and field in target_units:
                target_unit = target_units[field]
                try:
                    result[field] = self.convert_column(
                        result[field], source_unit, target_unit
                    )
                except ValueError as e:
                    print(f"警告: 字段 {field} 单位转换失败: {e}")
                    continue

        return result

    def _get_default_target_units(self) -> Dict[str, Unit]:
        """获取默认的目标单位"""
        return {
            # 货币统一为万元
            StandardFields.MARKET_CAP: Unit.WAN_YUAN,
            StandardFields.CIRCULATING_CAP: Unit.WAN_YUAN,
            StandardFields.TURNOVER: Unit.WAN_YUAN,
            # 股数统一为万股
            StandardFields.TOTAL_SHARES: Unit.WAN_SHARES,
            StandardFields.FLOAT_SHARES: Unit.WAN_SHARES,
            StandardFields.VOLUME: Unit.WAN_SHARES,
            # 比率统一为倍数或小数
            StandardFields.PE_RATIO: Unit.MULTIPLIER,
            StandardFields.PB_RATIO: Unit.MULTIPLIER,
            StandardFields.PS_RATIO: Unit.MULTIPLIER,
            StandardFields.ROE: Unit.DECIMAL,
            StandardFields.ROA: Unit.DECIMAL,
            StandardFields.DEBT_RATIO: Unit.DECIMAL,
        }

    def get_field_unit(self, field: str, source: str) -> Optional[Unit]:
        """
        获取字段的单位

        Args:
            field: 字段名
            source: 数据源名称

        Returns:
            字段单位，如果未找到返回None
        """
        if source in self._field_units:
            return self._field_units[source].get(field)
        return None

    def add_unit_mapping(self, source: str, field: str, unit: Unit):
        """
        添加字段单位映射

        Args:
            source: 数据源名称
            field: 字段名
            unit: 单位
        """
        if source not in self._field_units:
            self._field_units[source] = {}

        self._field_units[source][field] = unit

    def add_conversion_rule(self, from_unit: Unit, to_unit: Unit, converter: Callable):
        """
        添加单位转换规则

        Args:
            from_unit: 源单位
            to_unit: 目标单位
            converter: 转换函数
        """
        self._conversion_rules[(from_unit, to_unit)] = converter

    def get_available_conversions(self, from_unit: Unit) -> List[Unit]:
        """
        获取从指定单位可以转换到的所有单位

        Args:
            from_unit: 源单位

        Returns:
            可转换的目标单位列表
        """
        available = []
        for source, target in self._conversion_rules.keys():
            if source == from_unit:
                available.append(target)
        return available
