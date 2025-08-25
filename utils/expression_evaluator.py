"""
表达式求值工具

提供安全的数学表达式和逻辑表达式求值
支持自定义函数和变量
"""

from typing import Any, Dict, Optional, Callable
import pandas as pd
import numpy as np

from .expression_types import ExpressionError, SecurityError, ValidationError
from .safe_evaluator import SafeEvaluator
from .expression_validator import ExpressionValidator


class FormulaEvaluator:
    """公式求值器

    专门用于财务公式的求值，支持数组操作
    """

    def __init__(
        self,
        custom_functions: Optional[Dict[str, Callable]] = None,
        custom_constants: Optional[Dict[str, Any]] = None,
    ):
        """初始化公式求值器

        Args:
            custom_functions: 自定义函数
            custom_constants: 自定义常量
        """
        self.evaluator = SafeEvaluator(
            custom_functions=custom_functions,
            custom_constants=custom_constants,
            allow_assign=False,
        )

        # 添加数组处理函数
        array_functions = {
            "MEAN": lambda x: np.mean(x) if hasattr(x, "__iter__") else x,
            "STD": lambda x: np.std(x) if hasattr(x, "__iter__") else 0,
            "VAR": lambda x: np.var(x) if hasattr(x, "__iter__") else 0,
            "MEDIAN": lambda x: np.median(x) if hasattr(x, "__iter__") else x,
            "QUANTILE": lambda x, q: np.quantile(x, q) if hasattr(x, "__iter__") else x,
            "RANK": self._rank_function,
            "PERCENTILE": self._percentile_function,
            "CORR": self._correlation_function,
            "COV": self._covariance_function,
        }

        self.evaluator.functions.update(array_functions)

    def evaluate(
        self, formula: str, variables: Optional[Dict[str, Any]] = None
    ) -> Any:
        """求值公式

        Args:
            formula: 公式字符串
            variables: 变量字典

        Returns:
            求值结果
        """
        return self.evaluator.evaluate(formula, variables)

    def _rank_function(self, values, ascending=True):
        """排名函数"""
        if isinstance(values, (pd.Series, np.ndarray)):
            if isinstance(values, np.ndarray):
                values = pd.Series(values)
            return values.rank(ascending=ascending).values
        else:
            return 1

    def _percentile_function(self, values, q):
        """百分位数函数"""
        if hasattr(values, "__iter__"):
            return np.percentile(values, q * 100)
        else:
            return values

    def _correlation_function(self, x, y):
        """相关系数函数"""
        if hasattr(x, "__iter__") and hasattr(y, "__iter__"):
            return np.corrcoef(x, y)[0, 1]
        else:
            return 1.0

    def _covariance_function(self, x, y):
        """协方差函数"""
        if hasattr(x, "__iter__") and hasattr(y, "__iter__"):
            return np.cov(x, y)[0, 1]
        else:
            return 0.0


# 向后兼容的导入
__all__ = [
    "ExpressionError",
    "SecurityError", 
    "ValidationError",
    "SafeEvaluator",
    "FormulaEvaluator",
    "ExpressionValidator",
]
