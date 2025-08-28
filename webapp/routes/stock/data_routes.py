"""
股票数据相关API路由 - 数据获取
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from webapp.models import StockDataResponse, MarketType
from utils.logger import get_logger
from webapp.services.stock_data_service import get_all_stock_data_with_cache

logger = get_logger("stock_data_routes")
router = APIRouter()


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service

    return api_service


@router.get("/data", response_model=StockDataResponse)
async def get_stock_data(
    symbols: Optional[str] = Query(None, description="股票代码，逗号分隔"),
    market: MarketType = Query(MarketType.A_STOCK, description="市场类型"),
    limit: Optional[int] = Query(None, ge=1, description="返回数量限制,不传则返回所有"),
    fields: Optional[str] = Query(None, description="指定字段，逗号分隔"),
    api_service=Depends(get_api_service),
):
    """获取股票数据"""
    try:
        symbol_list = symbols.split(",") if symbols else None
        field_list = fields.split(",") if fields else None
        # 更新缓存键以反映可能没有限制
        cache_key_limit = limit if limit is not None else "all"
        cache_key = f"stock_data_{market.value}_{symbols}_{cache_key_limit}"

        cached_data = api_service.get_cached_data(cache_key)
        if cached_data:
            logger.info(f"返回缓存数据: {cache_key}")
            cache_result = cached_data["data"]
            # 应用limit（如果提供）
            if limit and len(cache_result) > limit:
                cache_result = cache_result[:limit]
            return StockDataResponse(
                message="数据获取成功（缓存）",
                data=cache_result,
                total=len(cache_result),
                market=market.value,
            )

        logger.info(
            f"获取股票数据: market={market.value}, symbols={symbol_list}, limit={limit}"
        )
        raw_data = await get_all_stock_data_with_cache(market.value, symbol_list)
        data_source = "Tushare"

        codes = [
            item.get("code") or item.get("ts_code", "").split(".")[0]
            for item in raw_data
            if isinstance(item, dict)
        ]

        from core.database import stock_db

        db_metrics = (
            stock_db.get_stock_metrics(symbols=codes, cache_hours=24) if codes else {}
        )

        enriched_data = []
        for item in raw_data:
            if isinstance(item, dict):
                code = item.get("code") or item.get("ts_code", "").split(".")[0]
                metrics = db_metrics.get(code, {})
                enriched_item = {
                    "code": code,
                    "name": item.get("name", ""),
                    "market": item.get("market", ""),
                    "area": item.get("area", ""),
                    "industry": item.get("industry", ""),
                    "price": metrics.get("current_price"),
                    "change": metrics.get("change_pct"),
                    "volume": metrics.get("volume"),
                    "market_cap": metrics.get("market_cap"),
                    "pe": metrics.get("pe"),
                    "pb": metrics.get("pb"),
                    "roe": metrics.get("roe"),
                    "roa": metrics.get("roa"),
                    "debt_ratio": metrics.get("debt_ratio"),
                    "eps": metrics.get("eps"),
                    **{
                        k: v
                        for k, v in item.items()
                        if k not in ["code", "name", "market", "area", "industry"]
                    },
                }
                enriched_data.append(enriched_item)

        raw_data = enriched_data
        if limit and len(raw_data) > limit:
            raw_data = raw_data[:limit]

        if field_list:
            raw_data = [
                {field: item.get(field) for field in field_list if field in item}
                for item in raw_data
            ]

        cache_data = {
            "data": raw_data,
            "total": len(raw_data),
            "data_source": data_source,
        }
        api_service.set_cached_data(cache_key, cache_data)

        return StockDataResponse(
            message=f"数据获取成功（{data_source}）",
            data=raw_data,
            total=len(raw_data),
            market=market.value,
        )
    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")
