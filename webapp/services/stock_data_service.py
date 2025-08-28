"""
股票数据服务层
"""

from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

from adapters.base import DataRequest, DataType, Market as AdapterMarket
from adapters.factory import AdapterFactory
from core.database import stock_db
from utils.logger import get_logger
from utils.env_config import env_config

logger = get_logger("stock_services")


# 更宽松且更实用的财务指标异常判定
def is_metrics_anomalous(metrics: Dict[str, Any]) -> bool:
    """判定一只股票的财务指标是否异常。

    规则（取任一命中即为异常）：
    - 大量缺失：关键字段缺失数 >= 3（pe/pb/roe/roa/market_cap/current_price）
    - 关键缺失：current_price 或 market_cap 缺失，且关键缺失总数 >= 2
    - 数值异常：
        current_price <= 0；
        pe <= 0 或 pe > 300；
        pb <= 0 或 pb > 80；
        roe < -50 或 roe > 80；
        debt_ratio < 0 或 debt_ratio > 95。

    注意：阈值可根据业务再调优。
    """
    if not isinstance(metrics, dict):
        return True

    keys = [
        "pe",
        "pb",
        "roe",
        "roa",
        "market_cap",
        "current_price",
    ]
    values = {k: metrics.get(k) for k in keys}

    def _to_float(x) -> Optional[float]:
        try:
            if x in (None, ""):
                return None
            return float(x)
        except Exception:
            return None

    missing_cnt = sum(1 for k, v in values.items() if v in (None, ""))
    if missing_cnt >= 3:
        return True

    # 关键缺失：价格或市值缺失，再叠加一个关键缺失就标记
    critical_missing = 0
    if values.get("current_price") in (None, ""):
        critical_missing += 1
    if values.get("market_cap") in (None, ""):
        critical_missing += 1
    if critical_missing >= 1 and missing_cnt >= 2:
        return True

    price = _to_float(values.get("current_price"))
    if price is not None and price <= 0:
        return True

    pe = _to_float(values.get("pe"))
    if pe is not None and (pe <= 0 or pe > 300):
        return True

    pb = _to_float(values.get("pb"))
    if pb is not None and (pb <= 0 or pb > 80):
        return True

    roe = _to_float(values.get("roe"))
    if roe is not None and (roe < -50 or roe > 80):
        return True

    debt_ratio = _to_float(metrics.get("debt_ratio"))
    if debt_ratio is not None and (debt_ratio < 0 or debt_ratio > 95):
        return True

    return False


