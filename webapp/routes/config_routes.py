"""
配置管理相关API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import json
import time
import platform
import psutil
from datetime import datetime

from webapp.models import (
    ConfigResponse,
    ConfigUpdateRequest,
    SuccessResponse,
    ErrorResponse,
)
from core.config_manager import CoreConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        from core.database import stock_db
        import os

        stats = {}

        # 获取策略数量
        try:
            from strategies.strategy_factory import StrategyFactory
            from strategies.config_manager import strategy_config_manager

            strategy_names = strategy_config_manager.list_available_strategies()
            stats["strategies"] = len(strategy_names)
        except Exception as e:
            logger.warning(f"获取策略数量失败: {e}")
            stats["strategies"] = 0

        # 获取股票数据数量
        try:
            # 先尝试较短缓存时间，再尝试更长的
            cached_stocks = stock_db.get_stock_basic_data(
                cache_hours=1
            )  # 1小时内的缓存
            if not cached_stocks:
                cached_stocks = stock_db.get_stock_basic_data(
                    cache_hours=24 * 7
                )  # 7天内的缓存
            stats["stocks"] = len(cached_stocks) if cached_stocks else 0
        except Exception as e:
            logger.warning(f"获取股票数量失败: {e}")
            stats["stocks"] = 0

        # 获取回测任务数量（从缓存或日志文件中）
        try:
            # 统计日志文件中的回测记录
            backtest_count = 0
            logs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs"
            )
            if os.path.exists(logs_dir):
                # 简单地基于日志文件数量估算
                log_files = [
                    f
                    for f in os.listdir(logs_dir)
                    if f.endswith(".log") or f.endswith(".log.zip")
                ]
                backtest_count = len(log_files)
            stats["backtests"] = backtest_count
        except Exception as e:
            logger.warning(f"获取回测任务数量失败: {e}")
            stats["backtests"] = 0

        # 系统运行状态
        stats["uptime"] = "运行中"
        stats["status"] = "healthy"

        # 额外的系统信息
        try:
            stats["cache_status"] = (
                "active" if stock_db.is_cache_valid(cache_hours=24) else "expired"
            )
        except:
            stats["cache_status"] = "unknown"
        stats["last_updated"] = datetime.now().isoformat()

        return SuccessResponse(message="系统统计信息获取成功", data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计信息失败: {str(e)}")


@router.get("/info")
async def get_system_info():
    """获取系统信息"""
    try:
        import sys

        # 获取系统基本信息
        memory = psutil.virtual_memory()

        system_info = {
            "system": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "os": platform.system(),
                "cpu_cores": psutil.cpu_count(),
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent,
                },
            },
            "dependencies": [
                {"name": "FastAPI", "status": "active"},
                {"name": "数据适配器", "status": "active"},
                {"name": "策略引擎", "status": "active"},
            ],
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }

        return SuccessResponse(message="系统信息获取成功", data=system_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")


async def get_api_service():
    """获取API服务实例的依赖注入"""
    from webapp.app import api_service

    return api_service


@router.get("/config", response_model=ConfigResponse)
async def get_config(api_service=Depends(get_api_service)):
    """获取当前配置"""
    try:
        config = api_service.config_manager.get_all_config()
        return ConfigResponse(message="配置获取成功", data=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/config/{section}")
async def get_config_section(section: str, api_service=Depends(get_api_service)):
    """获取指定配置节"""
    try:
        config = api_service.config_manager.get_config(section)
        if config is None:
            raise HTTPException(status_code=404, detail=f"配置节 '{section}' 不存在")

        return SuccessResponse(message=f"配置节 '{section}' 获取成功", data=config)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config")
async def update_config(
    request: ConfigUpdateRequest, api_service=Depends(get_api_service)
):
    """更新配置项"""
    try:
        # 类型转换
        value = request.value
        if request.type == "int":
            value = int(value)
        elif request.type == "float":
            value = float(value)
        elif request.type == "bool":
            value = bool(value)
        elif request.type == "json":
            value = json.loads(value)

        # 更新配置
        # CoreConfigManager 需要三个参数: config_name, key_path, value
        # 假设使用 "application" 作为默认的配置名称
        api_service.config_manager.set_config("application", request.key, value)

        return SuccessResponse(
            message=f"配置项 '{request.key}' 更新成功",
            data={"key": request.key, "value": value},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.get("/config/strategies")
async def get_strategies_config(api_service=Depends(get_api_service)):
    """获取策略配置"""
    try:
        strategies = api_service.config_manager.get_config("strategies", {})
        return SuccessResponse(message="策略配置获取成功", data=strategies)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略配置失败: {str(e)}")


@router.get("/config/data_sources")
async def get_data_sources_config(api_service=Depends(get_api_service)):
    """获取数据源配置"""
    try:
        data_sources = api_service.config_manager.get_config("data_sources", {})
        return SuccessResponse(message="数据源配置获取成功", data=data_sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源配置失败: {str(e)}")


@router.post("/config/reload")
async def reload_config(api_service=Depends(get_api_service)):
    """重新加载配置"""
    try:
        # 重新加载配置文件
        config_file = api_service.config_manager._config_file
        api_service.config_manager.load_config(config_file)

        timestamp = getattr(api_service.config_manager, "_last_modified", time.time())
        return SuccessResponse(
            message="配置重新加载成功",
            data={"timestamp": timestamp},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")


@router.post("/config/reset")
async def reset_config(api_service=Depends(get_api_service)):
    """重置配置为默认值"""
    try:
        # 使用示例配置文件作为默认配置
        default_config_file = "config/config.example.yaml"
        api_service.config_manager.load_config(default_config_file)

        return SuccessResponse(message="配置已重置为默认值", data={})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="默认配置文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置配置失败: {str(e)}")


@router.post("/cache/clear")
async def clear_cache(api_service=Depends(get_api_service)):
    """清除所有缓存数据"""
    try:
        # 清除应用内存缓存
        if hasattr(api_service, "cache_manager"):
            api_service.cache_manager.clear_all()

        # 清除应用内部的数据缓存
        if hasattr(api_service, "_data_cache"):
            api_service._data_cache.clear()

        # 清除数据库缓存
        from core.database import stock_db

        stock_db.clear_cache()

        return SuccessResponse(
            message="所有缓存数据已清除", data={"cleared_at": time.time()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@router.get("/cache/info")
async def get_cache_info(api_service=Depends(get_api_service)):
    """获取缓存信息"""
    try:
        cache_info = {
            "cache_type": "application",
            "has_cache_manager": hasattr(api_service, "cache_manager"),
            "data_cache_size": (
                len(api_service._data_cache)
                if hasattr(api_service, "_data_cache")
                else 0
            ),
        }

        # 如果有缓存管理器，获取更详细的信息
        if hasattr(api_service, "cache_manager"):
            cache_manager = api_service.cache_manager
            cache_info.update(
                {
                    "cache_manager_type": str(cache_manager.config.cache_type.value),
                    "cache_dir": cache_manager.config.cache_dir,
                    "default_ttl": cache_manager.config.default_ttl,
                }
            )

        return SuccessResponse(message="缓存信息获取成功", data=cache_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存信息失败: {str(e)}")
