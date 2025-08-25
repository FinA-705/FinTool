"""
股票数据相关API路由
"""
from fastapi import APIRouter
from .stock import (
    data_routes,
    info_routes,
    strategy_routes,
    other_routes,
    health_routes,
)

router = APIRouter()

# 包含各个子路由
router.include_router(data_routes.router, prefix="/stocks", tags=["Stock Data"])
router.include_router(info_routes.router, prefix="/stocks", tags=["Stock Info"])
router.include_router(
    strategy_routes.router, prefix="/stocks", tags=["Stock Strategy & Market"]
)
router.include_router(other_routes.router, prefix="/stocks", tags=["Stock Other"])
router.include_router(health_routes.router, prefix="/stocks", tags=["Stock Health"])
