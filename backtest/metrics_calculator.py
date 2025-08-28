"""
绩效指标计算器模块
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_skewness(data: np.ndarray) -> float:
    """计算偏度"""
    if len(data) <= 2:
        return 0.0
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    if std == 0:
        return 0.0
    return float(np.mean(((data - mean) / std) ** 3))


def calculate_kurtosis(data: np.ndarray) -> float:
    """计算峰度"""
    if len(data) <= 3:
        return 0.0
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    if std == 0:
        return 0.0
    return float(np.mean(((data - mean) / std) ** 4) - 3)


class MetricsCalculator:
    """绩效指标计算器"""

    def __init__(self, risk_free_rate: float = 0.03):
        self.risk_free_rate = risk_free_rate

    def calculate_total_return(self, returns: pd.Series) -> float:
        """计算总收益率"""
        try:
            cumulative = (1 + returns).cumprod()
            if len(cumulative) > 0:
                result = cumulative.iloc[-1] - 1
                return float(result) if pd.notna(result) else 0.0
            return 0.0
        except (TypeError, ValueError):
            return 0.0

    def calculate_annual_return(self, returns: pd.Series) -> float:
        """计算年化收益率"""
        if len(returns) == 0:
            return 0.0
        total_return = self.calculate_total_return(returns)
        days = len(returns)
        years = days / 252
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1

    def calculate_monthly_return(self, returns: pd.Series) -> float:
        """计算月化收益率"""
        annual_return = self.calculate_annual_return(returns)
        return (1 + annual_return) ** (1 / 12) - 1

    def calculate_volatility(
        self, returns: pd.Series, annualized: bool = True
    ) -> float:
        """计算波动率"""
        if len(returns) <= 1:
            return 0.0
        vol = returns.std()
        if annualized:
            vol *= np.sqrt(252)
        return vol

    def calculate_downside_volatility(
        self, returns: pd.Series, target_return: float = 0.0, annualized: bool = True
    ) -> float:
        """计算下行波动率"""
        downside_returns = returns[returns < target_return]
        if len(downside_returns) <= 1:
            return 0.0
        downside_vol = downside_returns.std()
        if annualized:
            downside_vol *= np.sqrt(252)
        return downside_vol

    def calculate_var(self, returns: pd.Series, confidence_level: float) -> float:
        """计算风险价值(VaR)"""
        if len(returns) == 0:
            return 0.0
        return float(-np.percentile(returns, confidence_level * 100))

    def calculate_cvar(self, returns: pd.Series, confidence_level: float) -> float:
        """计算条件风险价值(CVaR)"""
        if len(returns) == 0:
            return 0.0
        var = self.calculate_var(returns, confidence_level)
        tail_losses = returns[returns <= -var]
        if len(tail_losses) == 0:
            return var
        return -tail_losses.mean()

    def calculate_drawdown_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """计算回撤相关指标"""
        if len(returns) == 0:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_duration": 0,
                "current_drawdown": 0.0,
                "avg_drawdown": 0.0,
            }
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdowns = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        current_drawdown = drawdowns.iloc[-1] if len(drawdowns) > 0 else 0.0
        negative_drawdowns = drawdowns[drawdowns < 0]
        avg_drawdown = negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0.0
        max_drawdown_duration = self._calculate_max_drawdown_duration(drawdowns)
        return {
            "max_drawdown": max_drawdown,
            "max_drawdown_duration": max_drawdown_duration,
            "current_drawdown": current_drawdown,
            "avg_drawdown": avg_drawdown,
        }

    def _calculate_max_drawdown_duration(self, drawdowns: pd.Series) -> int:
        """计算最大回撤持续时间"""
        if len(drawdowns) == 0:
            return 0
        in_drawdown = drawdowns < 0
        max_duration = 0
        current_duration = 0
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        return max_duration

    def calculate_sharpe_ratio(self, annual_return: float, volatility: float) -> float:
        """计算夏普比率"""
        if volatility == 0:
            return 0.0
        excess_return = annual_return - self.risk_free_rate
        return excess_return / volatility

    def calculate_sortino_ratio(
        self, annual_return: float, downside_volatility: float
    ) -> float:
        """计算索提诺比率"""
        if downside_volatility == 0:
            return 0.0
        excess_return = annual_return - self.risk_free_rate
        return excess_return / downside_volatility

    def calculate_calmar_ratio(
        self, annual_return: float, max_drawdown: float
    ) -> float:
        """计算卡玛比率"""
        if max_drawdown == 0:
            return 0.0
        return annual_return / abs(max_drawdown)

    def calculate_omega_ratio(
        self, returns: pd.Series, target_return: float = 0.0
    ) -> float:
        """计算欧米伽比率"""
        if len(returns) == 0:
            return 0.0
        gains = returns[returns > target_return] - target_return
        losses = target_return - returns[returns <= target_return]
        if losses.sum() == 0:
            return float("inf") if gains.sum() > 0 else 1.0
        return gains.sum() / losses.sum()

    def calculate_skewness(self, returns: pd.Series) -> float:
        """计算偏度"""
        if len(returns) <= 2:
            return 0.0
        return calculate_skewness(np.array(returns.dropna().values))

    def calculate_kurtosis(self, returns: pd.Series) -> float:
        """计算峰度"""
        if len(returns) <= 3:
            return 0.0
        return calculate_kurtosis(np.array(returns.dropna().values))

    def calculate_benchmark_metrics(
        self, returns: pd.Series, benchmark_returns: pd.Series
    ) -> Dict[str, float]:
        """计算相对基准的指标"""
        aligned_data = pd.DataFrame(
            {"portfolio": returns, "benchmark": benchmark_returns}
        ).dropna()
        if len(aligned_data) <= 1:
            return {}
        portfolio_ret = aligned_data["portfolio"]
        benchmark_ret = aligned_data["benchmark"]
        covariance = np.cov(portfolio_ret, benchmark_ret)[0, 1]
        benchmark_variance = np.var(benchmark_ret)
        beta = covariance / benchmark_variance if benchmark_variance != 0 else 0.0
        portfolio_annual = self.calculate_annual_return(portfolio_ret)
        benchmark_annual = self.calculate_annual_return(benchmark_ret)
        alpha = portfolio_annual - (
            self.risk_free_rate + beta * (benchmark_annual - self.risk_free_rate)
        )
        excess_returns = portfolio_ret - benchmark_ret
        tracking_error = self.calculate_volatility(excess_returns)
        information_ratio = (
            excess_returns.mean() * np.sqrt(252) / tracking_error
            if tracking_error != 0
            else 0.0
        )
        up_periods = benchmark_ret > 0
        down_periods = benchmark_ret <= 0
        up_capture = 0.0
        down_capture = 0.0
        if up_periods.sum() > 0:
            portfolio_up_return = portfolio_ret[up_periods].mean()
            benchmark_up_return = benchmark_ret[up_periods].mean()
            up_capture = (
                portfolio_up_return / benchmark_up_return
                if benchmark_up_return != 0
                else 0.0
            )
        if down_periods.sum() > 0:
            portfolio_down_return = portfolio_ret[down_periods].mean()
            benchmark_down_return = benchmark_ret[down_periods].mean()
            down_capture = (
                portfolio_down_return / benchmark_down_return
                if benchmark_down_return != 0
                else 0.0
            )
        return {
            "beta": beta,
            "alpha": alpha,
            "tracking_error": tracking_error,
            "information_ratio": information_ratio,
            "up_capture": up_capture,
            "down_capture": down_capture,
        }

    def calculate_trade_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算交易统计指标"""
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_loss_ratio": 0.0,
                "avg_trade_return": 0.0,
            }
        buy_trades = [t for t in trades if t.get("action") == "buy"]
        total_trades = len(buy_trades)
        if total_trades == 0:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_loss_ratio": 0.0,
                "avg_trade_return": 0.0,
            }
        profitable_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        win_rate = len(profitable_trades) / total_trades
        avg_profit = (
            np.mean([t["pnl"] for t in profitable_trades]) if profitable_trades else 0
        )
        avg_loss = (
            abs(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 0
        )
        profit_loss_ratio = avg_profit / avg_loss if avg_loss != 0 else 0.0
        avg_trade_return = np.mean([t.get("pnl", 0) for t in trades])
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "avg_trade_return": avg_trade_return,
        }
