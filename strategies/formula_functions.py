"""
策略公式自定义函数实现

包含公式解析器使用的所有自定义函数
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, Union, Callable
from datetime import datetime


class FormulaFunctions:
    """自定义函数实现类"""

    @staticmethod
    def rank_function(
        values: Union[pd.Series, np.ndarray], ascending: bool = True
    ) -> Any:
        """排名函数"""
        if isinstance(values, pd.Series):
            return np.array(values.rank(ascending=ascending))
        else:
            series = pd.Series(values)
            return np.array(series.rank(ascending=ascending))

    @staticmethod
    def percentile_function(values: Union[pd.Series, np.ndarray], q: float) -> Any:
        """百分位数函数"""
        return float(np.percentile(values, q * 100))

    @staticmethod
    def if_function(
        condition: Union[bool, np.ndarray], true_value: Any, false_value: Any
    ) -> Any:
        """条件函数"""
        return np.where(condition, true_value, false_value)

    @staticmethod
    def ifs_function(*args) -> Any:
        """多条件函数"""
        if len(args) % 2 == 0:
            raise ValueError("IFS函数参数数量必须为奇数")

        result = args[-1]  # 默认值

        for i in range(0, len(args) - 1, 2):
            condition = args[i]
            value = args[i + 1]
            result = np.where(condition, value, result)

        return result

    @staticmethod
    def isnull_function(values: Union[pd.Series, np.ndarray]) -> Any:
        """空值检查函数"""
        if isinstance(values, pd.Series):
            return np.array(values.isnull())
        else:
            return pd.isnull(values)

    @staticmethod
    def days_since_function(date_col: Union[pd.Series, np.ndarray]) -> Any:
        """距今天数函数"""
        if isinstance(date_col, pd.Series):
            dates = pd.to_datetime(date_col)
        else:
            dates = pd.to_datetime(pd.Series(date_col))

        today = pd.Timestamp.now()
        delta = today - dates
        return np.array(delta.dt.days)

    @staticmethod
    def market_phase_function(
        prices: Union[pd.Series, np.ndarray], window: int = 252
    ) -> str:
        """市场阶段判断"""
        if len(prices) < window:
            return "insufficient_data"

        recent_return = (prices[-1] - prices[-window]) / prices[-window]

        if recent_return > 0.2:
            return "bull"
        elif recent_return < -0.2:
            return "bear"
        else:
            return "sideways"

    @staticmethod
    def sector_rank_function(
        values: Union[pd.Series, np.ndarray],
        sectors: Union[pd.Series, np.ndarray],
    ) -> Any:
        """行业内排名"""
        df = pd.DataFrame({"value": values, "sector": sectors})
        return np.array(df.groupby("sector")["value"].rank(ascending=False))

    @staticmethod
    def z_score_function(values: Union[pd.Series, np.ndarray]) -> Any:
        """Z-Score标准化"""
        values = np.array(values)
        return (values - np.mean(values)) / np.std(values)

    @staticmethod
    def bollinger_bands(
        prices: Union[pd.Series, np.ndarray], window: int = 20, std_dev: float = 2
    ) -> Dict[str, Any]:
        """布林带计算"""
        prices = pd.Series(prices) if not isinstance(prices, pd.Series) else prices

        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        return {
            "upper": np.array(upper),
            "middle": np.array(sma),
            "lower": np.array(lower),
            "width": np.array(upper - lower),
        }

    @staticmethod
    def momentum_function(
        prices: Union[pd.Series, np.ndarray], period: int = 10
    ) -> Any:
        """动量指标"""
        prices = pd.Series(prices) if not isinstance(prices, pd.Series) else prices
        return np.array(prices / prices.shift(period) - 1)


def get_custom_functions() -> Dict[str, Callable]:
    """获取所有自定义函数的字典"""
    functions = FormulaFunctions()

    return {
        "RANK": functions.rank_function,
        "PERCENTILE": functions.percentile_function,
        "IF": functions.if_function,
        "IFS": functions.ifs_function,
        "ISNULL": functions.isnull_function,
        "DAYS_SINCE": functions.days_since_function,
        "MARKET_PHASE": functions.market_phase_function,
        "SECTOR_RANK": functions.sector_rank_function,
        "Z_SCORE": functions.z_score_function,
        "BOLLINGER": functions.bollinger_bands,
        "MOMENTUM": functions.momentum_function,
    }
