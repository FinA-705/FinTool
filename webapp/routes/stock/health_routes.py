"""
股票数据相关API路由 - 健康检查
"""
from fastapi import APIRouter, HTTPException
from webapp.models import SuccessResponse
from utils.logger import get_logger

logger = get_logger("stock_health_routes")
router = APIRouter()


@router.get("/health/tushare")
async def tushare_health():
    """Tushare 适配器健康检查"""
    try:
        from adapters.factory import AdapterFactory
        from webapp.app import api_service as _api_service

        full_cfg = _api_service.config_manager.get_config("application") or {}
        tushare_cfg = (full_cfg.get("data_sources", {}) or {}).get("tushare", {}) or {}
        factory = AdapterFactory()
        adapter = factory.get_or_create_adapter("tushare", tushare_cfg)
        info = getattr(
            adapter,
            "health_check",
            lambda: {"adapter": "tushare", "error": "health_check not implemented"},
        )()
        status = "healthy" if info.get("token_valid") else "degraded"
        return SuccessResponse(message=f"Tushare健康检查: {status}", data=info)
    except Exception as e:
        logger.error(f"Tushare健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")
