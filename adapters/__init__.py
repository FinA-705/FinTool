"""
数据源适配器模块

提供统一的数据源接口，支持多种金融数据源：
- Tushare（A股专业数据）
- Yahoo Finance（全球市场数据）
- AKShare（多市场金融数据）
"""

from .base import BaseAdapter, DataRequest, DataResponse, Market, DataType
from .tushare_adapter import TushareAdapter
from .yfinance_adapter import YFinanceAdapter
from .factory import AdapterFactory, adapter_factory

__all__ = [
    "BaseAdapter",
    "DataRequest",
    "DataResponse",
    "Market",
    "DataType",
    "TushareAdapter",
    "YFinanceAdapter",
    "AdapterFactory",
    "adapter_factory",
]
