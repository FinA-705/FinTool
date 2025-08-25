"""
风险评估相关的数据模型和枚举
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class RiskMetric(Enum):
    """风险指标枚举"""
    VOLATILITY = "volatility"
    MAX_DRAWDOWN = "max_drawdown"
    VAR = "value_at_risk"
    CVAR = "conditional_var"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    BETA = "beta"
    ALPHA = "alpha"


class RiskLevel(Enum):
    """风险等级枚举"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class RiskConfig:
    """风险评估配置"""
    confidence_level: float = 0.95
    risk_free_rate: float = 0.03
    market_index: str = "000300.SH"
    lookback_days: int = 252
    min_periods: int = 30


@dataclass
class RiskMetrics:
    """风险指标结果"""
    volatility: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: Optional[float] = None
    alpha: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "volatility": self.volatility,
            "max_drawdown": self.max_drawdown,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "beta": self.beta,
            "alpha": self.alpha,
        }


@dataclass
class RiskAssessment:
    """风险评估结果"""
    symbol: str
    risk_level: RiskLevel
    risk_score: float
    metrics: RiskMetrics
    warnings: List[str]
    recommendations: List[str]
    assessment_date: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "metrics": self.metrics.to_dict(),
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "assessment_date": self.assessment_date.isoformat(),
        }
