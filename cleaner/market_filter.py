"""
市场和板块过滤模块

负责按市场、行业、板块等条件过滤股票数据
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd
from enum import Enum
from .field_mapper import StandardFields


class Market(Enum):
    """市场类型"""

    A_SHARE = "A"  # A股市场
    US_STOCK = "US"  # 美股市场
    HK_STOCK = "HK"  # 港股市场
    ALL = "ALL"  # 所有市场


class MarketFilter:
    """市场和板块过滤器"""

    def __init__(self):
        self._market_patterns = self._initialize_market_patterns()
        self._industry_groups = self._initialize_industry_groups()
        self._sector_groups = self._initialize_sector_groups()

    def _initialize_market_patterns(self) -> Dict[Market, Dict[str, Any]]:
        """初始化市场识别模式"""
        return {
            Market.A_SHARE: {
                "symbol_patterns": [
                    r"^\d{6}$",  # 6位数字 (如 000001)
                    r"^\d{6}\.(SH|SZ)$",  # 带交易所后缀 (如 000001.SZ)
                ],
                "exchange_codes": ["SH", "SZ"],
                "currency": "CNY",
            },
            Market.US_STOCK: {
                "symbol_patterns": [
                    r"^[A-Z]{1,5}$",  # 1-5位大写字母 (如 AAPL)
                    r"^[A-Z]+\.[A-Z]+$",  # 带点分隔 (如 BRK.A)
                ],
                "exchange_codes": ["NASDAQ", "NYSE", "AMEX"],
                "currency": "USD",
            },
            Market.HK_STOCK: {
                "symbol_patterns": [
                    r"^\d{4,5}$",  # 4-5位数字 (如 0700)
                    r"^\d{4,5}\.HK$",  # 带HK后缀 (如 0700.HK)
                ],
                "exchange_codes": ["HKEX"],
                "currency": "HKD",
            },
        }

    def _initialize_industry_groups(self) -> Dict[str, List[str]]:
        """初始化行业分组"""
        return {
            "科技": [
                "计算机应用",
                "计算机设备",
                "电子制造",
                "通信设备",
                "软件开发",
                "互联网服务",
                "半导体",
                "人工智能",
            ],
            "金融": [
                "银行",
                "保险",
                "证券",
                "信托",
                "租赁服务",
                "多元金融",
                "期货",
                "基金",
            ],
            "医药": [
                "化学制药",
                "生物制药",
                "医疗器械",
                "医疗服务",
                "中药",
                "医药商业",
                "疫苗",
                "医美",
            ],
            "消费": [
                "食品饮料",
                "纺织服装",
                "家用电器",
                "汽车",
                "零售",
                "旅游",
                "餐饮",
                "化妆品",
                "家具",
            ],
            "工业": [
                "机械设备",
                "电力设备",
                "建筑材料",
                "钢铁",
                "有色金属",
                "化工",
                "建筑装饰",
                "电气设备",
            ],
            "能源": ["石油石化", "煤炭", "电力", "燃气", "新能源", "环保", "公用事业"],
            "地产": ["房地产开发", "物业管理", "园区开发", "装修装饰"],
            "农业": ["种植业", "林业", "牧业", "渔业", "农产品加工"],
            "传媒": ["广告营销", "出版", "影视", "游戏", "教育", "体育"],
            "交通": ["航空运输", "铁路运输", "公路运输", "水路运输", "物流"],
        }

    def _initialize_sector_groups(self) -> Dict[str, List[str]]:
        """初始化板块分组"""
        return {
            "主板": ["主板A股", "主板B股"],
            "中小板": ["中小企业板"],
            "创业板": ["创业板"],
            "科创板": ["科创板"],
            "北交所": ["北京证券交易所"],
            "新三板": ["新三板精选层", "新三板创新层", "新三板基础层"],
            "港股主板": ["港股主板"],
            "港股创业板": ["港股创业板"],
            "美股主板": ["NYSE", "NASDAQ"],
            "美股OTC": ["OTC"],
        }

    def identify_market(self, symbol: str) -> Market:
        """
        识别股票代码对应的市场

        Args:
            symbol: 股票代码

        Returns:
            市场类型
        """
        import re

        for market, patterns in self._market_patterns.items():
            for pattern in patterns["symbol_patterns"]:
                if re.match(pattern, symbol.upper()):
                    return market

        return Market.A_SHARE  # 默认返回A股

    def filter_by_market(
        self, data: pd.DataFrame, markets: Union[Market, List[Market]]
    ) -> pd.DataFrame:
        """
        按市场过滤数据

        Args:
            data: 要过滤的数据框
            markets: 市场类型或市场类型列表

        Returns:
            过滤后的数据框
        """
        if StandardFields.SYMBOL not in data.columns:
            return data.copy()

        if isinstance(markets, Market):
            markets = [markets]

        if Market.ALL in markets:
            return data.copy()

        result = pd.DataFrame()

        for market in markets:
            market_data = data[
                data[StandardFields.SYMBOL].apply(
                    lambda x: self.identify_market(str(x)) == market
                )
            ]
            result = pd.concat([result, market_data], ignore_index=True)

        return result

    def filter_by_industry(
        self,
        data: pd.DataFrame,
        industries: Union[str, List[str]],
        exact_match: bool = False,
    ) -> pd.DataFrame:
        """
        按行业过滤数据

        Args:
            data: 要过滤的数据框
            industries: 行业名称或行业名称列表
            exact_match: 是否精确匹配

        Returns:
            过滤后的数据框
        """
        if StandardFields.INDUSTRY not in data.columns:
            return data.copy()

        if isinstance(industries, str):
            industries = [industries]

        if exact_match:
            # 精确匹配
            mask = data[StandardFields.INDUSTRY].isin(industries)
        else:
            # 模糊匹配
            mask = pd.Series([False] * len(data))
            for industry in industries:
                mask |= data[StandardFields.INDUSTRY].str.contains(
                    industry, case=False, na=False
                )

        return data[mask].copy()

    def filter_by_industry_group(
        self, data: pd.DataFrame, groups: Union[str, List[str]]
    ) -> pd.DataFrame:
        """
        按行业分组过滤数据

        Args:
            data: 要过滤的数据框
            groups: 行业分组名称或分组名称列表

        Returns:
            过滤后的数据框
        """
        if isinstance(groups, str):
            groups = [groups]

        target_industries = []
        for group in groups:
            if group in self._industry_groups:
                target_industries.extend(self._industry_groups[group])

        if not target_industries:
            return pd.DataFrame()

        return self.filter_by_industry(data, target_industries, exact_match=False)

    def filter_by_sector(
        self,
        data: pd.DataFrame,
        sectors: Union[str, List[str]],
        exact_match: bool = False,
    ) -> pd.DataFrame:
        """
        按板块过滤数据

        Args:
            data: 要过滤的数据框
            sectors: 板块名称或板块名称列表
            exact_match: 是否精确匹配

        Returns:
            过滤后的数据框
        """
        if StandardFields.SECTOR not in data.columns:
            return data.copy()

        if isinstance(sectors, str):
            sectors = [sectors]

        if exact_match:
            # 精确匹配
            mask = data[StandardFields.SECTOR].isin(sectors)
        else:
            # 模糊匹配
            mask = pd.Series([False] * len(data))
            for sector in sectors:
                mask |= data[StandardFields.SECTOR].str.contains(
                    sector, case=False, na=False
                )

        return data[mask].copy()

    def filter_by_market_cap(
        self,
        data: pd.DataFrame,
        min_cap: Optional[float] = None,
        max_cap: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        按市值过滤数据

        Args:
            data: 要过滤的数据框
            min_cap: 最小市值
            max_cap: 最大市值

        Returns:
            过滤后的数据框
        """
        if StandardFields.MARKET_CAP not in data.columns:
            return data.copy()

        result = data.copy()

        # 转换为数值类型
        market_cap = pd.to_numeric(result[StandardFields.MARKET_CAP], errors="coerce")

        # 应用过滤条件
        if min_cap is not None:
            result = result[market_cap >= min_cap]
            market_cap = market_cap[market_cap >= min_cap]

        if max_cap is not None:
            result = result[market_cap <= max_cap]

        return result

    def filter_by_pe_ratio(
        self,
        data: pd.DataFrame,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        按市盈率过滤数据

        Args:
            data: 要过滤的数据框
            min_pe: 最小市盈率
            max_pe: 最大市盈率

        Returns:
            过滤后的数据框
        """
        if StandardFields.PE_RATIO not in data.columns:
            return data.copy()

        result = data.copy()

        # 转换为数值类型
        pe_ratio = pd.to_numeric(result[StandardFields.PE_RATIO], errors="coerce")

        # 应用过滤条件
        if min_pe is not None:
            result = result[pe_ratio >= min_pe]
            pe_ratio = pe_ratio[pe_ratio >= min_pe]

        if max_pe is not None:
            result = result[pe_ratio <= max_pe]

        return result

    def apply_multiple_filters(
        self, data: pd.DataFrame, filters: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        应用多个过滤条件

        Args:
            data: 要过滤的数据框
            filters: 过滤条件字典

        Returns:
            过滤后的数据框
        """
        result = data.copy()

        # 市场过滤
        if "markets" in filters:
            result = self.filter_by_market(result, filters["markets"])

        # 行业过滤
        if "industries" in filters:
            exact_match = filters.get("industry_exact_match", False)
            result = self.filter_by_industry(result, filters["industries"], exact_match)

        # 行业分组过滤
        if "industry_groups" in filters:
            result = self.filter_by_industry_group(result, filters["industry_groups"])

        # 板块过滤
        if "sectors" in filters:
            exact_match = filters.get("sector_exact_match", False)
            result = self.filter_by_sector(result, filters["sectors"], exact_match)

        # 市值过滤
        if "min_market_cap" in filters or "max_market_cap" in filters:
            result = self.filter_by_market_cap(
                result, filters.get("min_market_cap"), filters.get("max_market_cap")
            )

        # 市盈率过滤
        if "min_pe_ratio" in filters or "max_pe_ratio" in filters:
            result = self.filter_by_pe_ratio(
                result, filters.get("min_pe_ratio"), filters.get("max_pe_ratio")
            )

        return result

    def get_market_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        获取市场分布摘要

        Args:
            data: 数据框

        Returns:
            市场分布统计
        """
        if StandardFields.SYMBOL not in data.columns:
            return {}

        summary = {
            "total_count": len(data),
            "market_distribution": {},
            "industry_distribution": {},
            "sector_distribution": {},
        }

        # 市场分布
        market_counts = {}
        for market in Market:
            if market != Market.ALL:
                count = len(self.filter_by_market(data, market))
                if count > 0:
                    market_counts[market.value] = count
        summary["market_distribution"] = market_counts

        # 行业分布
        if StandardFields.INDUSTRY in data.columns:
            industry_counts = (
                data[StandardFields.INDUSTRY].value_counts().head(10).to_dict()
            )
            summary["industry_distribution"] = industry_counts

        # 板块分布
        if StandardFields.SECTOR in data.columns:
            sector_counts = (
                data[StandardFields.SECTOR].value_counts().head(10).to_dict()
            )
            summary["sector_distribution"] = sector_counts

        return summary

    def add_industry_group(self, group_name: str, industries: List[str]):
        """
        添加行业分组

        Args:
            group_name: 分组名称
            industries: 行业列表
        """
        self._industry_groups[group_name] = industries

    def add_sector_group(self, group_name: str, sectors: List[str]):
        """
        添加板块分组

        Args:
            group_name: 分组名称
            sectors: 板块列表
        """
        self._sector_groups[group_name] = sectors

    def get_available_groups(self) -> Dict[str, List[str]]:
        """
        获取可用的分组

        Returns:
            分组字典
        """
        return {
            "industry_groups": list(self._industry_groups.keys()),
            "sector_groups": list(self._sector_groups.keys()),
        }
