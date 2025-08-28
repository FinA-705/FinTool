"""
回测绩效指标计算模块

提供全面的投资组合绩效分析指标
包括收益率、风险、回撤、比率等各类指标
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from dataclasses import dataclass

from utils.logger import get_logger
from backtest.metrics_calculator import MetricsCalculator
from backtest.report_generator import ReportGenerator

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""

    # 收益率指标
    total_return: float
    annual_return: float
    monthly_return: float
    daily_return: float

    # 风险指标
    volatility: float
    downside_volatility: float
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR

    # 回撤指标
    max_drawdown: float
    max_drawdown_duration: int
    current_drawdown: float
    avg_drawdown: float

    # 风险调整收益指标
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float

    # 基准相关指标
    beta: Optional[float] = None
    alpha: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None
    up_capture: Optional[float] = None
    down_capture: Optional[float] = None

    # 交易统计
    total_trades: int = 0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    avg_trade_return: float = 0.0

    # 其他指标
    skewness: float = 0.0
    kurtosis: float = 0.0
    best_day: float = 0.0
    worst_day: float = 0.0
    positive_days: float = 0.0


class PerformanceAnalyzer:
    """绩效分析器"""

    def __init__(self, risk_free_rate: float = 0.03):
        """初始化绩效分析器"""
        self.calculator = MetricsCalculator(risk_free_rate)
        self.reporter = ReportGenerator()

    def calculate_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
    ) -> PerformanceMetrics:
        """计算完整的绩效指标"""
        if len(returns) == 0:
            return self._default_metrics()

        returns = returns.dropna()
        if len(returns) == 0:
            return self._default_metrics()

        # 基础收益率指标
        total_return = self.calculator.calculate_total_return(returns)
        annual_return = self.calculator.calculate_annual_return(returns)
        monthly_return = self.calculator.calculate_monthly_return(returns)
        daily_return = returns.mean()

        # 风险指标
        volatility = self.calculator.calculate_volatility(returns)
        downside_volatility = self.calculator.calculate_downside_volatility(returns)
        var_95 = self.calculator.calculate_var(returns, 0.05)
        cvar_95 = self.calculator.calculate_cvar(returns, 0.05)

        # 回撤指标
        drawdown_metrics = self.calculator.calculate_drawdown_metrics(returns)

        # 风险调整收益指标
        sharpe_ratio = self.calculator.calculate_sharpe_ratio(annual_return, volatility)
        sortino_ratio = self.calculator.calculate_sortino_ratio(
            annual_return, downside_volatility
        )
        calmar_ratio = self.calculator.calculate_calmar_ratio(
            annual_return, drawdown_metrics["max_drawdown"]
        )
        omega_ratio = self.calculator.calculate_omega_ratio(returns)

        # 统计特征
        skewness = self.calculator.calculate_skewness(returns)
        kurtosis = self.calculator.calculate_kurtosis(returns)
        best_day = returns.max()
        worst_day = returns.min()
        positive_days = (returns > 0).mean()

        # 基准相关指标
        benchmark_metrics = {}
        if benchmark_returns is not None:
            benchmark_metrics = self.calculator.calculate_benchmark_metrics(
                returns, benchmark_returns
            )

        # 交易统计
        trade_metrics = {}
        if trades is not None:
            trade_metrics = self.calculator.calculate_trade_metrics(trades)

        return PerformanceMetrics(
            total_return=total_return,
            annual_return=annual_return,
            monthly_return=monthly_return,
            daily_return=daily_return,
            volatility=volatility,
            downside_volatility=downside_volatility,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=drawdown_metrics["max_drawdown"],
            max_drawdown_duration=drawdown_metrics["max_drawdown_duration"],
            current_drawdown=drawdown_metrics["current_drawdown"],
            avg_drawdown=drawdown_metrics["avg_drawdown"],
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            omega_ratio=omega_ratio,
            skewness=skewness,
            kurtosis=kurtosis,
            best_day=best_day,
            worst_day=worst_day,
            positive_days=positive_days,
            **benchmark_metrics,
            **trade_metrics,
        )

    def generate_performance_report(self, metrics: PerformanceMetrics) -> str:
        """生成绩效报告"""
        return self.reporter.generate_performance_report(metrics)

    def _default_metrics(self) -> PerformanceMetrics:
        """返回默认的空指标"""
        return PerformanceMetrics(
            total_return=0.0,
            annual_return=0.0,
            monthly_return=0.0,
            daily_return=0.0,
            volatility=0.0,
            downside_volatility=0.0,
            var_95=0.0,
            cvar_95=0.0,
            max_drawdown=0.0,
            max_drawdown_duration=0,
            current_drawdown=0.0,
            avg_drawdown=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            omega_ratio=0.0,
        )


# 使用示例
if __name__ == "__main__":
    import numpy as np

    print("=== 绩效指标计算模块测试 ===")

    # 生成模拟收益率数据
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")

    # 模拟策略收益率
    strategy_returns = pd.Series(
        np.random.normal(0.0008, 0.015, len(dates)), index=dates
    )

    # 模拟基准收益率
    benchmark_returns = pd.Series(
        np.random.normal(0.0005, 0.012, len(dates)), index=dates
    )

    # 创建模拟交易数据
    trades = [{"action": "buy", "pnl": np.random.normal(1000, 5000)} for i in range(50)]

    # 创建绩效分析器
    analyzer = PerformanceAnalyzer(risk_free_rate=0.03)

    # 计算绩效指标
    print("计算绩效指标...")
    metrics = analyzer.calculate_metrics(
        returns=strategy_returns, benchmark_returns=benchmark_returns, trades=trades
    )

    # 生成报告
    print("\n" + analyzer.generate_performance_report(metrics))

    print("绩效指标计算模块测试完成！")