async def get_all_stock_data_with_cache(
    market: str, symbol_list: Optional[List[str]] = None
) -> Any:
    """从Tushare获取所有股票数据并缓存到数据库"""
    try:
        # 首先检查数据库缓存
        cache_hours = 24  # 24小时缓存有效期

        if symbol_list:
            # 如果指定了股票代码，先从缓存获取
            cached_data = stock_db.get_stock_basic_data(
                symbols=symbol_list, cache_hours=cache_hours
            )
            if cached_data and len(cached_data) == len(symbol_list):
                logger.info(f"从数据库缓存获取到 {len(cached_data)} 条指定股票数据")
                return cached_data
        else:
            # 检查是否有完整的缓存数据
            # 第一次检查，不打印日志，避免混淆
            initial_check = stock_db.get_stock_basic_data(
                cache_hours=cache_hours, log_results=False
            )
            # 根据模式选择阈值：全量模式期望>1000；特选股模式阈值放宽
            threshold = 1000
            if env_config.selective_stocks_mode:
                threshold = 400  # 沪深300+中证500约800+，取保守下限
            if initial_check and len(initial_check) > threshold:
                logger.info(f"从数据库缓存获取到 {len(initial_check)} 条股票数据")
                return initial_check

        # 缓存无效或不完整，从Tushare获取新数据
        logger.info("数据库缓存无效或不完整，从Tushare获取新数据...")

        # 创建适配器工厂实例
        factory = AdapterFactory()
        # 从全局 api_service 的配置中获取 tushare 配置
        from webapp.app import api_service as _api_service

        tushare_cfg = {}
        try:
            full_cfg = _api_service.config_manager.get_config("application") or {}
            tushare_cfg = (full_cfg.get("data_sources", {}) or {}).get(
                "tushare", {}
            ) or {}
        except Exception as _e:  # 忽略配置获取异常，后续适配器内部会再尝试env
            logger.warning(f"读取tushare配置失败: {_e}")
        adapter = factory.get_or_create_adapter("tushare", tushare_cfg)

        # 转换市场类型
        adapter_market = (
            AdapterMarket.A_STOCK if market == "a_stock" else AdapterMarket.US_STOCK
        )

        # 如果指定了股票代码，获取指定股票；否则获取所有股票（无limit限制）
        data_request = DataRequest(
            symbols=symbol_list,
            market=adapter_market,
            data_type=DataType.BASIC_INFO,
            limit=None,  # 移除limit限制，获取所有数据
        )

        logger.info(
            f"开始从Tushare获取股票数据: market={market}, symbols={symbol_list}"
        )
        response = await adapter.get_data(data_request)

        if response.success and response.data is not None:
            data = response.data

            # 如果返回的是DataFrame，转换为字典列表
            if hasattr(data, "to_dict"):
                records = data.to_dict("records")
            elif isinstance(data, list):
                records = data
            else:
                records = []

            # 处理股票代码格式，确保正确显示
            for record in records:
                if isinstance(record, dict):
                    if "ts_code" in record:
                        record["code"] = record["ts_code"]  # 添加标准化的code字段
                    elif "symbol" in record:
                        record["code"] = record["symbol"]

                    # 确保有name字段
                    if "name" not in record and "company_name" in record:
                        record["name"] = record["company_name"]

            # 保存到数据库缓存
            try:
                if isinstance(records, list) and len(records) > 0:
                    # 确保records是正确的格式
                    valid_records = []
                    for record in records:
                        if isinstance(record, dict):
                            # 转换所有键为字符串
                            str_record = {str(k): v for k, v in record.items()}
                            valid_records.append(str_record)

                    if valid_records:
                        saved_count = stock_db.save_stock_basic_data(valid_records)
                        logger.info(
                            f"成功从Tushare获取 {len(records)} 条股票数据，保存到数据库 {saved_count} 条"
                        )

                        # 异步缓存财务指标数据（控制并发）
                        await cache_financial_metrics_batch(valid_records, adapter)
            except Exception as e:
                logger.warning(f"保存数据到数据库失败: {e}")

            return records
        else:
            logger.warning(
                f"从Tushare获取股票数据失败: {response.message if hasattr(response, 'message') else '未知错误'}"
            )

            # 如果从Tushare获取失败，尝试返回过期的缓存数据
            cached_data = stock_db.get_stock_basic_data(
                symbols=symbol_list, cache_hours=24 * 7
            )  # 尝试7天内的缓存
            if cached_data:
                logger.info(f"使用过期缓存数据: {len(cached_data)} 条")
                return cached_data

            return []

    except Exception as e:
        logger.error(f"获取股票数据失败: {e}")

        # 发生异常时，尝试返回缓存数据
        try:
            cached_data = stock_db.get_stock_basic_data(
                symbols=symbol_list, cache_hours=24 * 7
            )
            if cached_data:
                logger.info(f"异常情况下使用缓存数据: {len(cached_data)} 条")
                return cached_data
        except:
            pass

        raise Exception(f"数据获取服务不可用: {str(e)}")


