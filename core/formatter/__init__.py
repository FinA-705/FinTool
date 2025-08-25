"""
输出格式化器模块
"""

from .models import *
from .helpers import generate_recommendation, generate_summary
from .exporters import DataExporter
from .main import CoreOutputFormatter

# 全局输出格式化器实例
output_formatter = CoreOutputFormatter()

__all__ = [
    # Models
    "OutputFormat",
    "StockRating",
    "ScoreDetails",
    "StockInfo",
    "FinancialMetrics",
    "AIAnalysis",
    "RiskAssessment",
    "BacktestResult",
    "StockResult",
    "StrategyConfig",
    "ExecutionInfo",
    "ScreeningResult",
    # Helpers
    "generate_recommendation",
    "generate_summary",
    # Exporter
    "DataExporter",
    # Main class
    "CoreOutputFormatter",
    # Global instance
    "output_formatter",
]
