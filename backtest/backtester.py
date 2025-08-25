"""
历史数据回测引擎

支持多策略、多市场的历史回测
包含交易信号生成、仓位管理、绩效统计等功能
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategies.strategy_engine import EnhancedStrategyEngine, StrategyResult
from utils.logger import get_logger
from utils.timer import Timer
from utils.validators import DataValidator

from .backtest_types import Portfolio, BacktestConfig
from .trade_manager import TradeManager
from .position_manager import PositionManager

logger = get_logger(__name__)


class BacktestEngine:
    """回测引擎"""

    def __init__(self, config: BacktestConfig):
        """初始化回测引擎

        Args:
            config: 回测配置
        """
        self.config = config
        self.strategy_engine = EnhancedStrategyEngine()
        self.validator = DataValidator()

        # 回测状态
        self.current_date: Optional[datetime] = None
        self.portfolio = Portfolio(
            cash=config.initial_capital,
            positions={},
            total_value=config.initial_capital,
            daily_returns=[],
        )

        # 管理器
        self.trade_manager = TradeManager(config, self.portfolio)
        self.position_manager = PositionManager(config, self.portfolio)

        # 历史记录
        self.portfolio_history: List[Dict[str, Any]] = []

        # 绩效指标
        self.daily_nav: pd.Series = pd.Series(dtype=float)
        self.daily_returns: pd.Series = pd.Series(dtype=float)
        self.benchmark_returns: Optional[pd.Series] = None

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_name: str,
        benchmark_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """运行回测

        Args:
            data: 历史股票数据，必须包含日期索引
            strategy_name: 策略名称
            benchmark_data: 基准数据（可选）

        Returns:
            回测结果字典
        """
        timer = Timer()
        timer.start()

        logger.info(f"开始回测: {strategy_name}")
        logger.info(f"回测期间: {self.config.start_date} 到 {self.config.end_date}")
        logger.info(f"初始资金: {self.config.initial_capital:,.2f}")

        try:
            # 数据预处理
            processed_data = self._preprocess_data(data)

            # 处理基准数据
            if benchmark_data is not None:
                self._process_benchmark_data(benchmark_data)

            # 获取交易日期列表
            trading_dates = self._get_trading_dates(processed_data)

            # 逐日回测
            for i, date in enumerate(trading_dates):
                self.current_date = date

                # 获取当日数据
                daily_data = self._get_daily_data(processed_data, date)

                if daily_data.empty:
                    continue

                # 更新持仓价格
                self.trade_manager.update_positions_prices(daily_data)

                # 检查调仓信号
                if self.position_manager.should_rebalance(date, i):
                    # 执行策略选股
                    strategy_result = self._execute_strategy(strategy_name, daily_data)

                    # 生成交易信号
                    target_positions = self.position_manager.generate_target_positions(
                        strategy_result
                    )

                    # 执行交易
                    self.trade_manager.execute_trades(
                        target_positions, daily_data, date
                    )

                # 记录每日组合状态
                self._record_daily_portfolio()

            timer.stop()

            # 生成回测报告
            results = {
                "portfolio_history": self.portfolio_history,
                "trades": self.trade_manager.trades,
                "orders": self.trade_manager.orders,
                "final_value": self.portfolio.total_value,
                "total_return": (self.portfolio.total_value - self.config.initial_capital) / self.config.initial_capital,
                "benchmark_returns": self.benchmark_returns,
            }
            
            results["execution_time"] = timer.duration
            results["total_trades"] = len(self.trade_manager.trades)

            logger.info(f"回测完成，耗时 {timer.duration:.2f} 秒")
            logger.info(f"总交易次数: {len(self.trade_manager.trades)}")

            return results

        except Exception as e:
            logger.error(f"回测失败: {e}")
            raise

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """预处理数据

        Args:
            data: 原始数据

        Returns:
            处理后的数据
        """
        logger.info("开始数据预处理...")

        # 数据验证
        required_columns = ["date", "code", "close"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必需列: {missing_columns}")

        # 日期格式转换
        if data["date"].dtype == 'object':
            data["date"] = pd.to_datetime(data["date"])

        # 过滤日期范围
        mask = (data["date"] >= self.config.start_date) & (
            data["date"] <= self.config.end_date
        )
        filtered_data = data[mask].copy()

        # 排序
        filtered_data = filtered_data.sort_values(["date", "code"])

        # 数据清洗
        filtered_data = filtered_data.dropna(subset=["close"])
        filtered_data = filtered_data[filtered_data["close"] > 0]

        logger.info(f"数据预处理完成，共 {len(filtered_data)} 条记录")
        return filtered_data

    def _process_benchmark_data(self, benchmark_data: pd.DataFrame):
        """处理基准数据

        Args:
            benchmark_data: 基准数据
        """
        if "date" not in benchmark_data.columns or "close" not in benchmark_data.columns:
            logger.warning("基准数据格式不正确，忽略基准比较")
            return

        # 日期格式转换
        if benchmark_data["date"].dtype == 'object':
            benchmark_data["date"] = pd.to_datetime(benchmark_data["date"])

        # 过滤日期范围
        mask = (benchmark_data["date"] >= self.config.start_date) & (
            benchmark_data["date"] <= self.config.end_date
        )
        filtered_benchmark = benchmark_data[mask].copy()

        # 计算收益率
        filtered_benchmark = filtered_benchmark.sort_values("date")
        filtered_benchmark["returns"] = (
            filtered_benchmark["close"].pct_change().fillna(0)
        )

        # 保存基准收益率
        self.benchmark_returns = filtered_benchmark.set_index("date")["returns"]

        logger.info(f"基准数据处理完成，共 {len(filtered_benchmark)} 个交易日")

    def _get_trading_dates(self, data: pd.DataFrame) -> List[datetime]:
        """获取交易日期列表

        Args:
            data: 数据

        Returns:
            交易日期列表
        """
        trading_dates = sorted(data["date"].unique())
        logger.info(f"交易日期范围: {trading_dates[0]} 到 {trading_dates[-1]}")
        logger.info(f"总交易日数: {len(trading_dates)}")
        return trading_dates

    def _get_daily_data(
        self, data: pd.DataFrame, date: datetime
    ) -> pd.DataFrame:
        """获取当日数据

        Args:
            data: 全量数据
            date: 日期

        Returns:
            当日数据
        """
        daily_data = data[data["date"] == date].copy()
        return daily_data

    def _execute_strategy(
        self, strategy_name: str, daily_data: pd.DataFrame
    ) -> StrategyResult:
        """执行策略选股

        Args:
            strategy_name: 策略名称
            daily_data: 当日数据

        Returns:
            策略结果
        """
        try:
            # 确保数据格式正确
            if isinstance(daily_data, pd.Series):
                daily_data = daily_data.to_frame().T

            result = self.strategy_engine.execute_strategy(
                strategy_name, daily_data, top_n=self.config.max_positions
            )

            logger.debug(f"策略选股完成，选中 {len(result.filtered_stocks)} 只股票")
            return result

        except Exception as e:
            logger.error(f"策略执行失败: {e}")
            # 返回空结果
            return StrategyResult(
                filtered_stocks=pd.DataFrame(),
                scores=None,
                rankings=None,
                signals=None,
                execution_time=0.0,
                summary={},
            )

    def _record_daily_portfolio(self):
        """记录每日组合状态"""
        portfolio_value = self.portfolio.total_value

        # 计算当日收益率
        if len(self.portfolio_history) > 0:
            prev_value = self.portfolio_history[-1]["total_value"]
            daily_return = (portfolio_value - prev_value) / prev_value
        else:
            daily_return = 0.0

        # 记录组合状态
        portfolio_record = {
            "date": self.current_date,
            "cash": self.portfolio.cash,
            "positions_value": self.portfolio.get_position_value(),
            "total_value": portfolio_value,
            "daily_return": daily_return,
            "num_positions": len(self.portfolio.positions),
            "positions": dict(self.portfolio.positions),
        }

        self.portfolio_history.append(portfolio_record)
        self.portfolio.daily_returns.append(daily_return)

        # 更新净值序列
        nav = portfolio_value / self.config.initial_capital
        self.daily_nav = pd.concat([
            self.daily_nav, 
            pd.Series([nav], index=[self.current_date])
        ])

        logger.debug(
            f"{self.current_date.strftime('%Y-%m-%d') if self.current_date else 'Unknown'}: "
            f"总价值={portfolio_value:,.2f}, "
            f"持仓数={len(self.portfolio.positions)}, "
            f"当日收益率={daily_return:.4f}"
        )