async def cache_financial_metrics_batch(
    records: List[Dict],
    adapter,
    batch_size: int = 50,
    concurrent_limit: int = 10,
    force: bool = False,
):
    """
    批量缓存财务指标数据并存储到数据库，支持断点续传和进度日志

    Args:
        records: 股票基础信息列表
        adapter: Tushare适配器实例
        batch_size: 每批处理的股票数量
        concurrent_limit: 最大并发数
    """
    try:
        from webapp.app import api_service

        # 防并发：如果已有任务在进行，则跳过
        if api_service.get_cached_data("metrics_caching_lock"):
            logger.info("检测到财务指标缓存任务正在进行，跳过本次触发")
            return
        api_service.set_cached_data("metrics_caching_lock", True)

        adapter._init_client()
        client = adapter._client
        if client is None:
            logger.warning("Tushare客户端未初始化，跳过财务指标缓存")
            return

        def _safe_float(x):
            try:
                if x in (None, ""):
                    return None
                return float(x)
            except Exception:
                return None

        existing_metrics = stock_db.get_stock_metrics(cache_hours=1)
        processed_codes = set(existing_metrics.keys()) if not force else set()
        if force:
            logger.info("接收到 force 重抓指令，将忽略近期缓存，处理所有传入记录")
        else:
            logger.info(f"发现 {len(processed_codes)} 只股票已有近期财务指标，将跳过")

        pending_records = [
            r
            for r in records
            if (r.get("ts_code") or r.get("code") or "").split(".")[0]
            not in processed_codes
        ]

        if not pending_records:
            logger.info("所有股票财务指标都已处理完成")
            return

        logger.info(
            f"共需处理 {len(pending_records)} 只股票的财务指标（已跳过 {len(processed_codes)} 只）"
        )

        all_metrics_to_save = []
        total_batches = (len(pending_records) + batch_size - 1) // batch_size

        def _mark_bad_code_immediately(code: str):
            """将异常代码立即写入缓存列表，便于前端/接口即时可见。

            注意：该函数仅更新内存缓存（api_service内部缓存），不会立刻写入数据库。
            """
            try:
                if not code:
                    return
                existing = api_service.get_cached_data("metrics_bad_codes") or []
                if not isinstance(existing, list):
                    existing = []
                merged = sorted(set(existing) | {code})
                api_service.set_cached_data("metrics_bad_codes", merged, ttl=1800)
            except Exception:
                # 缓存失败不影响主流程
                pass

        async def process_batch(batch_records, batch_num):
            """处理一批股票的财务指标"""
            logger.info(f"开始处理批次 {batch_num}/{total_batches}...")
            batch_metrics = []
            bad_codes = []
            for record in batch_records:
                ts_code = record.get("ts_code") or record.get("code")
                if not ts_code:
                    continue

                pure_code = ts_code.split(".")[0]
                if "." not in ts_code:
                    if ts_code.startswith(("0", "3")):
                        ts_code += ".SZ"
                    elif ts_code.startswith("6"):
                        ts_code += ".SH"
                    else:
                        continue

                logger.debug(f"批次 {batch_num}: 获取 {ts_code} 的财务指标")

                pe = pb = roe = roa = debt_ratio = eps = None
                market_cap = current_price = change_pct = volume = None

                try:
                    daily_df = await client.daily_basic(ts_code=ts_code, limit=1)
                    if daily_df is not None and not daily_df.empty:
                        row = daily_df.iloc[0]
                        pe = _safe_float(row.get("pe"))
                        pb = _safe_float(row.get("pb"))
                        market_cap = _safe_float(row.get("total_mv"))
                except Exception as de:
                    logger.debug(f"获取 {ts_code} daily_basic 失败: {de}")
                    # 在获取阶段即预先标记该股票为异常
                    bad_codes.append(ts_code)
                    _mark_bad_code_immediately(ts_code)

                try:
                    fina_df = await client.fina_indicator(ts_code=ts_code, limit=1)
                    if fina_df is not None and not fina_df.empty:
                        frow = fina_df.iloc[0]
                        roe = _safe_float(frow.get("roe"))
                        roa = _safe_float(frow.get("roa"))
                        debt_ratio = _safe_float(frow.get("debt_to_assets"))
                        eps = _safe_float(frow.get("eps_basic"))
                except Exception as fe:
                    logger.debug(f"获取 {ts_code} fina_indicator 失败: {fe}")
                    # 在获取阶段即预先标记该股票为异常
                    bad_codes.append(ts_code)
                    _mark_bad_code_immediately(ts_code)

                try:
                    daily_df = await client.daily(ts_code=ts_code, limit=1)
                    if daily_df is not None and not daily_df.empty:
                        row = daily_df.iloc[0]
                        current_price = _safe_float(row.get("close"))
                        change_pct = _safe_float(row.get("pct_chg"))
                        volume = _safe_float(row.get("vol"))
                except Exception as daily_err:
                    logger.debug(f"获取 {ts_code} daily 失败: {daily_err}")
                    # 在获取阶段即预先标记该股票为异常
                    bad_codes.append(ts_code)
                    _mark_bad_code_immediately(ts_code)

                metrics_data = {
                    "ts_code": ts_code,
                    "pe": pe,
                    "pb": pb,
                    "roe": roe,
                    "roa": roa,
                    "debt_ratio": debt_ratio,
                    "eps": eps,
                    "market_cap": market_cap,
                    "current_price": current_price,
                    "change_pct": change_pct,
                    "volume": volume,
                }
                api_service.set_cached_data(
                    f"stock_metrics_{pure_code}", metrics_data, ttl=1800
                )
                # 立即入库（逐股）
                try:
                    stock_db.save_stock_metric(metrics_data)
                except Exception as se:
                    logger.error(f"逐股保存财务指标失败 {ts_code}: {se}")

                # 异常检测：使用更宽松且更贴近业务的规则
                if is_metrics_anomalous(metrics_data):
                    bad_codes.append(ts_code)
                else:
                    # 如果当前数据正常，从缓存的异常列表中移除此代码，避免误报长期滞留
                    try:
                        existing = (
                            api_service.get_cached_data("metrics_bad_codes") or []
                        )
                        if isinstance(existing, list) and ts_code in existing:
                            updated = [c for c in existing if c != ts_code]
                            api_service.set_cached_data(
                                "metrics_bad_codes", updated, ttl=1800
                            )
                    except Exception:
                        pass

                batch_metrics.append(metrics_data)
                await asyncio.sleep(0.05)

            if batch_metrics:
                all_metrics_to_save.extend(batch_metrics)
                try:
                    saved_count = stock_db.save_stock_metrics(batch_metrics)
                    logger.info(
                        f"批次 {batch_num}/{total_batches} 处理完成, 成功保存 {saved_count} 条财务指标到数据库"
                    )
                except Exception as e:
                    logger.error(f"批次 {batch_num} 保存财务指标失败: {e}")

                if bad_codes:
                    bad_list = sorted(set(bad_codes))
                    logger.warning(
                        f"检测到疑似问题数据（规则命中），建议重试拉取: {', '.join(bad_list)}"
                    )
                    try:
                        # 将本批结果与缓存中的异常列表做并集，避免覆盖丢失
                        existing = (
                            api_service.get_cached_data("metrics_bad_codes") or []
                        )
                        if not isinstance(existing, list):
                            existing = []
                        merged = sorted(set(existing) | set(bad_list))
                        api_service.set_cached_data(
                            "metrics_bad_codes", merged, ttl=1800
                        )
                    except Exception:
                        pass

        batches = [
            pending_records[i : i + batch_size]
            for i in range(0, len(pending_records), batch_size)
        ]
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def process_with_semaphore(batch, batch_num):
            async with semaphore:
                await process_batch(batch, batch_num)

        logger.info(
            f"开始并发处理 {len(batches)} 个批次，每批最多 {batch_size} 只股票，并发数: {concurrent_limit}"
        )
        tasks = [
            process_with_semaphore(batch, i + 1) for i, batch in enumerate(batches)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"全部批次处理完成，共处理 {len(pending_records)} 只股票的财务指标")

    except Exception as e:
        logger.warning(f"批量缓存财务指标失败: {e}")
    finally:
        try:
            # 释放锁
            from webapp.app import api_service as _api_service_final

            _api_service_final.set_cached_data("metrics_caching_lock", False)
        except Exception:
            pass
