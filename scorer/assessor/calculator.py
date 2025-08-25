"""
风险指标计算器
"""
import pandas as pd
import numpy as np
from typing import Optional
from .models import RiskMetrics, RiskConfig


class MetricsCalculator:
    """风险指标计算器"""

    def __init__(self, config: RiskConfig):
        self.config = config

    def calculate(
        self, returns: pd.Series, market_returns: Optional[pd.Series] = None
    ) -> RiskMetrics:
        """计算所有风险指标"""
        volatility = self._calculate_volatility(returns)
        max_drawdown = self._calculate_max_drawdown(returns)
        var_95 = self._calculate_var(returns, self.config.confidence_level)
        cvar_95 = self._calculate_cvar(returns, self.config.confidence_level)
        sharpe_ratio = self._calculate_sharpe_ratio(returns)
        sortino_ratio = self._calculate_sortino_ratio(returns)

        beta, alpha = None, None
        if market_returns is not None:
            aligned_data = pd.concat([returns, market_returns], axis=1, join="inner")
            if len(aligned_data) >= self.config.min_periods:
                stock_returns = aligned_data.iloc[:, 0]
                market_returns_aligned = aligned_data.iloc[:, 1]
                beta = self._calculate_beta(stock_returns, market_returns_aligned)
                alpha = self._calculate_alpha(stock_returns, market_returns_aligned, beta)

        return RiskMetrics(
            volatility=volatility,
            max_drawdown=max_drawdown,
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            beta=beta,
            alpha=alpha,
        )

    def _calculate_volatility(self, returns: pd.Series) -> float:
        return float(returns.std() * np.sqrt(252))

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())

    def _calculate_var(self, returns: pd.Series, confidence_level: float) -> float:
        return float(np.percentile(returns, (1 - confidence_level) * 100))

    def _calculate_cvar(self, returns: pd.Series, confidence_level: float) -> float:
        var = self._calculate_var(returns, confidence_level)
        return float(returns[returns <= var].mean())

    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        excess_returns = returns - self.config.risk_free_rate / 252
        if excess_returns.std() == 0:
            return 0.0
        return float(excess_returns.mean() / excess_returns.std() * np.sqrt(252))

    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        excess_returns = returns - self.config.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return float(excess_returns.mean() / downside_returns.std() * np.sqrt(252))

    def _calculate_beta(
        self, stock_returns: pd.Series, market_returns: pd.Series
    ) -> float:
        covariance = np.cov(stock_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        if market_variance == 0:
            return 1.0
        return float(covariance / market_variance)

    def _calculate_alpha(
        self, stock_returns: pd.Series, market_returns: pd.Series, beta: float
    ) -> float:
        stock_mean = stock_returns.mean() * 252
        market_mean = market_returns.mean() * 252
        return float(
            stock_mean
            - (
                self.config.risk_free_rate
                + beta * (market_mean - self.config.risk_free_rate)
            )
        )
