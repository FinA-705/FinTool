"""
仓位管理器

处理仓位分配和目标仓位生成
"""

from typing import Dict, Any
import pandas as pd
from strategies.strategy_engine import StrategyResult

from .backtest_types import BacktestConfig, Portfolio
from utils.logger import get_logger

logger = get_logger(__name__)


class PositionManager:
    """仓位管理器"""

    def __init__(self, config: BacktestConfig, portfolio: Portfolio):
        """初始化仓位管理器

        Args:
            config: 回测配置
            portfolio: 投资组合
        """
        self.config = config
        self.portfolio = portfolio

    def generate_target_positions(
        self, strategy_result: StrategyResult
    ) -> Dict[str, float]:
        """生成目标仓位

        Args:
            strategy_result: 策略结果

        Returns:
            目标仓位字典 {symbol: target_value}
        """
        target_positions = {}

        if strategy_result.filtered_stocks.empty:
            return target_positions

        # 计算可用资金
        available_cash = self.portfolio.total_value

        if self.config.position_size_method == "equal_weight":
            # 等权重分配
            target_positions = self._equal_weight_allocation(
                strategy_result.filtered_stocks, available_cash
            )

        elif (
            self.config.position_size_method == "score_weight"
            and strategy_result.scores is not None
        ):
            # 基于评分加权
            target_positions = self._score_weight_allocation(
                strategy_result.filtered_stocks, strategy_result.scores, available_cash
            )

        elif self.config.position_size_method == "market_cap_weight":
            # 市值加权
            target_positions = self._market_cap_weight_allocation(
                strategy_result.filtered_stocks, available_cash
            )

        elif self.config.position_size_method == "risk_parity":
            # 风险平价
            target_positions = self._risk_parity_allocation(
                strategy_result.filtered_stocks, available_cash
            )

        return target_positions

    def _equal_weight_allocation(
        self, stocks: pd.DataFrame, available_cash: float
    ) -> Dict[str, float]:
        """等权重分配

        Args:
            stocks: 选中的股票
            available_cash: 可用资金

        Returns:
            目标仓位字典
        """
        target_positions = {}
        num_stocks = len(stocks)

        if num_stocks == 0:
            return target_positions

        weight_per_stock = 1.0 / num_stocks

        for _, stock in stocks.iterrows():
            symbol = stock["code"]
            target_value = available_cash * weight_per_stock
            target_positions[symbol] = target_value

        return target_positions

    def _score_weight_allocation(
        self, stocks: pd.DataFrame, scores: pd.Series, available_cash: float
    ) -> Dict[str, float]:
        """基于评分加权分配

        Args:
            stocks: 选中的股票
            scores: 评分
            available_cash: 可用资金

        Returns:
            目标仓位字典
        """
        target_positions = {}

        # 确保评分为正数
        min_score = scores.min()
        if min_score <= 0:
            scores = scores - min_score + 0.01

        total_score = scores.sum()

        for symbol, score in scores.items():
            if symbol in stocks["code"].values:
                weight = score / total_score
                target_value = available_cash * weight
                target_positions[symbol] = target_value

        return target_positions

    def _market_cap_weight_allocation(
        self, stocks: pd.DataFrame, available_cash: float
    ) -> Dict[str, float]:
        """市值加权分配

        Args:
            stocks: 选中的股票
            available_cash: 可用资金

        Returns:
            目标仓位字典
        """
        target_positions = {}

        if "market_cap" not in stocks.columns:
            logger.warning("缺少市值数据，使用等权重分配")
            return self._equal_weight_allocation(stocks, available_cash)

        total_market_cap = stocks["market_cap"].sum()

        for _, stock in stocks.iterrows():
            symbol = stock["code"]
            weight = stock["market_cap"] / total_market_cap
            target_value = available_cash * weight
            target_positions[symbol] = target_value

        return target_positions

    def _risk_parity_allocation(
        self, stocks: pd.DataFrame, available_cash: float
    ) -> Dict[str, float]:
        """风险平价分配

        Args:
            stocks: 选中的股票
            available_cash: 可用资金

        Returns:
            目标仓位字典
        """
        target_positions = {}

        # 如果没有风险数据，使用等权重
        if "volatility" not in stocks.columns:
            logger.warning("缺少波动率数据，使用等权重分配")
            return self._equal_weight_allocation(stocks, available_cash)

        # 风险平价：权重与风险成反比
        risks = stocks["volatility"]
        inv_risks = 1.0 / risks
        total_inv_risk = inv_risks.sum()

        for _, stock in stocks.iterrows():
            symbol = stock["code"]
            weight = (1.0 / stock["volatility"]) / total_inv_risk
            target_value = available_cash * weight
            target_positions[symbol] = target_value

        return target_positions

    def should_rebalance(self, date, day_index: int) -> bool:
        """判断是否应该调仓

        Args:
            date: 当前日期
            day_index: 日期索引

        Returns:
            是否应该调仓
        """
        if day_index == 0:  # 第一天
            return True

        if self.config.rebalance_frequency == "daily":
            return True
        elif self.config.rebalance_frequency == "weekly":
            return date.weekday() == 0  # 周一
        elif self.config.rebalance_frequency == "monthly":
            return date.day == 1 or day_index == 0  # 每月第一天
        elif self.config.rebalance_frequency == "quarterly":
            return date.month in [1, 4, 7, 10] and date.day == 1
        else:
            return False
