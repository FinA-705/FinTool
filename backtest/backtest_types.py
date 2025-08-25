"""
回测数据类型定义

包含回测引擎使用的所有数据类和枚举
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    """订单类型"""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """订单信息"""

    id: str
    symbol: str
    order_type: OrderType
    quantity: int
    price: float
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_time: Optional[datetime] = None
    commission: float = 0.0


@dataclass
class Position:
    """持仓信息"""

    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float

    @property
    def total_cost(self) -> float:
        return self.quantity * self.avg_cost

    @property
    def total_pnl(self) -> float:
        return self.unrealized_pnl + self.realized_pnl


@dataclass
class Portfolio:
    """投资组合信息"""

    cash: float
    positions: Dict[str, Position]
    total_value: float
    daily_returns: List[float]

    def get_position_value(self) -> float:
        """获取持仓总价值"""
        return sum(pos.market_value for pos in self.positions.values())

    def get_total_pnl(self) -> float:
        """获取总盈亏"""
        return sum(pos.total_pnl for pos in self.positions.values())


@dataclass
class BacktestConfig:
    """回测配置"""

    start_date: datetime
    end_date: datetime
    initial_capital: float
    commission_rate: float = 0.0003  # 万分之三手续费
    min_commission: float = 5.0  # 最低手续费
    slippage_rate: float = 0.001  # 滑点率
    position_size_method: str = "equal_weight"  # 仓位分配方法
    max_positions: int = 20  # 最大持仓数量
    rebalance_frequency: str = "monthly"  # 调仓频率
    benchmark: Optional[str] = None  # 基准指数
