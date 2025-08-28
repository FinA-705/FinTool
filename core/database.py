"""
数据库管理模块
提供股票数据的持久化存储和缓存功能
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from utils.logger import get_logger

logger = get_logger("database")


class StockDatabase:
    """股票数据库管理器"""

    def __init__(self, db_path: str = "cache/stocks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_basic (
                    ts_code TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    area TEXT,
                    industry TEXT,
                    market TEXT,
                    list_date TEXT,
                    fullname TEXT,
                    enname TEXT,
                    cnspell TEXT,
                    exchange TEXT,
                    curr_type TEXT,
                    list_status TEXT,
                    delist_date TEXT,
                    is_hs TEXT,
                    act_name TEXT,
                    act_ent_type TEXT,
                    data_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_daily (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_code TEXT,
                    trade_date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    pre_close REAL,
                    change REAL,
                    pct_chg REAL,
                    vol REAL,
                    amount REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ts_code, trade_date)
                )
            """
            )

            # 创建财务指标表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_metrics (
                    ts_code TEXT PRIMARY KEY,
                    pe REAL,
                    pb REAL,
                    roe REAL,
                    roa REAL,
                    debt_ratio REAL,
                    eps REAL,
                    market_cap REAL,
                    current_price REAL,
                    change_pct REAL,
                    volume REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建财务指标详细数据表
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_indicators (
                    stock_code TEXT PRIMARY KEY,
                    data_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_basic_symbol ON stock_basic(symbol);
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_basic_name ON stock_basic(name);
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_daily_ts_code ON stock_daily(ts_code);
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_daily_trade_date ON stock_daily(trade_date);
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_metrics_ts_code ON stock_metrics(ts_code);
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_metrics_updated_at ON stock_metrics(updated_at);
            """
            )

            conn.commit()
            logger.info("数据库初始化完成")

    def save_stock_basic_data(self, data: List[Dict[str, Any]]) -> int:
        """
        保存股票基础信息到数据库

        Args:
            data: 股票基础信息列表

        Returns:
            保存的记录数
        """
        if not data:
            return 0

        saved_count = 0
        with sqlite3.connect(self.db_path) as conn:
            for record in data:
                try:
                    # 提取标准字段并转换数据类型
                    ts_code = record.get("ts_code") or record.get("code")
                    symbol = record.get("symbol") or ts_code
                    name = record.get("name") or record.get("company_name", "")
                    area = record.get("area", "")
                    industry = record.get("industry", "")
                    market = record.get("market", "")

                    # 处理日期字段，将Timestamp转换为字符串
                    list_date = record.get("list_date", "")
                    if hasattr(list_date, "strftime"):
                        list_date = list_date.strftime("%Y-%m-%d")
                    elif list_date is None:
                        list_date = ""
                    else:
                        list_date = str(list_date)

                    delist_date = record.get("delist_date", "")
                    if hasattr(delist_date, "strftime"):
                        delist_date = delist_date.strftime("%Y-%m-%d")
                    elif delist_date is None:
                        delist_date = ""
                    else:
                        delist_date = str(delist_date)

                    # 其他字段的类型转换
                    def safe_str(value):
                        if value is None:
                            return ""
                        if hasattr(value, "strftime"):  # Timestamp对象
                            return value.strftime("%Y-%m-%d %H:%M:%S")
                        return str(value)

                    # 其他字段作为JSON存储
                    data_json = json.dumps(record, ensure_ascii=False, default=safe_str)

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO stock_basic
                        (ts_code, symbol, name, area, industry, market, list_date,
                         fullname, enname, cnspell, exchange, curr_type, list_status,
                         delist_date, is_hs, act_name, act_ent_type, data_json, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                        (
                            ts_code,
                            symbol,
                            name,
                            area,
                            industry,
                            market,
                            list_date,
                            safe_str(record.get("fullname", "")),
                            safe_str(record.get("enname", "")),
                            safe_str(record.get("cnspell", "")),
                            safe_str(record.get("exchange", "")),
                            safe_str(record.get("curr_type", "")),
                            safe_str(record.get("list_status", "")),
                            delist_date,
                            safe_str(record.get("is_hs", "")),
                            safe_str(record.get("act_name", "")),
                            safe_str(record.get("act_ent_type", "")),
                            data_json,
                        ),
                    )
                    saved_count += 1

                except Exception as e:
                    logger.error(
                        f"Error saving stock record {record.get('ts_code', 'unknown')}: {e}"
                    )
                    continue

        return saved_count

        logger.info(f"成功保存 {saved_count} 条股票基础信息到数据库")
        return saved_count

    def get_stock_basic_data(
        self,
        symbols: Optional[List[str]] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None,
        cache_hours: int = 24,
        log_results: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        从数据库获取股票基础信息

        Args:
            symbols: 股票代码列表
            market: 市场类型
            limit: 返回数量限制
            cache_hours: 缓存有效期（小时）
            log_results: 是否打印日志
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 构建查询条件
            where_conditions = []
            params = []

            # 检查缓存有效期
            cutoff_time = datetime.now() - timedelta(hours=cache_hours)
            where_conditions.append("updated_at > ?")
            # 使用与 SQLite CURRENT_TIMESTAMP 一致的格式，避免包含 'T' 导致字符串比较失败
            params.append(cutoff_time.strftime("%Y-%m-%d %H:%M:%S"))

            if symbols:
                placeholders = ",".join("?" * len(symbols))
                where_conditions.append(f"ts_code IN ({placeholders})")
                params.extend(symbols)

            if market:
                where_conditions.append("market = ?")
                params.append(market)

            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

            # 首先，检查是否有任何有效数据
            count_query = f"SELECT COUNT(*) FROM stock_basic WHERE {where_clause}"
            count_cursor = conn.execute(count_query, params)
            total_valid_records = count_cursor.fetchone()[0]

            if log_results:
                logger.info(f"数据库中有效的股票记录数: {total_valid_records}")

            if total_valid_records == 0:
                if log_results:
                    logger.warning("数据库中没有找到有效的股票缓存数据。")
                # 如果没有有效数据，则移除 updated_at 条件，尝试获取旧数据
                where_conditions.pop(0)
                params.pop(0)
                where_clause = (
                    " AND ".join(where_conditions) if where_conditions else "1=1"
                )

            query = f"""
                SELECT * FROM stock_basic
                WHERE {where_clause}
                ORDER BY ts_code
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # 转换为字典列表
            results = []
            for row in rows:
                record = dict(row)
                # 如果有JSON数据，尝试合并
                if record.get("data_json"):
                    try:
                        json_data = json.loads(record["data_json"])
                        record.update(json_data)
                    except json.JSONDecodeError:
                        pass  # 忽略无法解析的JSON
                results.append(record)

            if log_results:
                logger.info(f"从数据库返回 {len(results)} 条股票数据")
            return results

    def is_cache_valid(self, cache_hours: int = 24) -> bool:
        """
        检查数据库缓存是否有效

        Args:
            cache_hours: 缓存有效期（小时）

        Returns:
            True if cache is valid
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT MAX(updated_at) FROM stock_basic")
            latest_update_str = cursor.fetchone()[0]

            if not latest_update_str:
                return False

            latest_update = datetime.fromisoformat(latest_update_str)
            return latest_update > datetime.now() - timedelta(hours=cache_hours)

    def get_all_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT ts_code FROM stock_basic")
            return [row[0] for row in cursor.fetchall()]

    def save_financial_indicators(self, stock_code: str, indicators: Dict[str, Any]):
        """
        保存股票财务指标

        Args:
            stock_code: 股票代码
            indicators: 财务指标字典
        """
        with sqlite3.connect(self.db_path) as conn:
            # 检查是否已存在该股票的记录
            cursor = conn.execute(
                "SELECT 1 FROM financial_indicators WHERE stock_code = ?", (stock_code,)
            )
            exists = cursor.fetchone()

            # 将字典转换为JSON字符串
            indicators_json = json.dumps(indicators, ensure_ascii=False)

            if exists:
                # 更新现有记录
                conn.execute(
                    """
                    UPDATE financial_indicators
                    SET data_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE stock_code = ?
                    """,
                    (indicators_json, stock_code),
                )
            else:
                # 插入新记录
                conn.execute(
                    """
                    INSERT INTO financial_indicators (stock_code, data_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (stock_code, indicators_json),
                )
            conn.commit()

    def get_financial_indicators(
        self, stock_codes: List[str], cache_days: int = 90
    ) -> Dict[str, Dict[str, Any]]:
        """
        从数据库获取股票财务指标

        Args:
            stock_codes: 股票代码列表
            cache_days: 缓存有效期（天数）

        Returns:
            财务指标字典，键为股票代码
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            results = {}

            # 计算缓存有效期
            cutoff_date = datetime.now() - timedelta(days=cache_days)

            # 构建查询
            placeholders = ",".join("?" * len(stock_codes))
            query = f"""
                SELECT stock_code, data_json
                FROM financial_indicators
                WHERE stock_code IN ({placeholders}) AND updated_at > ?
            """
            # 与 SQLite 的 TIMESTAMP 字符串格式保持一致
            params = stock_codes + [cutoff_date.strftime("%Y-%m-%d %H:%M:%S")]

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            for row in rows:
                try:
                    results[row["stock_code"]] = json.loads(row["data_json"])
                except json.JSONDecodeError:
                    logger.warning(
                        f"无法解析股票 {row['stock_code']} 的财务指标JSON数据"
                    )

            logger.info(f"从数据库获取到 {len(results)} 条财务指标数据")
            return results

    def get_stocks_without_recent_indicators(
        self, all_codes: List[str], cache_days: int = 90
    ) -> List[str]:
        """
        获取没有近期财务指标的股票

        Args:
            all_codes: 所有股票代码列表
            cache_days: 缓存有效期（天数）

        Returns:
            需要更新的股票代码列表
        """
        with sqlite3.connect(self.db_path) as conn:
            # 计算缓存有效期
            cutoff_date = datetime.now() - timedelta(days=cache_days)

            # 查询已有近期指标的股票
            placeholders = ",".join("?" * len(all_codes))
            query = f"""
                SELECT DISTINCT stock_code
                FROM financial_indicators
                WHERE stock_code IN ({placeholders}) AND updated_at > ?
            """
            # 与 SQLite 的 TIMESTAMP 字符串格式保持一致
            params = all_codes + [cutoff_date.strftime("%Y-%m-%d %H:%M:%S")]

            cursor = conn.execute(query, params)
            existing_codes = {row[0] for row in cursor.fetchall()}

            logger.info(f"发现 {len(existing_codes)} 只股票已有近期财务指标，将跳过")

            # 返回需要更新的股票列表
            return [code for code in all_codes if code not in existing_codes]

    def get_stock_metrics(
        self, symbols: Optional[List[str]] = None, cache_hours: int = 1
    ) -> Dict[str, Any]:
        """
        获取股票的财务指标（从 stock_metrics 表）。

        说明：本方法返回的键为“纯代码”（不带 .SH/.SZ 后缀），
        以便与调用方的处理逻辑一致（调用方通常以纯代码去重）。

        Args:
            symbols: 纯代码列表（如 000001），如果为 None 则获取全部
            cache_hours: 缓存有效期（小时）

        Returns:
            一个字典，键是纯代码，值是财务指标字典
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cutoff_time = datetime.now() - timedelta(hours=cache_hours)

            # 直接按时间过滤，避免在 SQL 中处理后缀/纯代码匹配的复杂性
            query = (
                "SELECT ts_code, pe, pb, roe, roa, debt_ratio, eps, market_cap, "
                "current_price, change_pct, volume FROM stock_metrics WHERE updated_at > ?"
            )
            # 使用与 SQLite CURRENT_TIMESTAMP 一致的格式
            params = [cutoff_time.strftime("%Y-%m-%d %H:%M:%S")]

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            sym_set = set(s.upper().split(".")[0] for s in symbols) if symbols else None
            metrics: Dict[str, Any] = {}
            for row in rows:
                ts_code = row["ts_code"] or ""
                pure = ts_code.split(".")[0].upper()
                if sym_set is not None and pure not in sym_set:
                    continue
                metrics[pure] = {
                    "ts_code": ts_code,
                    "pe": row["pe"],
                    "pb": row["pb"],
                    "roe": row["roe"],
                    "roa": row["roa"],
                    "debt_ratio": row["debt_ratio"],
                    "eps": row["eps"],
                    "market_cap": row["market_cap"],
                    "current_price": row["current_price"],
                    "change_pct": row["change_pct"],
                    "volume": row["volume"],
                }
            return metrics

    def save_stock_metric(self, metric: Dict[str, Any]) -> int:
        """
        保存单只股票的财务指标（逐股、立即入库）。

        Args:
            metric: 指标字典，包含 ts_code, pe, pb, roe, roa, debt_ratio, eps,
                    market_cap, current_price, change_pct, volume

        Returns:
            成功保存的条数（0或1）
        """

        def _safe_float(x):
            try:
                if x in (None, ""):
                    return None
                return float(x)
            except Exception:
                return None

        ts_code = metric.get("ts_code") or metric.get("code")
        if not ts_code:
            logger.error("save_stock_metric: 缺少 ts_code，跳过保存")
            return 0

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO stock_metrics
                (ts_code, pe, pb, roe, roa, debt_ratio, eps, market_cap,
                 current_price, change_pct, volume, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(ts_code) DO UPDATE SET
                    pe=excluded.pe,
                    pb=excluded.pb,
                    roe=excluded.roe,
                    roa=excluded.roa,
                    debt_ratio=excluded.debt_ratio,
                    eps=excluded.eps,
                    market_cap=excluded.market_cap,
                    current_price=excluded.current_price,
                    change_pct=excluded.change_pct,
                    volume=excluded.volume,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    ts_code,
                    _safe_float(metric.get("pe")),
                    _safe_float(metric.get("pb")),
                    _safe_float(metric.get("roe")),
                    _safe_float(metric.get("roa")),
                    _safe_float(metric.get("debt_ratio")),
                    _safe_float(metric.get("eps")),
                    _safe_float(metric.get("market_cap")),
                    _safe_float(metric.get("current_price")),
                    _safe_float(metric.get("change_pct")),
                    _safe_float(metric.get("volume")),
                ),
            )
            return 1

    def save_stock_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """
        批量保存股票财务指标（向后兼容原有批量用法）。

        Args:
            metrics: 指标字典列表

        Returns:
            成功保存的条数
        """
        if not metrics:
            return 0
        saved = 0
        with sqlite3.connect(self.db_path) as conn:
            for metric in metrics:
                try:

                    def _safe_float(x):
                        try:
                            if x in (None, ""):
                                return None
                            return float(x)
                        except Exception:
                            return None

                    ts_code = metric.get("ts_code") or metric.get("code")
                    if not ts_code:
                        continue

                    conn.execute(
                        """
                        INSERT INTO stock_metrics
                        (ts_code, pe, pb, roe, roa, debt_ratio, eps, market_cap,
                         current_price, change_pct, volume, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(ts_code) DO UPDATE SET
                            pe=excluded.pe,
                            pb=excluded.pb,
                            roe=excluded.roe,
                            roa=excluded.roa,
                            debt_ratio=excluded.debt_ratio,
                            eps=excluded.eps,
                            market_cap=excluded.market_cap,
                            current_price=excluded.current_price,
                            change_pct=excluded.change_pct,
                            volume=excluded.volume,
                            updated_at=CURRENT_TIMESTAMP
                        """,
                        (
                            ts_code,
                            _safe_float(metric.get("pe")),
                            _safe_float(metric.get("pb")),
                            _safe_float(metric.get("roe")),
                            _safe_float(metric.get("roa")),
                            _safe_float(metric.get("debt_ratio")),
                            _safe_float(metric.get("eps")),
                            _safe_float(metric.get("market_cap")),
                            _safe_float(metric.get("current_price")),
                            _safe_float(metric.get("change_pct")),
                            _safe_float(metric.get("volume")),
                        ),
                    )
                    saved += 1
                except Exception as e:
                    logger.error(
                        f"保存指标失败 {metric.get('ts_code', 'unknown')}: {e}"
                    )
                    continue
        return saved

    def clear_cache(self) -> None:
        """
        清空与股票缓存相关的数据库表。

        这个方法用于在需要时完全清除本地持久化的缓存数据，
        包括基础信息、日线数据、财务指标和指标详细表。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM stock_basic")
                cursor.execute("DELETE FROM stock_daily")
                cursor.execute("DELETE FROM stock_metrics")
                cursor.execute("DELETE FROM financial_indicators")
                conn.commit()
                # 释放空间
                cursor.execute("VACUUM")
            logger.info("本地数据库缓存已清除（所有相关表已删除数据并已 VACUUM）")
        except Exception as e:
            logger.error(f"清除数据库缓存时发生错误: {e}")
            raise


# 创建一个单例实例供其他模块使用
stock_db = StockDatabase()
