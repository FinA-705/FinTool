"""
Walter Schloss 价值投资策略

基于Walter Schloss的投资理念实现的选股策略，专注于：
1. 低估值股票（低P/E、低P/B）
2. 财务安全性（低负债、充足现金）
3. 长期稳定性（避免高风险行业）
4. 简单易懂的业务模式

参考资料：
- Walter Schloss的16条投资原则
- Benjamin Graham的《证券分析》
- Warren Buffett对Schloss的评价
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

from .base_strategy import BaseStrategy, StrategyConfig, StrategyType
from .config_manager import ConfigManager


class SchlossStrategy(BaseStrategy):
    """Walter Schloss 价值投资策略"""

    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        初始化Schloss策略

        Args:
            config: 策略配置，如果为None则从配置管理器加载
        """
        if config is None:
            config_manager = ConfigManager()
            config = config_manager.load_strategy_config("schloss")

        super().__init__(config)
        self.config_manager = ConfigManager()

        # 加载评分区间配置
        self.pe_ranges = self.config_manager.get_scoring_ranges("pe_ratio")
        self.pb_ranges = self.config_manager.get_scoring_ranges("pb_ratio")
        self.roe_ranges = self.config_manager.get_scoring_ranges("roe")
        self.debt_ranges = self.config_manager.get_scoring_ranges("debt_to_equity")

    def get_strategy_type(self) -> StrategyType:
        """获取策略类型"""
        return StrategyType.VALUE

    def get_default_config(self) -> StrategyConfig:
        """获取默认配置"""
        return StrategyConfig(
            name="Walter Schloss Value Strategy",
            version="1.0.0",
            parameters={
                "min_market_cap": 1000000000,  # 10亿最小市值
                "max_pe_ratio": 15,
                "min_pb_ratio": 0.5,
                "max_pb_ratio": 1.5,
                "min_roe": 0.08,
                "max_debt_to_equity": 0.6,
                "min_current_ratio": 1.2,
                "min_revenue_growth": -0.1,
                "exclude_financial": True,
                "exclude_new_listings": True,
                "min_listing_years": 3,
            },
            weight_config={
                "value_score": 0.4,
                "quality_score": 0.3,
                "safety_score": 0.2,
                "growth_score": 0.1,
            },
            filters={
                "markets": ["A股", "US", "HK"],
                "exclude_sectors": ["银行", "保险", "证券"],
                "min_trading_days": 250,
                "min_avg_volume": 1000000,
            },
        )

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证输入数据是否满足策略要求

        Args:
            data: 股票数据DataFrame

        Returns:
            bool: 数据是否有效
        """
        required_columns = [
            "stock_code",
            "stock_name",
            "market_cap",
            "pe_ratio",
            "pb_ratio",
            "roe",
            "debt_to_equity",
            "current_ratio",
            "revenue_growth",
            "sector",
            "listing_date",
        ]

        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logging.error(f"缺少必要字段: {missing_columns}")
            return False

        if data.empty:
            logging.error("输入数据为空")
            return False

        return True

    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        应用Schloss策略的基础过滤条件

        Args:
            data: 股票数据DataFrame

        Returns:
            pd.DataFrame: 过滤后的数据
        """
        filtered_data = data.copy()
        params = self.config.parameters
        filters = self.config.filters

        # 1. 市值过滤
        if "min_market_cap" in params:
            filtered_data = filtered_data[
                filtered_data["market_cap"] >= params["min_market_cap"]
            ]

        # 2. 排除金融股（Walter Schloss不喜欢复杂的金融业务）
        if params.get("exclude_financial", True):
            excluded_sectors = filters.get("exclude_sectors", [])
            filtered_data = filtered_data[
                ~filtered_data["sector"].isin(excluded_sectors)
            ]

        # 3. 排除新上市股票（需要足够的历史数据）
        if params.get("exclude_new_listings", True):
            min_years = params.get("min_listing_years", 3)
            filtered_data = filtered_data[filtered_data["listing_years"] >= min_years]

        # 4. 基本财务指标过滤
        # P/E比率
        if "max_pe_ratio" in params:
            filtered_data = filtered_data[
                (filtered_data["pe_ratio"] > 0)
                & (filtered_data["pe_ratio"] <= params["max_pe_ratio"])
            ]

        # P/B比率
        if "min_pb_ratio" in params and "max_pb_ratio" in params:
            filtered_data = filtered_data[
                (filtered_data["pb_ratio"] >= params["min_pb_ratio"])
                & (filtered_data["pb_ratio"] <= params["max_pb_ratio"])
            ]

        # ROE
        if "min_roe" in params:
            filtered_data = filtered_data[filtered_data["roe"] >= params["min_roe"]]

        # 负债权益比
        if "max_debt_to_equity" in params:
            filtered_data = filtered_data[
                filtered_data["debt_to_equity"] <= params["max_debt_to_equity"]
            ]

        # 流动比率
        if "min_current_ratio" in params:
            filtered_data = filtered_data[
                filtered_data["current_ratio"] >= params["min_current_ratio"]
            ]

        # 5. 交易活跃度过滤
        if "min_trading_days" in filters:
            filtered_data = filtered_data[
                filtered_data["trading_days"] >= filters["min_trading_days"]
            ]

        if "min_avg_volume" in filters:
            filtered_data = filtered_data[
                filtered_data["avg_volume"] >= filters["min_avg_volume"]
            ]

        logging.info(f"过滤前: {len(data)} 只股票, 过滤后: {len(filtered_data)} 只股票")
        return filtered_data

    def calculate_criteria_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算各项指标得分

        Args:
            data: 股票数据DataFrame

        Returns:
            pd.DataFrame: 包含各项指标得分的DataFrame
        """
        scores_df = pd.DataFrame(index=data.index)

        # 1. 估值得分 (Value Score)
        scores_df["value_score"] = self._calculate_value_score(data)

        # 2. 质量得分 (Quality Score)
        scores_df["quality_score"] = self._calculate_quality_score(data)

        # 3. 安全得分 (Safety Score)
        scores_df["safety_score"] = self._calculate_safety_score(data)

        # 4. 成长得分 (Growth Score)
        scores_df["growth_score"] = self._calculate_growth_score(data)

        return scores_df

    def _calculate_value_score(self, data: pd.DataFrame) -> pd.Series:
        """计算估值得分"""
        value_scores = pd.Series(0.0, index=data.index)

        # P/E比率得分 (权重60%)
        pe_scores = self._score_by_ranges(
            data["pe_ratio"], self.pe_ranges, reverse=True
        )
        value_scores += pe_scores * 0.6

        # P/B比率得分 (权重40%)
        pb_scores = self._score_by_ranges(
            data["pb_ratio"], self.pb_ranges, reverse=True
        )
        value_scores += pb_scores * 0.4

        return value_scores

    def _calculate_quality_score(self, data: pd.DataFrame) -> pd.Series:
        """计算质量得分"""
        quality_scores = pd.Series(0.0, index=data.index)

        # ROE得分 (权重50%)
        roe_scores = self._score_by_ranges(data["roe"], self.roe_ranges)
        quality_scores += roe_scores * 0.5

        # ROA得分 (权重30%)，如果有的话
        if "roa" in data.columns:
            roa_scores = data["roa"].apply(
                lambda x: min(100, max(0, x * 1000))
            )  # 简化评分
            quality_scores += roa_scores * 0.3
        else:
            quality_scores += 50 * 0.3  # 默认中等分数

        # 毛利率得分 (权重20%)
        if "gross_margin" in data.columns:
            gross_margin_scores = data["gross_margin"].apply(
                lambda x: min(100, max(0, x * 200))
            )
            quality_scores += gross_margin_scores * 0.2
        else:
            quality_scores += 50 * 0.2

        return quality_scores

    def _calculate_safety_score(self, data: pd.DataFrame) -> pd.Series:
        """计算安全得分"""
        safety_scores = pd.Series(0.0, index=data.index)

        # 负债权益比得分 (权重40%)
        debt_scores = self._score_by_ranges(
            data["debt_to_equity"], self.debt_ranges, reverse=True
        )
        safety_scores += debt_scores * 0.4

        # 流动比率得分 (权重30%)
        current_ratio_scores = data["current_ratio"].apply(
            lambda x: min(100, max(0, (x - 1) * 50)) if x >= 1 else 0
        )
        safety_scores += current_ratio_scores * 0.3

        # 现金比率得分 (权重20%)
        if "cash_ratio" in data.columns:
            cash_scores = data["cash_ratio"].apply(lambda x: min(100, max(0, x * 200)))
            safety_scores += cash_scores * 0.2
        else:
            safety_scores += 50 * 0.2

        # 利息覆盖倍数得分 (权重10%)
        if "interest_coverage" in data.columns:
            interest_scores = data["interest_coverage"].apply(
                lambda x: min(100, max(0, x * 10)) if x > 0 else 0
            )
            safety_scores += interest_scores * 0.1
        else:
            safety_scores += 50 * 0.1

        return safety_scores

    def _calculate_growth_score(self, data: pd.DataFrame) -> pd.Series:
        """计算成长得分（Schloss不太关注，但适度考虑）"""
        growth_scores = pd.Series(0.0, index=data.index)

        # 营收增长得分 (权重60%)
        revenue_growth_scores = data["revenue_growth"].apply(
            lambda x: min(100, max(0, (x + 0.1) * 200))  # -10%到40%映射到0-100
        )
        growth_scores += revenue_growth_scores * 0.6

        # 净利润增长得分 (权重40%)
        if "profit_growth" in data.columns:
            profit_growth_scores = data["profit_growth"].apply(
                lambda x: min(100, max(0, (x + 0.1) * 200))
            )
            growth_scores += profit_growth_scores * 0.4
        else:
            growth_scores += revenue_growth_scores * 0.4  # 使用营收增长代替

        return growth_scores

    def _score_by_ranges(
        self, series: pd.Series, ranges: Dict[str, List[float]], reverse: bool = False
    ) -> pd.Series:
        """
        根据区间配置计算得分

        Args:
            series: 数据序列
            ranges: 评分区间配置
            reverse: 是否反向评分（值越小得分越高）

        Returns:
            pd.Series: 得分序列
        """
        scores = pd.Series(0.0, index=series.index)

        if not ranges:
            return scores

        # 定义得分映射
        score_mapping = {"excellent": 90, "good": 70, "fair": 50, "poor": 20}

        for level, (min_val, max_val) in ranges.items():
            mask = (series >= min_val) & (series < max_val)
            scores[mask] = score_mapping.get(level, 50)

        return scores

    def generate_reasons(self, row: pd.Series, criteria_scores: pd.Series) -> List[str]:
        """生成Schloss策略特定的选中原因"""
        reasons = []

        # 估值方面
        if criteria_scores["value_score"] > 70:
            reasons.append(
                f"估值合理 - P/E: {row.get('pe_ratio', 'N/A'):.1f}, P/B: {row.get('pb_ratio', 'N/A'):.1f}"
            )

        # 质量方面
        if criteria_scores["quality_score"] > 70:
            reasons.append(f"盈利能力强 - ROE: {row.get('roe', 0)*100:.1f}%")

        # 安全方面
        if criteria_scores["safety_score"] > 70:
            debt_ratio = row.get("debt_to_equity", 0)
            current_ratio = row.get("current_ratio", 0)
            reasons.append(
                f"财务稳健 - 负债率: {debt_ratio:.1f}, 流动比率: {current_ratio:.1f}"
            )

        # Schloss特色原因
        if row.get("pe_ratio", 999) < 10:
            reasons.append("低市盈率价值股（P/E < 10）")

        if row.get("pb_ratio", 999) < 1.0:
            reasons.append("破净股机会（P/B < 1.0）")

        if row.get("debt_to_equity", 999) < 0.3:
            reasons.append("低负债安全边际")

        return reasons

    def generate_warnings(
        self, row: pd.Series, criteria_scores: pd.Series
    ) -> List[str]:
        """生成Schloss策略特定的风险警告"""
        warnings = []

        # 估值警告
        if row.get("pe_ratio", 0) > 20:
            warnings.append(f"市盈率偏高 (P/E: {row.get('pe_ratio'):.1f})")

        if row.get("pb_ratio", 0) > 2.0:
            warnings.append(f"市净率偏高 (P/B: {row.get('pb_ratio'):.1f})")

        # 财务警告
        if row.get("debt_to_equity", 0) > 0.5:
            warnings.append(f"负债水平较高 ({row.get('debt_to_equity'):.1f})")

        if row.get("current_ratio", 0) < 1.5:
            warnings.append(f"流动性不足 (流动比率: {row.get('current_ratio'):.1f})")

        # 业务警告
        if row.get("revenue_growth", 0) < -0.2:
            warnings.append(f"营收大幅下滑 ({row.get('revenue_growth', 0)*100:.1f}%)")

        # 市场警告
        if row.get("market_cap", 0) < 500000000:  # 5亿以下
            warnings.append("小市值股票，流动性风险")

        return warnings
