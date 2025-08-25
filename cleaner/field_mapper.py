"""
字段映射和重命名模块

负责将不同数据源的字段名标准化为统一格式
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from enum import Enum


class DataSource(Enum):
    """数据源枚举"""

    TUSHARE = "tushare"
    YFINANCE = "yfinance"
    AKSHARE = "akshare"
    EASTMONEY = "eastmoney"


class StandardFields:
    """标准化字段名定义"""

    # 基本信息
    SYMBOL = "symbol"  # 股票代码
    NAME = "name"  # 股票名称
    MARKET = "market"  # 市场 (A/US/HK)
    INDUSTRY = "industry"  # 行业
    SECTOR = "sector"  # 板块

    # 价格数据
    CLOSE = "close"  # 收盘价
    OPEN = "open"  # 开盘价
    HIGH = "high"  # 最高价
    LOW = "low"  # 最低价
    VOLUME = "volume"  # 成交量
    TURNOVER = "turnover"  # 成交额

    # 财务指标
    PE_RATIO = "pe_ratio"  # 市盈率
    PB_RATIO = "pb_ratio"  # 市净率
    PS_RATIO = "ps_ratio"  # 市销率
    ROE = "roe"  # 净资产收益率
    ROA = "roa"  # 总资产收益率
    DEBT_RATIO = "debt_ratio"  # 负债率

    # 估值数据
    MARKET_CAP = "market_cap"  # 总市值
    CIRCULATING_CAP = "circulating_cap"  # 流通市值
    TOTAL_SHARES = "total_shares"  # 总股本
    FLOAT_SHARES = "float_shares"  # 流通股本

    # 技术指标
    MA5 = "ma5"  # 5日均线
    MA10 = "ma10"  # 10日均线
    MA20 = "ma20"  # 20日均线
    RSI = "rsi"  # RSI指标
    MACD = "macd"  # MACD指标


class FieldMapper:
    """字段映射器"""

    def __init__(self):
        self._field_maps = self._initialize_field_maps()
        self._reverse_maps = self._create_reverse_maps()

    def _initialize_field_maps(self) -> Dict[DataSource, Dict[str, str]]:
        """初始化字段映射表"""
        return {
            DataSource.TUSHARE: {
                # Tushare字段映射
                "ts_code": StandardFields.SYMBOL,
                "name": StandardFields.NAME,
                "close": StandardFields.CLOSE,
                "open": StandardFields.OPEN,
                "high": StandardFields.HIGH,
                "low": StandardFields.LOW,
                "vol": StandardFields.VOLUME,
                "amount": StandardFields.TURNOVER,
                "pe": StandardFields.PE_RATIO,
                "pb": StandardFields.PB_RATIO,
                "ps": StandardFields.PS_RATIO,
                "total_mv": StandardFields.MARKET_CAP,
                "circ_mv": StandardFields.CIRCULATING_CAP,
                "industry": StandardFields.INDUSTRY,
            },
            DataSource.YFINANCE: {
                # Yahoo Finance字段映射
                "Close": StandardFields.CLOSE,
                "Open": StandardFields.OPEN,
                "High": StandardFields.HIGH,
                "Low": StandardFields.LOW,
                "Volume": StandardFields.VOLUME,
                "trailingPE": StandardFields.PE_RATIO,
                "priceToBook": StandardFields.PB_RATIO,
                "marketCap": StandardFields.MARKET_CAP,
                "sector": StandardFields.SECTOR,
                "industry": StandardFields.INDUSTRY,
            },
            DataSource.AKSHARE: {
                # AKShare字段映射
                "代码": StandardFields.SYMBOL,
                "名称": StandardFields.NAME,
                "收盘价": StandardFields.CLOSE,
                "开盘价": StandardFields.OPEN,
                "最高价": StandardFields.HIGH,
                "最低价": StandardFields.LOW,
                "成交量": StandardFields.VOLUME,
                "成交额": StandardFields.TURNOVER,
                "市盈率": StandardFields.PE_RATIO,
                "市净率": StandardFields.PB_RATIO,
                "总市值": StandardFields.MARKET_CAP,
                "行业": StandardFields.INDUSTRY,
            },
        }

    def _create_reverse_maps(self) -> Dict[DataSource, Dict[str, str]]:
        """创建反向映射表（标准字段到源字段）"""
        reverse_maps = {}
        for source, field_map in self._field_maps.items():
            reverse_maps[source] = {v: k for k, v in field_map.items()}
        return reverse_maps

    def map_fields(self, data: pd.DataFrame, source: DataSource) -> pd.DataFrame:
        """
        将数据框字段名映射为标准字段名

        Args:
            data: 原始数据框
            source: 数据源类型

        Returns:
            映射后的数据框
        """
        if source not in self._field_maps:
            raise ValueError(f"不支持的数据源: {source}")

        field_map = self._field_maps[source]

        # 创建数据副本
        result = data.copy()

        # 执行字段映射
        columns_to_rename = {}
        for original_col in result.columns:
            if original_col in field_map:
                standard_col = field_map[original_col]
                columns_to_rename[original_col] = standard_col

        if columns_to_rename:
            result = result.rename(columns=columns_to_rename)

        return result

    def reverse_map_fields(
        self, data: pd.DataFrame, source: DataSource
    ) -> pd.DataFrame:
        """
        将标准字段名映射回源字段名

        Args:
            data: 标准化数据框
            source: 目标数据源类型

        Returns:
            反向映射后的数据框
        """
        if source not in self._reverse_maps:
            raise ValueError(f"不支持的数据源: {source}")

        reverse_map = self._reverse_maps[source]

        # 创建数据副本
        result = data.copy()

        # 执行反向映射
        columns_to_rename = {}
        for standard_col in result.columns:
            if standard_col in reverse_map:
                original_col = reverse_map[standard_col]
                columns_to_rename[standard_col] = original_col

        if columns_to_rename:
            result = result.rename(columns=columns_to_rename)

        return result

    def get_available_fields(self, source: DataSource) -> List[str]:
        """
        获取数据源支持的字段列表

        Args:
            source: 数据源类型

        Returns:
            字段名列表
        """
        if source not in self._field_maps:
            return []

        return list(self._field_maps[source].keys())

    def get_standard_fields(self) -> List[str]:
        """
        获取所有标准字段名列表

        Returns:
            标准字段名列表
        """
        all_standards = set()
        for field_map in self._field_maps.values():
            all_standards.update(field_map.values())
        return sorted(list(all_standards))

    def add_custom_mapping(
        self, source: DataSource, original_field: str, standard_field: str
    ):
        """
        添加自定义字段映射

        Args:
            source: 数据源类型
            original_field: 原始字段名
            standard_field: 标准字段名
        """
        if source not in self._field_maps:
            self._field_maps[source] = {}
            self._reverse_maps[source] = {}

        self._field_maps[source][original_field] = standard_field
        self._reverse_maps[source][standard_field] = original_field

    def remove_mapping(self, source: DataSource, original_field: str):
        """
        移除字段映射

        Args:
            source: 数据源类型
            original_field: 要移除的原始字段名
        """
        if source in self._field_maps and original_field in self._field_maps[source]:
            standard_field = self._field_maps[source][original_field]
            del self._field_maps[source][original_field]

            if (
                source in self._reverse_maps
                and standard_field in self._reverse_maps[source]
            ):
                del self._reverse_maps[source][standard_field]
