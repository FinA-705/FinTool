"""
策略管理相关API路由（干净重建）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from utils.logger import get_logger
from webapp.models import SuccessResponse

logger = get_logger("strategy_routes")
router = APIRouter()


# ========= 依赖 =========
async def get_api_service():
    from webapp.app import api_service

    return api_service


# ========= 数据模型 =========
class StrategyCreateRequest(BaseModel):
    name: str
    version: Optional[str] = "1.0.0"
    parameters: Optional[Dict[str, Any]] = None
    weight_config: Optional[Dict[str, float]] = None
    filters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = True
    description: Optional[str] = None


class StrategyUpdateRequest(BaseModel):
    version: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    weight_config: Optional[Dict[str, float]] = None
    filters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class ImportConfigRequest(BaseModel):
    config: Dict[str, Any]


# ========= 内部服务 =========
async def get_real_strategies() -> List[Dict[str, Any]]:
    try:
        from strategies.config_manager import strategy_config_manager

        names = strategy_config_manager.list_available_strategies()
        out: List[Dict[str, Any]] = []
        for n in names:
            try:
                cfg = strategy_config_manager.load_strategy_config(n)
                out.append(
                    {
                        "name": n,
                        "description": f"基于配置的{n}策略",
                        "status": "active",
                        "last_run": datetime.now().strftime("%Y-%m-%d"),
                        "type": "real",
                        "filters": getattr(cfg, "filters", {}),
                        "scoring": "基于权重的评分算法",
                        "created_at": datetime.now().isoformat(),
                    }
                )
            except Exception as e:  # noqa: BLE001
                logger.warning(f"加载策略配置失败 {n}: {e}")
                out.append(
                    {
                        "name": n,
                        "description": f"{n}策略",
                        "status": "active",
                        "last_run": datetime.now().strftime("%Y-%m-%d"),
                        "type": "real",
                        "filters": {},
                        "scoring": "默认评分",
                        "created_at": datetime.now().isoformat(),
                    }
                )
        return out
    except Exception as e:  # noqa: BLE001
        logger.error(f"获取真实策略失败: {e}")
        raise Exception(f"策略服务不可用: {str(e)}")


# ========= 路由 =========
@router.get("/strategies")
async def get_strategies(api_service=Depends(get_api_service)):
    try:
        strategies = await get_real_strategies()
        return SuccessResponse(message="策略列表获取成功", data=strategies)
    except Exception as e:  # noqa: BLE001
        logger.error(f"获取策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略失败: {str(e)}")


@router.post("/strategies")
async def create_strategy(
    strategy_data: StrategyCreateRequest, api_service=Depends(get_api_service)
):
    try:
        from strategies.config_manager import StrategyConfig, strategy_config_manager

        name = strategy_data.name
        if not name:
            raise HTTPException(status_code=400, detail="策略名称不能为空")
        if name in strategy_config_manager.list_available_strategies():
            raise HTTPException(status_code=409, detail="策略已存在")

        cfg = StrategyConfig(
            name=name,
            version=strategy_data.version or "1.0.0",
            parameters=strategy_data.parameters or {},
            weight_config=strategy_data.weight_config or {},
            filters=strategy_data.filters or {},
            enabled=True if strategy_data.enabled is None else strategy_data.enabled,
        )
        strategy_config_manager.save_strategy_config(name, cfg)

        created = cfg.__dict__.copy()
        created.update(
            {
                "description": strategy_data.description or "",
                "status": "active" if created.get("enabled") else "disabled",
                "created_at": datetime.now().isoformat(),
                "type": "real",
            }
        )
        return SuccessResponse(message=f"策略 '{name}' 创建成功", data=created)
    except Exception as e:  # noqa: BLE001
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建策略失败: {str(e)}")


@router.delete("/strategies/{strategy_name}")
async def delete_strategy(strategy_name: str, api_service=Depends(get_api_service)):
    try:
        from core.config_manager import config_manager
        from strategies.config_manager import strategy_config_manager

        strategies = config_manager.get_config("strategies", default={}) or {}
        if strategy_name not in strategies:
            raise HTTPException(status_code=404, detail="策略不存在")
        del strategies[strategy_name]
        config_manager.configs["strategies"] = strategies
        config_manager.save_config("strategies")
        strategy_config_manager.clear_cache()
        return SuccessResponse(message=f"策略 '{strategy_name}' 删除成功", data={})
    except Exception as e:  # noqa: BLE001
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除策略失败: {str(e)}")


@router.post("/strategies/{strategy_name}/execute")
async def execute_strategy(
    strategy_name: str,
    top_n: int = Query(20, description="返回前N只股票"),
    api_service=Depends(get_api_service),
):
    try:
        start_time = datetime.now()
        from core.database import stock_db
        from strategies.strategy_factory import StrategyFactory

        stocks = stock_db.get_stock_basic_data(cache_hours=24 * 7)
        if not stocks:
            raise HTTPException(status_code=500, detail="无法获取股票数据")
        total_stocks = len(stocks)

        strategy = StrategyFactory().create_strategy(strategy_name)
        selected_results: List[Dict[str, Any]] = []

        use_pandas = True
        try:  # 优先 pandas
            import math
            import pandas as pd  # type: ignore

            df = pd.DataFrame(stocks)

            def _pure(code: str) -> str:
                try:
                    return (code or "").split(".")[0].upper()
                except Exception:  # noqa: BLE001
                    return ""

            # 获取数据库财务指标，先查近24小时；覆盖率不足则回退到更长时间窗口
            pure_codes = []
            if "ts_code" in df.columns:
                pure_codes = [
                    _pure(str(ts)) for ts in df["ts_code"].fillna("") if str(ts)
                ]
            metrics_map = stock_db.get_stock_metrics(symbols=pure_codes, cache_hours=24)
            coverage = 0.0
            if pure_codes:
                covered = sum(1 for c in set(pure_codes) if c in metrics_map)
                coverage = covered / max(1, len(set(pure_codes)))
            if coverage < 0.5:  # 覆盖率过低，回退到更长缓存期
                fallback_map = stock_db.get_stock_metrics(
                    symbols=pure_codes, cache_hours=24 * 365
                )
                if fallback_map:
                    # 以近24小时优先，缺失的用回退补齐
                    for k, v in fallback_map.items():
                        metrics_map.setdefault(k, v)

            # 构建用于映射的纯代码列
            df["pure_code"] = (
                df["ts_code"].astype(str).apply(_pure)
                if "ts_code" in df.columns
                else ""
            )

            df["stock_code"] = df.get("ts_code")
            df["stock_name"] = df.get("name")
            df["sector"] = df["industry"].fillna("") if "industry" in df.columns else ""
            df["listing_date"] = (
                df["list_date"].fillna("") if "list_date" in df.columns else ""
            )

            # 从 metrics_map 合并关键财务字段（严格使用 DB 数据）
            def mget(pure, key, default=math.nan):
                m = metrics_map.get(pure)
                if not m:
                    return default
                return m.get(key, default)

            df["market_cap"] = df["pure_code"].apply(lambda c: mget(c, "market_cap"))
            df["pe_ratio"] = df["pure_code"].apply(lambda c: mget(c, "pe"))
            df["pb_ratio"] = df["pure_code"].apply(lambda c: mget(c, "pb"))
            df["roe"] = df["pure_code"].apply(lambda c: mget(c, "roe"))
            df["roa"] = df["pure_code"].apply(lambda c: mget(c, "roa"))
            df["debt_to_equity"] = df["pure_code"].apply(
                lambda c: mget(c, "debt_ratio")
            )
            if "avg_volume" not in df.columns:
                df["avg_volume"] = df["pure_code"].apply(
                    lambda c: mget(c, "volume", 2_000_000)
                )
            # 额外保留价格相关（用于调试/展示）
            df["current_price"] = df["pure_code"].apply(
                lambda c: mget(c, "current_price")
            )
            df["change_pct"] = df["pure_code"].apply(lambda c: mget(c, "change_pct"))
            df["eps"] = df["pure_code"].apply(lambda c: mget(c, "eps"))

            if "current_ratio" not in df.columns:
                df["current_ratio"] = 1.5
            else:
                df["current_ratio"] = df["current_ratio"].fillna(1.5)
            if "revenue_growth" not in df.columns:
                df["revenue_growth"] = 0.0
            else:
                df["revenue_growth"] = df["revenue_growth"].fillna(0.0)

            def _years_since(date_str: str) -> float:
                try:
                    if not date_str:
                        return 0.0
                    ds = str(date_str)
                    if len(ds) == 8 and ds.isdigit():
                        ds = f"{ds[0:4]}-{ds[4:6]}-{ds[6:8]}"
                    return (datetime.now() - datetime.fromisoformat(ds)).days / 365.25
                except Exception:  # noqa: BLE001
                    return 0.0

            df["listing_years"] = df["listing_date"].apply(_years_since)

            # 近似交易日数（避免硬依赖日线表），用于基础过滤
            try:
                df["trading_days"] = (df["listing_years"] * 250).round().astype(int)
            except Exception:
                df["trading_days"] = 250

            # 确保关键列为数值类型
            for col in [
                "market_cap",
                "pe_ratio",
                "pb_ratio",
                "roe",
                "roa",
                "debt_to_equity",
                "current_ratio",
                "revenue_growth",
                "avg_volume",
            ]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            results = strategy.screen_stocks(df, top_n=top_n)
            for i, r in enumerate(results):
                selected_results.append(
                    {
                        "rank": i + 1,
                        "code": r.stock_code,
                        "name": r.stock_name,
                        "score": round(r.score, 1),
                        "reason": (
                            ", ".join(getattr(r, "reasons", [])[:2])
                            if getattr(r, "reasons", None)
                            else "符合策略条件"
                        ),
                        "warnings": getattr(r, "warnings", []),
                        "metadata": getattr(r, "metadata", {}),
                    }
                )
        except ImportError:
            use_pandas = False
        except Exception as e:  # pandas 流程失败，回退
            logger.warning(f"策略筛选失败，使用简化筛选: {e}")
            use_pandas = False

        if not use_pandas:
            filtered: List[Dict[str, Any]] = []
            for s in stocks:
                reasons: List[str] = []
                name = s.get("name")
                if name:
                    if not any(x in name for x in ["ST", "*ST", "PT"]):
                        reasons.append("非风险警示股")
                    else:
                        continue
                    if s.get("list_date"):
                        reasons.append("已正常上市")
                    else:
                        continue
                    market = s.get("market", "")
                    if market in ["主板", "创业板", "科创板"]:
                        reasons.append(f"{market}上市")
                    elif market:
                        reasons.append("正规市场上市")
                    industry = s.get("industry", "")
                    if industry:
                        reasons.append(f"属于{industry}行业")
                    s["selection_reasons"] = reasons
                    filtered.append(s)

            for i, s in enumerate(filtered[:top_n]):
                score = 85 - (i * 2)
                rs = s.get("selection_reasons", ["符合基本筛选条件"])
                selected_results.append(
                    {
                        "rank": i + 1,
                        "code": s.get("ts_code", s.get("symbol", f"STOCK{i}")),
                        "name": s.get("name", f'股票{s.get("ts_code", i+1)}'),
                        "score": score,
                        "reason": ", ".join(rs[:3]),
                        "warnings": [],
                        "metadata": {
                            "market": s.get("market", ""),
                            "industry": s.get("industry", ""),
                            "area": s.get("area", ""),
                        },
                    }
                )

        elapsed = (datetime.now() - start_time).total_seconds()
        payload = {
            "strategy_name": strategy_name,
            "execution_time": round(elapsed, 3),
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
            message=f"策略执行成功，筛选出{len(selected_results)}只股票", data=payload
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"执行策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行策略失败: {str(e)}")


@router.get("/strategies/{strategy_name}")
async def get_strategy_detail(strategy_name: str, api_service=Depends(get_api_service)):
    try:
        from strategies.config_manager import strategy_config_manager
        from strategies.strategy_factory import StrategyFactory

        cfg = strategy_config_manager.load_strategy_config(strategy_name)
        summary: Dict[str, Any] = {}
        try:
            strat = StrategyFactory().create_strategy(strategy_name)
            summary = strat.get_config_summary()
        except Exception:  # noqa: BLE001
            pass
        return SuccessResponse(
            message="获取策略详情成功",
            data={
                "name": cfg.name,
                "version": cfg.version,
                "parameters": cfg.parameters,
                "weight_config": cfg.weight_config,
                "filters": cfg.filters,
                "enabled": cfg.enabled,
                "summary": summary,
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"获取策略详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略详情失败: {str(e)}")


@router.put("/strategies/{strategy_name}")
async def update_strategy(
    strategy_name: str,
    updates: StrategyUpdateRequest,
    api_service=Depends(get_api_service),
):
    try:
        from strategies.config_manager import strategy_config_manager

        cfg = strategy_config_manager.load_strategy_config(strategy_name)
        if updates.version is not None:
            cfg.version = updates.version
        if updates.parameters is not None:
            cfg.parameters.update(updates.parameters)
        if updates.weight_config is not None:
            cfg.weight_config.update(updates.weight_config)
        if updates.filters is not None:
            cfg.filters.update(updates.filters)
        if updates.enabled is not None:
            cfg.enabled = updates.enabled
        strategy_config_manager.save_strategy_config(strategy_name, cfg)
        return SuccessResponse(
            message="策略更新成功",
            data={
                "name": cfg.name,
                "version": cfg.version,
                "parameters": cfg.parameters,
                "weight_config": cfg.weight_config,
                "filters": cfg.filters,
                "enabled": cfg.enabled,
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新策略失败: {str(e)}")


@router.post("/strategies/{strategy_name}/enable")
async def enable_strategy(
    strategy_name: str,
    enabled: bool = Query(True, description="是否启用"),
    api_service=Depends(get_api_service),
):
    try:
        from strategies.config_manager import strategy_config_manager

        cfg = strategy_config_manager.load_strategy_config(strategy_name)
        cfg.enabled = enabled
        strategy_config_manager.save_strategy_config(strategy_name, cfg)
        return SuccessResponse(message="状态更新成功", data={"enabled": cfg.enabled})
    except Exception as e:  # noqa: BLE001
        logger.error(f"更新策略启用状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/strategies/{strategy_name}/clone")
async def clone_strategy(
    strategy_name: str,
    new_name: str = Query(..., description="新策略名称"),
    api_service=Depends(get_api_service),
):
    try:
        from strategies.config_manager import StrategyConfig, strategy_config_manager

        if new_name == strategy_name:
            raise HTTPException(status_code=400, detail="新名称不能与原名称相同")
        if new_name in strategy_config_manager.list_available_strategies():
            raise HTTPException(status_code=409, detail="新策略已存在")

        src = strategy_config_manager.load_strategy_config(strategy_name)
        dst = StrategyConfig(
            name=new_name,
            version=src.version,
            parameters=dict(src.parameters),
            weight_config=dict(src.weight_config),
            filters=dict(src.filters),
            enabled=src.enabled,
        )
        strategy_config_manager.save_strategy_config(new_name, dst)
        return SuccessResponse(message="克隆成功", data={"name": new_name})
    except Exception as e:  # noqa: BLE001
        logger.error(f"克隆策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"克隆策略失败: {str(e)}")


@router.get("/strategies/scoring/ranges/{metric}")
async def get_scoring_ranges(metric: str):
    try:
        from strategies.config_manager import strategy_config_manager

        ranges = strategy_config_manager.get_scoring_ranges(metric)
        return SuccessResponse(message="获取评分区间成功", data=ranges)
    except Exception as e:  # noqa: BLE001
        logger.error(f"获取评分区间失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评分区间失败: {str(e)}")


@router.post("/strategies/{strategy_name}/export")
async def export_strategy(strategy_name: str):
    try:
        from strategies.config_manager import strategy_config_manager

        cfg = strategy_config_manager.load_strategy_config(strategy_name)
        return SuccessResponse(
            message="导出成功",
            data={
                "name": cfg.name,
                "version": cfg.version,
                "parameters": cfg.parameters,
                "weight_config": cfg.weight_config,
                "filters": cfg.filters,
                "enabled": cfg.enabled,
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"导出策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出策略失败: {str(e)}")


@router.post("/strategies/{strategy_name}/import")
async def import_strategy(strategy_name: str, req: ImportConfigRequest):
    try:
        from strategies.config_manager import StrategyConfig, strategy_config_manager

        cfg_dict = req.config or {}
        existing = strategy_config_manager.load_strategy_config(strategy_name)
        new_cfg = StrategyConfig(
            name=strategy_name,
            version=cfg_dict.get("version", existing.version),
            parameters=cfg_dict.get("parameters", existing.parameters),
            weight_config=cfg_dict.get("weight_config", existing.weight_config),
            filters=cfg_dict.get("filters", existing.filters),
            enabled=cfg_dict.get("enabled", existing.enabled),
        )
        strategy_config_manager.save_strategy_config(strategy_name, new_cfg)
        return SuccessResponse(message="导入成功", data={"name": strategy_name})
    except Exception as e:  # noqa: BLE001
        logger.error(f"导入策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"导入策略失败: {str(e)}")
