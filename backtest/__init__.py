"""
回测模块

提供策略回测和性能分析功能：
- 历史数据回测
- 性能指标计算
- 风险度量
- 交易管理
- 仓位管理
"""

from .backtester import BacktestEngine
from .backtest_types import (
    BacktestConfig,
    Portfolio,
    Position,
    Order,
    OrderType,
    OrderStatus,
)
from .trade_manager import TradeManager
from .position_manager import PositionManager
from .performance_metrics import PerformanceAnalyzer

__all__ = [
    "BacktestEngine",
    "BacktestConfig",
    "Portfolio",
    "Position",
    "Order",
    "OrderType",
    "OrderStatus",
    "TradeManager",
    "PositionManager",
    "PerformanceAnalyzer",
]
