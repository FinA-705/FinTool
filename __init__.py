"""
FinancialAgent - 智能选股系统

一个基于施洛斯价值投资策略的跨市场智能选股系统
"""

__version__ = "0.1.0"
__author__ = "FinancialAgent Team"
__email__ = "team@financialagent.com"
__description__ = "智能选股系统 - 跨市场价值投资策略分析工具"

# 导入核心组件
from .core.config_manager import ConfigManager
from .core.cache_manager import CacheManager
from .core.output_formatter import OutputFormatter

# 导入适配器
from .adapters.base import BaseAdapter

# 导入策略
from .strategies.schloss_strategy import SchlossStrategy

# 导入评分器
from .scorer.basic_scorer import BasicScorer
from .scorer.ai_scorer import AIScorer
from .scorer.risk_assessor import RiskAssessor

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "description": __description__,
}

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",
    "__description__",
    "VERSION_INFO",
    # 核心组件
    "ConfigManager",
    "CacheManager",
    "OutputFormatter",
    # 适配器
    "BaseAdapter",
    # 策略
    "SchlossStrategy",
    # 评分器
    "BasicScorer",
    "AIScorer",
    "RiskAssessor",
]
