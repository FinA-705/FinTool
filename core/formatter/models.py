"""
输出格式化器的数据模型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class OutputFormat(Enum):
    """输出格式枚举"""

    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"


class StockRating(Enum):
    """股票评级"""

    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


@dataclass
class ScoreDetails:
    """评分详情"""

    total_score: float
    value_score: float
    quality_score: float
    safety_score: float
    growth_score: float
    ai_score: Optional[float] = None
    risk_score: Optional[float] = None


@dataclass
class StockInfo:
    """股票基本信息"""

    symbol: str
    name: str
    market: str
    sector: str
    industry: str
    market_cap: Optional[float] = None
    currency: str = "CNY"


@dataclass
class FinancialMetrics:
    """财务指标"""

    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None


@dataclass
class AIAnalysis:
    """AI分析结果"""

    rating: StockRating
    confidence: float
    reasoning: str
    key_strengths: List[str]
    key_risks: List[str]
    price_target: Optional[float] = None
    investment_horizon: str = "中长期"


@dataclass
class RiskAssessment:
    """风险评估"""

    volatility: float
    max_drawdown: float
    beta: Optional[float] = None
    risk_level: str = "中等"
    risk_factors: Optional[List[str]] = None


@dataclass
class BacktestResult:
    """回测结果"""

    period: str
    total_return: float
    annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float


@dataclass
class StockResult:
    """单个股票完整结果"""

    stock_info: StockInfo
    scores: ScoreDetails
    financial_metrics: FinancialMetrics
    ai_analysis: Optional[AIAnalysis] = None
    risk_assessment: Optional[RiskAssessment] = None
    backtest_result: Optional[BacktestResult] = None
    current_price: Optional[float] = None
    recommendation: str = "待分析"
    last_updated: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


@dataclass
class StrategyConfig:
    """策略配置信息"""

    strategy_name: str
    version: str
    parameters: Dict[str, Any]
    description: str


@dataclass
class ExecutionInfo:
    """执行信息"""

    execution_id: str
    start_time: str
    end_time: str
    duration_seconds: float
    total_stocks_analyzed: int
    successful_analyses: int
    failed_analyses: int
    data_sources: List[str]


@dataclass
class ScreeningResult:
    """筛选结果主体"""

    strategy_config: StrategyConfig
    execution_info: ExecutionInfo
    stocks: List[StockResult]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]
