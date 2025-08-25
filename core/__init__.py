"""
核心模块

系统核心功能组件：
- 配置管理
- 缓存管理
- 输出格式化
- 任务调度
"""

from .config_manager import CoreConfigManager, config_manager, ConfigValidationRule
from .cache_manager import CoreCacheManager, cache_manager, CacheConfig, CacheType
from .output_formatter import (
    CoreOutputFormatter,
    output_formatter,
    StockResult,
    ScreeningResult,
    StockInfo,
    ScoreDetails,
    FinancialMetrics,
    AIAnalysis,
    RiskAssessment,
    BacktestResult,
    OutputFormat,
    StockRating,
)
from .scheduler import (
    CoreScheduler,
    scheduler,
    TaskInfo,
    TaskResult,
    TaskStatus,
    TaskPriority,
)

__all__ = [
    # 配置管理
    "CoreConfigManager",
    "config_manager",
    "ConfigValidationRule",
    # 缓存管理
    "CoreCacheManager",
    "cache_manager",
    "CacheConfig",
    "CacheType",
    # 输出格式化
    "CoreOutputFormatter",
    "output_formatter",
    "StockResult",
    "ScreeningResult",
    "StockInfo",
    "ScoreDetails",
    "FinancialMetrics",
    "AIAnalysis",
    "RiskAssessment",
    "BacktestResult",
    "OutputFormat",
    "StockRating",
    # 任务调度
    "CoreScheduler",
    "scheduler",
    "TaskInfo",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
]
