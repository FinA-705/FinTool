"""
回测交易管理器

处理订单执行、仓位管理和交易记录
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime
import uuid

from .backtest_types import (
    Order,
    OrderType,
    OrderStatus,
    Position,
    Portfolio,
    BacktestConfig,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class TradeManager:
    """交易管理器"""

    def __init__(self, config: BacktestConfig, portfolio: Portfolio):
        """初始化交易管理器

        Args:
            config: 回测配置
            portfolio: 投资组合
        """
        self.config = config
        self.portfolio = portfolio
        self.orders: List[Order] = []
        self.trades: List[Dict[str, Any]] = []

    def execute_trades(
        self,
        target_positions: Dict[str, float],
        daily_data: pd.DataFrame,
        current_date: datetime,
    ):
        """执行交易

        Args:
            target_positions: 目标仓位字典 {symbol: target_value}
            daily_data: 当日数据
            current_date: 当前日期
        """
        # 先卖出不在目标中的股票
        current_symbols = set(self.portfolio.positions.keys())
        target_symbols = set(target_positions.keys())

        symbols_to_sell = current_symbols - target_symbols
        for symbol in symbols_to_sell:
            self._sell_position(symbol, daily_data, current_date)

        # 买入或调整目标仓位
        for symbol, target_value in target_positions.items():
            self._adjust_position(symbol, target_value, daily_data, current_date)

    def _sell_position(
        self,
        symbol: str,
        daily_data: pd.DataFrame,
        current_date: datetime,
        quantity: Optional[int] = None,
    ):
        """卖出持仓

        Args:
            symbol: 股票代码
            daily_data: 当日数据
            current_date: 当前日期
            quantity: 卖出数量，None表示全部卖出
        """
        if symbol not in self.portfolio.positions:
            return

        position = self.portfolio.positions[symbol]

        # 获取卖出价格
        stock_data = daily_data[daily_data["code"] == symbol]
        if stock_data.empty:
            logger.warning(f"无法找到 {symbol} 的价格数据")
            return

        sell_price = stock_data["close"].iloc[0]

        # 应用滑点
        sell_price *= 1 - self.config.slippage_rate

        # 确定卖出数量
        quantity_to_sell = quantity or position.quantity

        if quantity_to_sell <= 0:
            return

        # 计算交易金额
        trade_value = quantity_to_sell * sell_price
        commission = max(
            trade_value * self.config.commission_rate, self.config.min_commission
        )
        net_proceeds = trade_value - commission

        # 计算已实现盈亏
        realized_pnl = (sell_price - position.avg_cost) * quantity_to_sell

        # 创建卖出订单
        order = Order(
            id=f"sell_{symbol}_{current_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            symbol=symbol,
            order_type=OrderType.SELL,
            quantity=quantity_to_sell,
            price=sell_price,
            timestamp=current_date,
            status=OrderStatus.FILLED,
            filled_price=sell_price,
            filled_time=current_date,
            commission=commission,
        )

        # 更新投资组合
        self.portfolio.cash += net_proceeds

        if quantity_to_sell == position.quantity:
            # 全部卖出，删除持仓
            del self.portfolio.positions[symbol]
        else:
            # 部分卖出，更新持仓
            position.quantity -= quantity_to_sell
            position.market_value = position.quantity * position.current_price
            position.unrealized_pnl = (
                position.current_price - position.avg_cost
            ) * position.quantity
            position.realized_pnl += realized_pnl

        # 记录订单和交易
        self.orders.append(order)
        self.trades.append(
            {
                "date": current_date,
                "symbol": symbol,
                "action": "sell",
                "quantity": quantity_to_sell,
                "price": sell_price,
                "value": trade_value,
                "commission": commission,
                "pnl": realized_pnl,
            }
        )

        logger.debug(
            f"卖出 {symbol}: {quantity_to_sell}股 @ {sell_price:.2f}, PnL: {realized_pnl:.2f}"
        )

    def _adjust_position(
        self,
        symbol: str,
        target_value: float,
        daily_data: pd.DataFrame,
        current_date: datetime,
    ):
        """调整仓位到目标金额

        Args:
            symbol: 股票代码
            target_value: 目标持仓金额
            daily_data: 当日数据
            current_date: 当前日期
        """
        # 获取当前价格
        stock_data = daily_data[daily_data["code"] == symbol]
        if stock_data.empty:
            logger.warning(f"无法找到 {symbol} 的价格数据")
            return

        current_price = stock_data["close"].iloc[0]
        buy_price = current_price * (1 + self.config.slippage_rate)

        # 计算目标数量
        target_quantity = int(target_value / buy_price)

        if target_quantity <= 0:
            return

        # 当前持仓数量
        current_quantity = 0
        if symbol in self.portfolio.positions:
            current_quantity = self.portfolio.positions[symbol].quantity

        # 计算需要调整的数量
        quantity_diff = target_quantity - current_quantity

        if quantity_diff > 0:
            # 需要买入
            self._buy_position(symbol, quantity_diff, daily_data, current_date)
        elif quantity_diff < 0:
            # 需要卖出
            self._sell_position(symbol, daily_data, current_date, abs(quantity_diff))

    def _buy_position(
        self,
        symbol: str,
        quantity_to_buy: int,
        daily_data: pd.DataFrame,
        current_date: datetime,
    ):
        """买入指定数量的股票

        Args:
            symbol: 股票代码
            quantity_to_buy: 买入数量
            daily_data: 当日数据
            current_date: 当前日期
        """
        # 获取价格
        stock_data = daily_data[daily_data["code"] == symbol]
        if stock_data.empty:
            return

        current_price = stock_data["close"].iloc[0]
        buy_price = current_price * (1 + self.config.slippage_rate)

        # 计算交易成本
        trade_value = quantity_to_buy * buy_price
        commission = max(
            trade_value * self.config.commission_rate, self.config.min_commission
        )
        total_cost = trade_value + commission

        # 检查现金是否足够
        if total_cost > self.portfolio.cash:
            # 资金不足，按现金调整
            available_cash = self.portfolio.cash * 0.99  # 留一点余量
            quantity_to_buy = int(
                available_cash / (buy_price * (1 + self.config.commission_rate))
            )

            if quantity_to_buy <= 0:
                return

            trade_value = quantity_to_buy * buy_price
            commission = max(
                trade_value * self.config.commission_rate, self.config.min_commission
            )
            total_cost = trade_value + commission

        # 创建买入订单
        order = Order(
            id=f"buy_{symbol}_{current_date.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}",
            symbol=symbol,
            order_type=OrderType.BUY,
            quantity=quantity_to_buy,
            price=buy_price,
            timestamp=current_date,
            status=OrderStatus.FILLED,
            filled_price=buy_price,
            filled_time=current_date,
            commission=commission,
        )

        # 更新投资组合
        self.portfolio.cash -= total_cost

        if symbol in self.portfolio.positions:
            # 更新现有持仓
            position = self.portfolio.positions[symbol]
            old_cost = position.avg_cost * position.quantity
            new_cost = buy_price * quantity_to_buy
            position.avg_cost = (old_cost + new_cost) / (
                position.quantity + quantity_to_buy
            )
            position.quantity += quantity_to_buy
            position.current_price = current_price
            position.market_value = position.quantity * current_price
            position.unrealized_pnl = (
                current_price - position.avg_cost
            ) * position.quantity
        else:
            # 创建新持仓
            self.portfolio.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity_to_buy,
                avg_cost=buy_price,
                current_price=current_price,
                market_value=quantity_to_buy * current_price,
                unrealized_pnl=(current_price - buy_price) * quantity_to_buy,
                realized_pnl=0.0,
            )

        # 记录订单和交易
        self.orders.append(order)
        self.trades.append(
            {
                "date": current_date,
                "symbol": symbol,
                "action": "buy",
                "quantity": quantity_to_buy,
                "price": buy_price,
                "value": trade_value,
                "commission": commission,
                "pnl": 0.0,
            }
        )

        logger.debug(f"买入 {symbol}: {quantity_to_buy}股 @ {buy_price:.2f}")

    def update_positions_prices(self, daily_data: pd.DataFrame):
        """更新持仓价格

        Args:
            daily_data: 当日数据
        """
        for symbol, position in self.portfolio.positions.items():
            # 查找当前股票价格
            stock_data = daily_data[daily_data["code"] == symbol]
            if not stock_data.empty:
                current_price = stock_data["close"].iloc[0]
                position.current_price = current_price
                position.market_value = position.quantity * current_price
                position.unrealized_pnl = (
                    current_price - position.avg_cost
                ) * position.quantity

        # 更新组合总价值
        self.portfolio.total_value = (
            self.portfolio.cash + self.portfolio.get_position_value()
        )
