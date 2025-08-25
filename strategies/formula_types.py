"""
策略公式类型定义

定义公式解析器使用的枚举和数据类
"""

from typing import Any, Dict, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class FormulaType(Enum):
    """公式类型枚举"""

    FILTER = "filter"  # 过滤条件
    SCORE = "score"  # 评分公式
    RANKING = "ranking"  # 排序公式
    SIGNAL = "signal"  # 交易信号
    RISK = "risk"  # 风险指标
    TECHNICAL = "technical"  # 技术指标


class OperatorType(Enum):
    """操作符类型"""

    COMPARISON = "comparison"  # 比较操作 (>, <, ==, !=, >=, <=)
    LOGICAL = "logical"  # 逻辑操作 (and, or, not)
    ARITHMETIC = "arithmetic"  # 算术操作 (+, -, *, /, %, **)
    MEMBERSHIP = "membership"  # 成员操作 (in, not in)
    FUNCTION = "function"  # 函数调用


@dataclass
class FormulaComponent:
    """公式组件"""

    type: str  # 组件类型
    value: Any  # 组件值
    position: Tuple[int, int]  # 在公式中的位置
    dependencies: List[str]  # 依赖的字段


@dataclass
class ParsedFormula:
    """解析后的公式"""

    original: str  # 原始公式
    components: List[FormulaComponent]  # 公式组件
    variables: Set[str]  # 使用的变量
    functions: Set[str]  # 使用的函数
    operators: Set[str]  # 使用的操作符
    formula_type: FormulaType  # 公式类型
    is_valid: bool  # 是否有效
    error_message: Optional[str] = None
