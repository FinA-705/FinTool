"""
路由模块初始化
"""

from .stock_routes import router as stock_router
from .config_routes import router as config_router
from .backtest_routes import router as backtest_router

__all__ = ["stock_router", "config_router", "backtest_router"]
