"""
股票数据相关API路由
统一管理所有股票相关的API端点
"""

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from webapp.models import StockDataResponse, MarketType, SuccessResponse
from utils.logger import get_logger
from webapp.services.stock_data_service import get_all_stock_data_with_cache

logger = get_logger("stock_routes")
router = APIRouter()


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service

    return api_service


def _safe_float(x):
    """安全的浮点数转换"""
    try:
        if x in (None, ""):
            return None
        return float(x)
    except Exception:
        return None


# ========== 数据获取相关路由 ==========


@router.get("/stocks/data", response_model=StockDataResponse)
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
        cache_key_limit = limit if limit is not None else "all"
        cache_key = f"stock_data_{market.value}_{symbols}_{cache_key_limit}"

        cached_data = api_service.get_cached_data(cache_key)
        if cached_data:
            logger.info(f"返回缓存数据: {cache_key}")
            cache_result = cached_data["data"]
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

        raw_data = await get_all_stock_data_with_cache(
            market=market.value,
            symbol_list=symbol_list,
        )

        # 合并财务指标
        codes = [
            (item.get("code") or item.get("ts_code", "").split(".")[0])
            for item in (raw_data or [])
            if isinstance(item, dict)
        ]
        from core.database import stock_db

        db_metrics = (
            stock_db.get_stock_metrics(symbols=codes, cache_hours=24) if codes else {}
        )

        enriched_data = []
        for item in raw_data or []:
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

        data = enriched_data

        # 应用limit过滤
        if limit and data and len(data) > limit:
            data = data[:limit]

        total_count = len(data) if data else 0
        api_service.set_cached_data(
            cache_key, {"data": data, "timestamp": datetime.now().isoformat()}, ttl=3600
        )

        return StockDataResponse(
            message="数据获取成功",
            data=data,
            total=total_count,
            market=market.value,
        )

    except Exception as e:
        logger.error(f"获取股票数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")


# ========== 股票详细信息相关路由 ==========


