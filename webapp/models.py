"""
Web应用数据模型

定义API请求和响应的数据结构
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from enum import Enum


class MarketType(str, Enum):
    """市场类型"""

    A_STOCK = "a_stock"
    US_STOCK = "us_stock"
    HK_STOCK = "hk_stock"
    ALL = "all"


class OutputFormat(str, Enum):
    """输出格式"""

    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"


class TimeFrame(str, Enum):
    """时间周期"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""

    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseResponse):
    """错误响应模型"""

    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseResponse):
    """成功响应模型"""

    success: bool = True
    data: Any


# 股票数据相关模型
class StockDataRequest(BaseModel):
    """股票数据请求"""

    symbols: Optional[List[str]] = Field(None, description="股票代码列表")
    market: MarketType = Field(MarketType.A_STOCK, description="市场类型")
    limit: int = Field(100, gt=0, le=1000, description="返回数量限制")
    fields: Optional[List[str]] = Field(None, description="指定字段")

    @validator("symbols")
    def validate_symbols(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("最多支持50个股票代码")
        return v


class StockInfo(BaseModel):
    """股票基本信息"""

    code: str
    name: Optional[str] = None
    market: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None


class StockDataResponse(SuccessResponse):
    """股票数据响应"""

    data: List[Dict[str, Any]]
    total: int
    market: str


# 策略相关模型
class StrategyFilter(BaseModel):
    """策略过滤条件"""

    field: str
    operator: str  # >, <, >=, <=, ==, !=
    value: Union[float, int, str]


class StrategyConfigRequest(BaseModel):
    """策略配置请求"""

    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    filters: List[str] = Field(default_factory=list)
    score_formula: Optional[str] = None
    ranking_formula: Optional[str] = None
    signal_formulas: Optional[Dict[str, str]] = None
    risk_formulas: Optional[Dict[str, str]] = None
    constants: Dict[str, float] = Field(default_factory=dict)


class StrategyExecuteRequest(BaseModel):
    """策略执行请求"""

    strategy_name: str
    market: MarketType = MarketType.A_STOCK
    top_n: int = Field(20, gt=0, le=100)
    include_scores: bool = False


class StrategyResult(BaseModel):
    """策略结果"""

    code: str
    name: Optional[str] = None
    score: float
    rank: int
    signals: Optional[Dict[str, Any]] = None


class StrategyExecuteResponse(SuccessResponse):
    """策略执行响应"""

    data: List[StrategyResult]
    strategy_name: str
    execution_time: float
    total_stocks: int


# 回测相关模型
class BacktestRequest(BaseModel):
    """回测请求"""

    strategy_name: str
    start_date: date
    end_date: date
    initial_capital: float = Field(1000000, gt=0)
    commission_rate: float = Field(0.0008, ge=0, le=0.01)
    slippage_rate: float = Field(0.002, ge=0, le=0.01)
    rebalance_frequency: str = Field("monthly")
    max_positions: int = Field(20, gt=0, le=50)
    benchmark: Optional[str] = None

    @validator("end_date")
    def validate_dates(cls, v, values):
        if "start_date" in values and v <= values["start_date"]:
            raise ValueError("结束日期必须晚于开始日期")
        return v


class PerformanceMetrics(BaseModel):
    """性能指标"""

    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None


class BacktestResult(BaseModel):
    """回测结果"""

    strategy_name: str
    period: str
    performance_metrics: PerformanceMetrics
    trades_count: int
    final_value: float


class BacktestResponse(SuccessResponse):
    """回测响应"""

    data: BacktestResult
    execution_time: float


# 配置相关模型
class ConfigItem(BaseModel):
    """配置项"""

    key: str
    value: Any
    type: str
    description: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""

    key: str
    value: Any
    type: Optional[str] = "auto"


class ConfigResponse(SuccessResponse):
    """配置响应"""

    data: Dict[str, Any]


# 系统信息模型
class SystemStatus(BaseModel):
    """系统状态"""

    name: str
    version: str
    uptime: str
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


class ServiceStatus(BaseModel):
    """服务状态"""

    name: str
    status: str  # healthy, warning, error
    last_check: datetime
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseResponse):
    """健康检查响应"""

    system: SystemStatus
    services: List[ServiceStatus]


# 通用分页模型
class PaginationParams(BaseModel):
    """分页参数"""

    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class PaginatedResponse(SuccessResponse):
    """分页响应"""

    data: List[Any]
    pagination: Dict[str, Any]  # total, page, size, pages


# 文件上传模型
class FileUploadResponse(SuccessResponse):
    """文件上传响应"""

    filename: str
    size: int
    content_type: str
    upload_time: datetime


# 任务相关模型
class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    """任务信息"""

    task_id: str
    status: TaskStatus
    progress: float = Field(0, ge=0, le=100)
    message: Optional[str] = None
    created_time: datetime
    updated_time: datetime
    result: Optional[Any] = None


class TaskResponse(SuccessResponse):
    """任务响应"""

    data: TaskInfo
