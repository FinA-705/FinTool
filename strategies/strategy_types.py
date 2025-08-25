"""
策略引擎数据类型

定义策略引擎使用的枚举和数据类
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from dataclasses import dataclass
from enum import Enum


class StrategyExecutionMode(Enum):
    """策略执行模式"""

    FILTER_ONLY = "filter_only"  # 仅过滤
    SCORE_ONLY = "score_only"  # 仅评分
    FULL_PIPELINE = "full_pipeline"  # 完整流水线


@dataclass
class StrategyResult:
    """策略执行结果"""

    filtered_stocks: pd.DataFrame  # 过滤后的股票
    scores: Optional[pd.Series]  # 评分结果
    rankings: Optional[pd.Series]  # 排名结果
    signals: Optional[pd.DataFrame]  # 交易信号
    execution_time: float  # 执行时间
    summary: Dict[str, Any]  # 执行摘要


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str  # 策略名称
    description: str  # 策略描述
    filters: List[str]  # 过滤条件列表
    score_formula: Optional[str]  # 评分公式
    ranking_formula: Optional[str]  # 排序公式
    signal_formulas: Optional[Dict[str, str]]  # 信号公式
    risk_formulas: Optional[Dict[str, str]]  # 风险公式
    constants: Optional[Dict[str, Any]]  # 自定义常量
    enabled: bool = True  # 是否启用
