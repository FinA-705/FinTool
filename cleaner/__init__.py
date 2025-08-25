"""
数据清洗与标准化模块

提供统一的数据清洗、字段映射、单位转换和过滤功能
"""

from .cleaner import DataCleaner, CleaningConfig
from .field_mapper import FieldMapper, DataSource, StandardFields
from .unit_converter import UnitConverter, Unit
from .data_validator import DataValidator, MissingValueStrategy, OutlierDetectionMethod
from .market_filter import MarketFilter, Market

__all__ = [
    # 主要类
    "DataCleaner",
    "CleaningConfig",
    # 子模块类
    "FieldMapper",
    "UnitConverter",
    "DataValidator",
    "MarketFilter",
    # 枚举类
    "DataSource",
    "StandardFields",
    "Unit",
    "MissingValueStrategy",
    "OutlierDetectionMethod",
    "Market",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "FinancialAgent Team"
