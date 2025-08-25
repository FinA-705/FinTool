"""
股票数据相关API路由 - 详细信息
"""
from fastapi import APIRouter, Depends, HTTPException
from webapp.models import SuccessResponse
from utils.logger import get_logger
from datetime import datetime

logger = get_logger("stock_info_routes")
router = APIRouter()


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service
    return api_service


def _safe_float(x):
    try:
        if x in (None, ""):
            return None
        return float(x)
    except Exception:
        return None


@router.get("/info/{stock_code}")
async def get_stock_info(stock_code: str, api_service=Depends(get_api_service)):
    """获取单只股票详细信息"""
    try:
        pure_code = stock_code.split(".")[0]
        cache_key = f"stock_info_{pure_code}"
        cached = api_service.get_cached_data(cache_key)
        if cached:
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
            "financial_metrics": metrics,
            "update_time": datetime.now().isoformat(),
            "data_source": "database",
        }
        api_service.set_cached_data(cache_key, stock_info, ttl=300)
        return SuccessResponse(message="股票信息获取成功", data=stock_info)
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取股票信息失败: {str(e)}")


async def _fetch_and_cache_metrics(info, pure_code, api_service):
    """获取并缓存财务指标"""
    metrics_cache_key = f"stock_metrics_{pure_code}"
    cached_metrics = api_service.get_cached_data(metrics_cache_key)
    if cached_metrics:
        return cached_metrics

    try:
        from adapters.factory import AdapterFactory
        from webapp.app import api_service as _svc

        full_cfg = _svc.config_manager.get_config("application") or {}
        tushare_cfg = (full_cfg.get("data_sources", {}) or {}).get("tushare", {}) or {}
        adapter = AdapterFactory().get_or_create_adapter("tushare", tushare_cfg)
        ts_code = info.get("ts_code") or info.get("code") or pure_code
        if "." not in ts_code:
            if ts_code.startswith(("0", "3")):
                ts_code += ".SZ"
            elif ts_code.startswith("6"):
                ts_code += ".SH"
            elif ts_code.startswith("8"):
                ts_code += ".BJ"

        adapter._init_client()
        client = adapter._client
        pe, pb, roe, roa, debt_ratio, eps = None, None, None, None, None, None

        if client:
            try:
                daily_df = client.daily_basic(ts_code=ts_code)
                if daily_df is not None and not daily_df.empty:
                    row = daily_df.sort_values("trade_date", ascending=False).iloc[0]
                    pe = _safe_float(row.get("pe"))
                    pb = _safe_float(row.get("pb"))
            except Exception as de:
                logger.warning(f"获取 daily_basic 失败: {ts_code} {de}")

            try:
                fina_df = client.fina_indicator(ts_code=ts_code)
                if fina_df is not None and not fina_df.empty:
                    frow = fina_df.sort_values("end_date", ascending=False).iloc[0]
                    roe = _safe_float(frow.get("roe"))
                    roa = _safe_float(frow.get("roa"))
                    debt_ratio = _safe_float(frow.get("debt_to_assets")) or _safe_float(frow.get("assets_to_eqt"))
                    eps = _safe_float(frow.get("eps_basic")) or _safe_float(frow.get("eps"))
            except Exception as fe:
                logger.warning(f"获取财务指标失败: {ts_code} {fe}")

        metrics = {
            "pe": pe, "pb": pb, "roe": roe, "roa": roa,
            "debt_ratio": debt_ratio, "eps": eps
        }
        api_service.set_cached_data(metrics_cache_key, metrics, ttl=600)
        return metrics
    except Exception as me:
        logger.warning(f"获取{pure_code} 估值/财务指标失败: {me}")
        return {}