@router.get("/stocks/info/{stock_code}")
async def get_stock_info(stock_code: str, api_service=Depends(get_api_service)):
    """获取单只股票详细信息"""
    try:
        pure_code = stock_code.split(".")[0]
        cache_key = f"stock_info_{pure_code}"
        cached = api_service.get_cached_data(cache_key)
        if cached:
            # 若缓存中缺少关键指标，则忽略缓存并刷新
            fm = cached.get("financial_metrics") or {}
            probe = fm or cached  # 兼容旧结构（顶层包含指标）
            has_core = any(
                probe.get(k) is not None
                for k in ["current_price", "pe", "pb", "roe", "market_cap"]
            )
            if has_core:
                return SuccessResponse(message="股票信息获取成功（缓存）", data=cached)

        from core.database import stock_db

        records = stock_db.get_stock_basic_data(symbols=[pure_code], cache_hours=24 * 7)
        info = records[0] if records else {}

        metrics = await _fetch_and_cache_metrics(info, pure_code, api_service)

        stock_info = {
            "code": pure_code,
            "name": info.get("name") or info.get("fullname") or pure_code,
            "industry": info.get("industry", ""),
            "area": info.get("area", ""),
            "market": info.get("market", ""),
            "listing_date": str(info.get("list_date", "")).split(" ")[0],
            # 顶层继续保留常用指标以兼容旧前端逻辑
            "pe": metrics.get("pe"),
            "pb": metrics.get("pb"),
            "roe": metrics.get("roe"),
            "market_cap": metrics.get("market_cap"),
            "current_price": metrics.get("current_price"),
            "change_pct": metrics.get("change_pct"),
            # 同时提供嵌套字段，便于前端统一读取
            "financial_metrics": metrics,
        }

        api_service.set_cached_data(cache_key, stock_info, ttl=3600)
        return SuccessResponse(message="股票信息获取成功", data=stock_info)

    except Exception as e:
        logger.error(f"获取股票信息失败: {stock_code}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


async def _fetch_and_cache_metrics(info, pure_code, api_service):
    """获取和缓存股票指标数据"""
    from core.database import stock_db

    # 优先读取内存缓存（由批量缓存任务写入，TTL 30 分钟）
    cache_key = f"stock_metrics_{pure_code}"
    cached = api_service.get_cached_data(cache_key)
    if cached:
        return cached

    try:
        # 放宽时间窗口，避免详情页因1小时窗口而查不到已入库指标
        m = stock_db.get_stock_metrics(symbols=[pure_code], cache_hours=24)
        data = m.get(pure_code, {}) if m else {}
        if data:
            api_service.set_cached_data(cache_key, data, ttl=1800)
        return data
    except Exception as e:
        logger.warning(f"获取股票指标失败: {pure_code}, 错误: {str(e)}")
        return {}


@router.get("/stocks/basic/{stock_code}")
async def get_stock_basic_info(stock_code: str, api_service=Depends(get_api_service)):
    """获取股票基本信息"""
    try:
        pure_code = stock_code.split(".")[0]
        cache_key = f"stock_basic_{pure_code}"
        cached = api_service.get_cached_data(cache_key)
        if cached:
            return SuccessResponse(message="基本信息获取成功（缓存）", data=cached)

        from core.database import stock_db

        records = stock_db.get_stock_basic_data(symbols=[pure_code], cache_hours=24 * 7)

        if not records:
            raise HTTPException(status_code=404, detail="未找到股票信息")

        info = records[0]
        basic_info = {
            "code": pure_code,
            "name": info.get("name", ""),
            "fullname": info.get("fullname", ""),
            "industry": info.get("industry", ""),
            "area": info.get("area", ""),
            "market": info.get("market", ""),
            "exchange": info.get("exchange", ""),
            "listing_date": str(info.get("list_date", "")).split(" ")[0],
            "list_status": info.get("list_status", ""),
        }

        api_service.set_cached_data(cache_key, basic_info, ttl=24 * 3600)
        return SuccessResponse(message="基本信息获取成功", data=basic_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票基本信息失败: {stock_code}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取基本信息失败: {str(e)}")


# ========== 策略和市场相关路由 ==========


@router.get("/stocks/strategy/{strategy_name}/data")
async def get_strategy_data(
    strategy_name: str,
    limit: Optional[int] = Query(10, description="返回数量限制"),
    api_service=Depends(get_api_service),
):
    """获取策略筛选后的股票数据"""
    try:
        cache_key = f"strategy_data_{strategy_name}_{limit}"
        cached = api_service.get_cached_data(cache_key)
        if cached:
            return SuccessResponse(message=f"策略数据获取成功（缓存）", data=cached)

        from strategies.strategy_engine import EnhancedStrategyEngine
        import pandas as pd

        engine = EnhancedStrategyEngine()
        strategy_info = engine.get_strategy_info(strategy_name)

        if not strategy_info:
            raise HTTPException(
                status_code=404, detail=f"策略 '{strategy_name}' 未找到"
            )

        from core.database import stock_db

        stocks = stock_db.get_stock_basic_data(cache_hours=24)
        if not stocks:
            raise HTTPException(status_code=404, detail="没有可用的股票数据")

        df = pd.DataFrame(stocks)
        result = engine.execute_strategy(strategy_name, df)

        # 从策略结果中提取数据
        filtered_df = result.filtered_stocks
        if limit and len(filtered_df) > limit:
            filtered_df = filtered_df.head(limit)

        data = filtered_df.to_dict("records")
        api_service.set_cached_data(cache_key, data, ttl=1800)

        return SuccessResponse(
            message=f"策略 '{strategy_name}' 数据获取成功", data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略数据失败: {strategy_name}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取策略数据失败: {str(e)}")


@router.get("/stocks/market/summary")
async def get_market_summary(api_service=Depends(get_api_service)):
    """获取市场概览数据"""
    try:
        cache_key = "market_summary"
        cached = api_service.get_cached_data(cache_key)
        if cached:
            return SuccessResponse(message="市场概览获取成功（缓存）", data=cached)

        from core.database import stock_db

        stocks = stock_db.get_stock_basic_data(cache_hours=24)
        if not stocks:
            raise HTTPException(status_code=404, detail="没有可用的股票数据")

        total_stocks = len(stocks)

        markets = {}
        for stock in stocks:
            market = stock.get("market", "未知")
            if market not in markets:
                markets[market] = 0
            markets[market] += 1

        industries = {}
        for stock in stocks:
            industry = stock.get("industry", "未知")
            if industry not in industries:
                industries[industry] = 0
            industries[industry] += 1

        summary = {
            "total_stocks": total_stocks,
            "markets": markets,
            "top_industries": dict(
                sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "last_updated": datetime.now().isoformat(),
        }

        api_service.set_cached_data(cache_key, summary, ttl=3600)
        return SuccessResponse(message="市场概览获取成功", data=summary)

    except Exception as e:
        logger.error(f"获取市场概览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


# ========== 健康检查和其他路由 ==========


@router.get("/stocks/health")
async def health_check():
    """股票服务健康检查"""
    try:
        from core.database import stock_db

        # 测试数据库连接
        test_data = stock_db.get_stock_basic_data(limit=1, cache_hours=1)
        db_status = "OK" if test_data else "NO_DATA"

        return SuccessResponse(
            message="股票服务正常",
            data={
                "status": "healthy",
                "database": db_status,
                "timestamp": datetime.now().isoformat(),
                "service": "stock_api",
            },
        )
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail=f"服务不可用: {str(e)}")


# ========== 财务指标运维相关路由 ==========


class RefetchRequest(BaseModel):
    codes: Optional[List[str]] = None


@router.get("/stocks/metrics/bad-codes")
async def get_metrics_bad_codes(api_service=Depends(get_api_service)):
    """获取已缓存的疑似问题股票代码列表"""
    try:
        codes = api_service.get_cached_data("metrics_bad_codes") or []
        if not isinstance(codes, list):
            codes = []
        if not codes:
            try:
                from core.database import stock_db
                db_metrics = stock_db.get_stock_metrics(cache_hours=24) or {}
                from webapp.services.stock_data_service import (
                    is_metrics_anomalous as _is_bad,
                )
                recomputed = []
                for symbol, m in db_metrics.items():
                    if not m or not isinstance(m, dict):
                        recomputed.append(symbol)
                        continue
                    if _is_bad(m):
                        recomputed.append(symbol)
                def to_ts_code(code: str) -> str:
                    if not code:
                        return code
                    code = code.strip()
                    if "." in code:
                        return code
                    if code.startswith(("0", "3")):
                        return f"{code}.SZ"
                    if code.startswith("6"):
                        return f"{code}.SH"
                    return code
                codes = sorted({to_ts_code(c) for c in recomputed if c})
                api_service.set_cached_data("metrics_bad_codes", codes, ttl=1800)
            except Exception as _re:
                logger.warning(f"重算异常代码失败，返回空列表: {_re}")
        return SuccessResponse(
            message="获取异常代码成功", data={"count": len(codes), "codes": codes}
        )
    except Exception as e:
        logger.error(f"获取异常代码失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取异常代码失败: {str(e)}")


@router.post("/stocks/metrics/refetch")
async def refetch_metrics(
    payload: RefetchRequest,
    all: Optional[bool] = Query(False, description="是否对全部异常代码重抓"),
    force: Optional[bool] = Query(False, description="是否强制忽略近期缓存重抓"),
    batch_size: Optional[int] = Query(50, ge=1, le=200, description="批处理大小"),
    concurrent_limit: Optional[int] = Query(10, ge=1, le=50, description="并发上限"),
    api_service=Depends(get_api_service),
):
    """重抓财务指标，支持传入 codes 或使用缓存的异常列表（all=true）"""
    try:
        target_codes: List[str] = []
        if payload and payload.codes:
            target_codes = [c for c in payload.codes if isinstance(c, str)]
        elif all:
            cached = api_service.get_cached_data("metrics_bad_codes") or []
            if isinstance(cached, list):
                target_codes = cached

        if not target_codes:
            return SuccessResponse(
                message="没有需要重抓的代码",
                data={"total_processed": 0, "cached_count": 0},
            )

        # 标准化为 ts_code（带交易所后缀）
        def to_ts_code(code: str) -> Optional[str]:
            if not code:
                return None
            code = code.strip()
            if "." in code:
                return code
            if code.startswith(("0", "3")):
                return f"{code}.SZ"
            if code.startswith("6"):
                return f"{code}.SH"
            return None

        ts_codes = [to_ts_code(c) for c in target_codes]
        ts_codes = [c for c in ts_codes if c]
        if not ts_codes:
            return SuccessResponse(
                message="代码格式不识别，未处理",
                data={"total_processed": 0, "cached_count": 0},
            )

        # 构造最小记录集供批处理器使用
        minimal_records = [{"ts_code": c} for c in ts_codes]

        # 构造适配器
        from adapters.factory import AdapterFactory

        factory = AdapterFactory()
        try:
            full_cfg = api_service.config_manager.get_config("application") or {}
            tushare_cfg = (full_cfg.get("data_sources", {}) or {}).get(
                "tushare", {}
            ) or {}
        except Exception as _e:
            logger.warning(f"读取tushare配置失败: {_e}")
            tushare_cfg = {}
        adapter = factory.get_or_create_adapter("tushare", tushare_cfg)

        # 运行批处理（带 force）
        from webapp.services.stock_data_service import cache_financial_metrics_batch

        await cache_financial_metrics_batch(
            records=minimal_records,
            adapter=adapter,
            batch_size=batch_size or 50,
            concurrent_limit=concurrent_limit or 10,
            force=bool(force),
        )

        # 简单统计：从DB读取刚刚覆盖的条目数
        from core.database import stock_db

        db_metrics = stock_db.get_stock_metrics(
            symbols=[c.split(".")[0] for c in ts_codes], cache_hours=1
        )
        cached_count = len([k for k, v in (db_metrics or {}).items() if v])

        return SuccessResponse(
            message="重抓任务已触发",
            data={
                "total_processed": len(ts_codes),
                "cached_count": cached_count,
            },
        )
    except Exception as e:
        logger.error(f"重抓财务指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"重抓财务指标失败: {str(e)}")


@router.get("/stocks/search")
async def search_stocks(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回数量限制"),
    api_service=Depends(get_api_service),
):
    """搜索股票"""
    try:
        cache_key = f"search_{q}_{limit}"
        cached = api_service.get_cached_data(cache_key)
        if cached:
            return SuccessResponse(message="搜索成功（缓存）", data=cached)

        from core.database import stock_db

        stocks = stock_db.get_stock_basic_data(cache_hours=24)
        if not stocks:
            return SuccessResponse(message="搜索完成", data=[])

        results = []
        q_lower = q.lower()

        for stock in stocks:
            code = stock.get("ts_code", "").split(".")[0]
            name = stock.get("name", "")

            if (
                q_lower in code.lower()
                or q_lower in name.lower()
                or q_lower in stock.get("fullname", "").lower()
            ):
                results.append(
                    {
                        "code": code,
                        "name": name,
                        "fullname": stock.get("fullname", ""),
                        "industry": stock.get("industry", ""),
                        "market": stock.get("market", ""),
                    }
                )

                if len(results) >= limit:
                    break

        api_service.set_cached_data(cache_key, results, ttl=1800)
        return SuccessResponse(message="搜索完成", data=results)

    except Exception as e:
        logger.error(f"搜索股票失败: {q}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


# ========== 策略执行相关路由 ==========


@router.post("/stocks/screen")
async def screen_stocks(
    strategy_data: dict,
    api_service=Depends(get_api_service),
):
    """执行股票筛选策略 - 兼容性wrapper"""
    try:
        strategy_name = strategy_data.get("strategy", "schloss")
        top_n = strategy_data.get("top_n", 20)

        # 委托给策略路由
        from webapp.routes.strategy_routes import execute_strategy

        return await execute_strategy(strategy_name, top_n, api_service)

    except Exception as e:
        logger.error(f"股票筛选失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"筛选失败: {str(e)}")


@router.post("/stocks/cache-metrics")
async def cache_metrics(
    params: dict = {},
    api_service=Depends(get_api_service),
):
    """手动缓存财务指标"""
    try:
        from core.database import stock_db

        # 强制刷新缓存
        stocks_data = stock_db.get_stock_basic_data(cache_hours=0)
        count = len(stocks_data) if stocks_data else 0

        return SuccessResponse(
            message=f"缓存刷新完成，处理 {count} 条股票数据",
            data={"count": count, "timestamp": datetime.now().isoformat()},
        )

    except Exception as e:
        logger.error(f"缓存指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"缓存失败: {str(e)}")


# ========== 市场信息相关路由 ==========


@router.get("/stocks/markets")
async def get_markets(api_service=Depends(get_api_service)):
    """获取支持的市场"""
    try:
        markets = [
            {"code": "a_stock", "name": "A股市场"},
            {"code": "us", "name": "美股市场"},
            {"code": "hk", "name": "港股市场"},
        ]
        return SuccessResponse(message="获取市场信息成功", data=markets)

    except Exception as e:
        logger.error(f"获取市场信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场信息失败: {str(e)}")


@router.get("/stocks/industries")
async def get_industries(
    market: str = Query("a_stock", description="市场代码"),
    api_service=Depends(get_api_service),
):
    """获取行业分类"""
    try:
        from core.database import stock_db

        cache_key = f"industries_{market}"
        cached_result = api_service.get_cached_data(cache_key)
        if cached_result:
            return SuccessResponse(message="获取行业分类成功", data=cached_result)

        stocks_data = stock_db.get_stock_basic_data(cache_hours=24)
        if not stocks_data:
            return SuccessResponse(message="暂无行业数据", data=[])

        industries = {}
        for stock in stocks_data:
            industry = stock.get("industry", "未分类")
            if industry not in industries:
                industries[industry] = 0
            industries[industry] += 1

        # 转换为前端需要的格式
        industry_list = [
            {"code": industry, "name": industry, "count": count}
            for industry, count in sorted(
                industries.items(), key=lambda x: x[1], reverse=True
            )
        ]

        api_service.set_cached_data(cache_key, industry_list, ttl=3600)
        return SuccessResponse(message="获取行业分类成功", data=industry_list)

    except Exception as e:
        logger.error(f"获取行业分类失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取行业分类失败: {str(e)}")


@router.get("/stocks/trending")
async def get_trending_stocks(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    api_service=Depends(get_api_service),
):
    """获取热门股票"""
    try:
        from core.database import stock_db

        cache_key = f"trending_stocks_{limit}"
        cached_result = api_service.get_cached_data(cache_key)
        if cached_result:
            return SuccessResponse(message="获取热门股票成功", data=cached_result)

        stocks_data = stock_db.get_stock_basic_data(cache_hours=24)
        if not stocks_data:
            return SuccessResponse(message="暂无股票数据", data=[])

        # 简单的热门排序：按市值排序
        sorted_stocks = sorted(
            [s for s in stocks_data if s.get("total_mv")],
            key=lambda x: _safe_float(x.get("total_mv", 0)) or 0,
            reverse=True,
        )[:limit]

        trending_list = []
        for stock in sorted_stocks:
            trending_list.append(
                {
                    "code": stock.get("ts_code", "").split(".")[0],
                    "name": stock.get("name", ""),
                    "industry": stock.get("industry", ""),
                    "market_value": _safe_float(stock.get("total_mv")),
                    "pe_ratio": _safe_float(stock.get("pe")),
                }
            )

        api_service.set_cached_data(cache_key, trending_list, ttl=1800)
        return SuccessResponse(message="获取热门股票成功", data=trending_list)

    except Exception as e:
        logger.error(f"获取热门股票失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热门股票失败: {str(e)}")


@router.get("/stocks/health/tushare")
async def check_tushare_health(api_service=Depends(get_api_service)):
    """Tushare健康检查"""
    try:
        # 检查Tushare连接状态
        from adapters.tushare_adapter import TushareAdapter
        from core.config_manager import config_manager

        # 获取配置
        app_config = config_manager.get_config("application", default={})
        tushare_config = app_config.get("tushare", {})

        try:
            adapter = TushareAdapter(tushare_config)
            # 简单的连接测试 - 检查适配器是否成功创建
            return SuccessResponse(
                message="Tushare连接正常",
                data={
                    "status": "healthy",
                    "api_ready": True,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as adapter_error:
            return SuccessResponse(
                message="Tushare连接异常",
                data={
                    "status": "error",
                    "api_ready": False,
                    "error": str(adapter_error),
                    "timestamp": datetime.now().isoformat(),
                },
            )

    except Exception as e:
        logger.error(f"Tushare健康检查失败: {str(e)}")
        return SuccessResponse(
            message="Tushare连接异常",
            data={
                "status": "error",
                "api_ready": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )
