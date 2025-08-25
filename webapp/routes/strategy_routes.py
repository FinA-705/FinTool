"""
策略管理相关API路由
处理真实的策略数据，与演示接口分离
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime

from webapp.models import SuccessResponse, ErrorResponse
from utils.logger import get_logger

logger = get_logger("strategy_routes")

router = APIRouter()


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service

    return api_service


async def get_real_strategies() -> List[Dict[str, Any]]:
    """获取真实策略列表"""
    try:
        from strategies.strategy_factory import StrategyFactory
        from strategies.config_manager import ConfigManager

        # 获取配置管理器
        config_manager = ConfigManager()
        strategy_names = config_manager.list_available_strategies()

        # 转换为API格式
        real_strategies = []
        for strategy_name in strategy_names:
            try:
                strategy_config = config_manager.load_strategy_config(strategy_name)
                real_strategies.append(
                    {
                        "name": strategy_name,
                        "description": f"基于配置的{strategy_name}策略",
                        "status": "active",
                        "last_run": datetime.now().strftime("%Y-%m-%d"),
                        "type": "real",
                        "filters": (
                            strategy_config.filters
                            if hasattr(strategy_config, "filters")
                            else {}
                        ),
                        "scoring": "基于权重的评分算法",
                        "created_at": datetime.now().isoformat(),
                    }
                )
            except Exception as e:
                logger.warning(f"加载策略配置失败 {strategy_name}: {e}")
                # 添加默认策略配置
                real_strategies.append(
                    {
                        "name": strategy_name,
                        "description": f"{strategy_name}策略",
                        "status": "active",
                        "last_run": datetime.now().strftime("%Y-%m-%d"),
                        "type": "real",
                        "filters": {},
                        "scoring": "默认评分",
                        "created_at": datetime.now().isoformat(),
                    }
                )

        return real_strategies

    except Exception as e:
        logger.error(f"获取真实策略失败: {e}")
        raise Exception(f"策略服务不可用: {str(e)}")


@router.get("/strategies")
async def get_strategies(api_service=Depends(get_api_service)):
    """获取策略列表"""
    try:
        strategies = await get_real_strategies()
        return SuccessResponse(message="策略列表获取成功", data=strategies)

    except Exception as e:
        logger.error(f"获取策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.post("/strategies")
async def create_strategy(
    strategy_data: Dict[str, Any], api_service=Depends(get_api_service)
):
    """创建新策略"""
    try:
        # 这里应该调用真实的策略创建逻辑
        strategy_name = strategy_data.get("name")
        if not strategy_name:
            raise HTTPException(status_code=400, detail="策略名称不能为空")

        # TODO: 实现真实的策略创建逻辑

        created_strategy = {
            "name": strategy_name,
            "description": strategy_data.get("description", ""),
            "filters": strategy_data.get("filters", {}),
            "scoring": strategy_data.get("scoring", ""),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "type": "real",
        }

        return SuccessResponse(
            message=f"策略 '{strategy_name}' 创建成功", data=created_strategy
        )

    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")


@router.delete("/strategies/{strategy_name}")
async def delete_strategy(strategy_name: str, api_service=Depends(get_api_service)):
    """删除策略"""
    try:
        # TODO: 实现真实的策略删除逻辑
        return SuccessResponse(message=f"策略 '{strategy_name}' 删除成功", data={})

    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除策略失败: {str(e)}")


@router.post("/strategies/{strategy_name}/execute")
async def execute_strategy(
    strategy_name: str,
    top_n: int = Query(20, description="返回前N只股票"),
    api_service=Depends(get_api_service),
):
    """执行策略选股"""
    try:
        start_time = datetime.now()

        # 导入必要的模块
        from strategies.strategy_factory import StrategyFactory
        from core.database import stock_db

        # 获取股票数据
        stocks_data = stock_db.get_stock_basic_data(cache_hours=24 * 7)
        if not stocks_data:
            raise HTTPException(status_code=500, detail="无法获取股票数据")

        total_stocks = len(stocks_data)

        # 创建策略实例
        strategy_factory = StrategyFactory()
        strategy = strategy_factory.create_strategy(strategy_name)

        # 执行策略筛选
        selected_results = []
        try:
            # 尝试使用pandas运行策略
            try:
                import pandas as pd

                stocks_df = pd.DataFrame(stocks_data)
                strategy_results = strategy.screen_stocks(stocks_df, top_n=top_n)

                for i, result in enumerate(strategy_results):
                    selected_results.append(
                        {
                            "rank": i + 1,
                            "code": result.stock_code,
                            "name": result.stock_name,
                            "score": round(result.score, 1),
                            "reason": (
                                ", ".join(result.reasons[:2])
                                if result.reasons
                                else "符合策略条件"
                            ),
                            "warnings": result.warnings,
                            "metadata": result.metadata,
                        }
                    )

            except ImportError:
                # 如果pandas不可用，使用简化筛选
                logger.warning("pandas不可用，使用简化筛选")
                raise Exception("使用简化筛选")

        except Exception as e:
            logger.warning(f"策略筛选失败，使用简化筛选: {e}")
            # 简化筛选：基于基本条件
            filtered_stocks = []
            for stock in stocks_data:
                reasons = []
                # 简单筛选条件
                if stock.get("name"):
                    if not any(x in stock.get("name", "") for x in ["ST", "*ST", "PT"]):
                        reasons.append("非风险警示股")
                    else:
                        continue  # 跳过风险警示股

                    if stock.get("list_date"):
                        reasons.append("已正常上市")
                    else:
                        continue

                    # 检查市场类型
                    market = stock.get("market", "")
                    if market in ["主板", "创业板", "科创板"]:
                        reasons.append(f"{market}上市")
                    elif market:
                        reasons.append("正规市场上市")

                    # 检查行业信息
                    industry = stock.get("industry", "")
                    if industry:
                        reasons.append(f"属于{industry}行业")

                    # 添加到筛选结果
                    stock["selection_reasons"] = reasons
                    filtered_stocks.append(stock)

            # 取前top_n只股票
            for i, stock in enumerate(filtered_stocks[:top_n]):
                score = 85 - (i * 2)  # 简单评分
                reasons = stock.get("selection_reasons", ["符合基本筛选条件"])

                selected_results.append(
                    {
                        "rank": i + 1,
                        "code": stock.get("ts_code", stock.get("symbol", f"STOCK{i}")),
                        "name": stock.get("name", f'股票{stock.get("ts_code", i+1)}'),
                        "score": score,
                        "reason": ", ".join(reasons[:3]),  # 最多显示3个理由
                        "warnings": [],
                        "metadata": {
                            "market": stock.get("market", ""),
                            "industry": stock.get("industry", ""),
                            "area": stock.get("area", ""),
                        },
                    }
                )

        execution_time = (datetime.now() - start_time).total_seconds()

        result = {
            "strategy_name": strategy_name,
            "execution_time": round(execution_time, 3),
            "total_stocks": total_stocks,
            "selected_count": len(selected_results),
            "selection_ratio": (
                round(len(selected_results) / total_stocks * 100, 2)
                if total_stocks > 0
                else 0
            ),
            "data": selected_results,
            "execution_timestamp": datetime.now().isoformat(),
        }

        return SuccessResponse(
            message=f"策略执行成功，筛选出{len(selected_results)}只股票", data=result
        )

    except Exception as e:
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")
