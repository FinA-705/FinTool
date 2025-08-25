"""
FastAPI应用创建和配置
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 添加项目根目录到sys.path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from webapp.routes import (
    main_routes,
    stock_routes,
    strategy_routes,
    backtest_routes,
    config_routes,
)
from core.api_service import APIService

# 全局API服务实例
api_service = APIService()


def create_app() -> FastAPI:
    """创建并配置FastAPI应用"""
    app = FastAPI(
        title="Financial Agent API",
        description="提供股票数据、策略执行和回测服务的API",
        version="1.0.0",
    )

    # 挂载静态文件目录
    static_dir = current_dir / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 包含API路由
    app.include_router(main_routes.router)
    app.include_router(stock_routes.router, prefix="/api/v1", tags=["Stocks"])
    app.include_router(strategy_routes.router, prefix="/api/v1", tags=["Strategies"])
    app.include_router(backtest_routes.router, prefix="/api/v1", tags=["Backtest"])
    app.include_router(config_routes.router, prefix="/api/v1", tags=["Config"])

    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        api_service.initialize()
        print("API服务已启动并初始化")

    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        api_service.shutdown()
        print("API服务已关闭")

    return app


app = create_app()
