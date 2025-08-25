"""
股票数据相关API路由 - 其他功能
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List
from webapp.models import SuccessResponse, ErrorResponse, MarketType
from utils.logger import get_logger
from webapp.services.stock_data_service import cache_financial_metrics_batch

logger = get_logger("stock_other_routes")
router = APIRouter()


@router.post("/cache-metrics")
async def cache_metrics_manually(
    limit: int = Query(None, description="缓存股票数量限制，默认为所有"),
    force_update: bool = Query(False, description="是否强制更新现有指标"),
):
    """手动缓存股票的财务指标到数据库"""
    try:
        from core.database import stock_db
        from adapters.factory import AdapterFactory

        # 如果不强制更新，则只获取没有近期指标的股票
        if not force_update:
            all_basic_data = stock_db.get_stock_basic_data(
                limit=limit, cache_hours=24 * 30, log_results=False
            )
            all_codes: List[str] = [
                str(r.get("ts_code") or r.get("code"))
                for r in all_basic_data
                if r.get("ts_code") or r.get("code")
            ]
            existing_metrics = stock_db.get_stock_metrics(
                symbols=all_codes, cache_hours=24
            )
            processed_codes = set(existing_metrics.keys())

            records_to_process = [
                r for r in all_basic_data
                if (r.get("ts_code") or r.get("code") or "").split(".")[0] not in processed_codes
            ]

            if not records_to_process:
                return SuccessResponse(message="所有股票的财务指标都已是最新", data={"processed_count": 0})

            records = records_to_process
            logger.info(f"从断点处继续，准备处理 {len(records)} 只股票的财务指标")

        else:
            records = stock_db.get_stock_basic_data(
                limit=limit, cache_hours=24 * 30, log_results=False
            )
            logger.info(f"强制更新模式，准备处理 {len(records)} 只股票的财务指标")

        if not records:
            return SuccessResponse(message="没有找到需要处理的股票数据", data={"processed_count": 0})

        factory = AdapterFactory()
        from webapp.app import api_service as _svc
        full_cfg = _svc.config_manager.get_config("application") or {}
        tushare_cfg = (full_cfg.get("data_sources", {}) or {}).get("tushare", {}) or {}
        adapter = factory.get_or_create_adapter("tushare", tushare_cfg)

        await cache_financial_metrics_batch(
            records=records, adapter=adapter, batch_size=50, concurrent_limit=10
        )

        # 重新查询以获取准确的已保存数量
        final_codes = [r.get("code") or r.get("ts_code", "").split(".")[0] for r in records]
        db_metrics = stock_db.get_stock_metrics(symbols=final_codes, cache_hours=1) if final_codes else {}
        actual_saved_count = len(db_metrics)

        return SuccessResponse(
            message=f"成功处理了 {len(records)} 只股票，缓存了 {actual_saved_count} 条财务指标",
            data={"total_processed": len(records), "cached_count": actual_saved_count},
        )
    except Exception as e:
        logger.error(f"缓存财务指标失败: {e}")
        return ErrorResponse(message=f"缓存财务指标失败: {str(e)}")


@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="搜索关键词"),
    market: MarketType = Query(MarketType.A_STOCK, description="市场类型"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
):
    """搜索股票"""
    try:
        results = [
            {
                "code": f"{query}00{i}",
                "name": f"{query}相关股票{i+1}",
                "market": market.value,
                "industry": "制造业",
                "match_type": "name" if i % 2 == 0 else "code",
            }
            for i in range(min(limit, 10))
        ]
        return SuccessResponse(message=f"搜索完成，找到 {len(results)} 个结果", data=results)
    except Exception as e:
        logger.error(f"股票搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/trending")
async def get_trending_stocks(
    market: MarketType = Query(MarketType.A_STOCK, description="市场类型"),
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
):
    """获取热门股票"""
    trending = [
        {
            "code": f"HOT{i:03d}",
            "name": f"热门股票{i+1}",
            "change_pct": (10 - i) * 0.5,
            "volume_ratio": 2.5 - i * 0.1,
            "attention_score": 95 - i * 3,
            "market": market.value,
        }
        for i in range(limit)
    ]
    return SuccessResponse(message="热门股票获取成功", data=trending)
