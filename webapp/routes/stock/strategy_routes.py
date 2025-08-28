"""
股票数据相关API路由 - 策略与市场
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from webapp.models import (
    StrategyExecuteRequest,
    StrategyExecuteResponse,
    SuccessResponse,
)
from utils.logger import get_logger
from datetime import datetime

logger = get_logger("stock_strategy_routes")
router = APIRouter()


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service

    return api_service


@router.post("/screen", response_model=StrategyExecuteResponse)
async def screen_stocks(
    request: StrategyExecuteRequest,
    api_service=Depends(get_api_service),
):
    """执行选股策略"""
    try:
        logger.info(f"执行选股策略: {request.strategy_name}")
        start_time = datetime.now()
        await asyncio.sleep(0.1)  # 模拟计算时间

        results = []
        for i in range(request.top_n):
            result = {
                "code": f"00000{i:02d}",
                "name": f"优质股{i+1}",
                "score": 90 - i * 2,
                "rank": i + 1,
            }
            if request.include_scores:
                result["signals"] = {
                    "buy_signal": i < 5,
                    "risk_level": "low" if i < 10 else "medium",
                    "confidence": 0.8 - i * 0.02,
                }
            results.append(result)

        execution_time = (datetime.now() - start_time).total_seconds()
        return StrategyExecuteResponse(
            message="策略执行成功",
            data=results,
            strategy_name=request.strategy_name,
            execution_time=execution_time,
            total_stocks=1000,
        )
    except Exception as e:
        logger.error(f"策略执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"策略执行失败: {str(e)}")


@router.get("/markets")
async def get_supported_markets():
    """获取支持的市场列表"""
    markets = [
        {
            "code": "a_stock",
            "name": "A股市场",
            "description": "中国沪深交易所",
            "timezone": "Asia/Shanghai",
            "trading_hours": "09:30-15:00",
            "currency": "CNY",
        },
        {
            "code": "us_stock",
            "name": "美股市场",
            "description": "美国纳斯达克、纽交所",
            "timezone": "America/New_York",
            "trading_hours": "09:30-16:00",
            "currency": "USD",
        },
        {
            "code": "hk_stock",
            "name": "港股市场",
            "description": "香港交易所",
            "timezone": "Asia/Hong_Kong",
            "trading_hours": "09:30-16:00",
            "currency": "HKD",
        },
    ]
    return SuccessResponse(message="市场信息获取成功", data=markets)


@router.get("/industries")
async def get_industries():
    """获取行业分类"""
    industries = [
        {"code": "manufacturing", "name": "制造业", "count": 1500},
        {"code": "finance", "name": "金融业", "count": 200},
        {"code": "technology", "name": "信息技术", "count": 800},
    ]
    return SuccessResponse(message="行业信息获取成功", data=industries)
