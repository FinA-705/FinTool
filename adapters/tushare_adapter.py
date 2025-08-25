"""
Tushare数据源适配器

实现基于Tushare API的A股数据获取功能。
支持股票基础信息、财务数据、市场行情等数据类型。
"""

import asyncio
import pandas as pd
import tushare as ts
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import time
import logging

from .base import BaseAdapter, DataRequest, DataResponse, Market, DataType
from utils.env_config import env_config

try:
    from core.config_manager import CoreConfigManager
except Exception:  # 避免循环依赖导致导入失败
    CoreConfigManager = None


class TushareAdapter(BaseAdapter):
    """
    Tushare数据源适配器

    提供A股市场的全面数据获取能力，包括：
    - 股票基础信息
    - 财务数据
    - 市场行情数据
    - 技术指标数据
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Tushare适配器

        Args:
            config: 配置参数，如果不包含token则从环境变量获取
        """
        # 优先使用传入 config；若缺失则尝试 CoreConfigManager；仍为空再用环境变量
        if "token" not in config:
            # 尝试全局配置管理器
            if CoreConfigManager:
                try:
                    cfg_mgr = CoreConfigManager()
                    app_cfg = cfg_mgr.get_config("application") or {}
                    token_from_cfg = (
                        (app_cfg.get("data_sources", {}) or {})
                        .get("tushare", {})
                        .get("token")
                    )
                    if token_from_cfg:
                        config["token"] = token_from_cfg
                except Exception:
                    pass
            # 环境变量兜底
            if "token" not in config and env_config.tushare_token:
                config["token"] = env_config.tushare_token

        if "baseurl" not in config:
            config["baseurl"] = env_config.tushare_baseurl

        # 设置实例属性
        self.token = config.get("token")
        self.baseurl = config.get("baseurl", "http://api.tushare.pro")

        if not self.token:
            raise ValueError(
                "Tushare token is required. Please set TUSHARE_TOKEN in .env file or provide in config"
            )

        # 设置请求频率限制（根据Tushare权限等级调整）
        self.request_interval = config.get("request_interval", 0.1)  # 默认100ms间隔
        self.last_request_time = 0

        # 调用父类初始化
        super().__init__(config)

    def _get_field_map(self) -> Dict[str, str]:
        """
        获取Tushare字段到标准字段的映射

        Returns:
            字段映射字典
        """
        return {
            # 基础信息字段
            "symbol": "ts_code",  # 股票代码
            "name": "name",  # 股票名称
            "industry": "industry",  # 行业
            "market": "market",  # 市场
            "list_date": "list_date",  # 上市日期
            "area": "area",  # 地域
            # 财务指标字段
            "pe": "pe",  # 市盈率
            "pb": "pb",  # 市净率
            "pe_ttm": "pe_ttm",  # 滚动市盈率
            "ps": "ps",  # 市销率
            "ps_ttm": "ps_ttm",  # 滚动市销率
            "dv_ratio": "dv_ratio",  # 股息率
            "dv_ttm": "dv_ttm",  # 滚动股息率
            "total_share": "total_share",  # 总股本
            "float_share": "float_share",  # 流通股本
            "free_share": "free_share",  # 自由流通股本
            "turnover_rate": "turnover_rate",  # 换手率
            "turnover_rate_f": "turnover_rate_f",  # 自由流通换手率
            "volume_ratio": "volume_ratio",  # 量比
            "pe_ttm": "pe_ttm",  # TTM市盈率
            "pb_mrq": "pb_mrq",  # MRQ市净率
            # 财务数据字段
            "revenue": "total_revenue",  # 营业总收入
            "profit": "n_income",  # 净利润
            "roe": "roe",  # 净资产收益率
            "roa": "roa",  # 总资产收益率
            "gross_margin": "gross_margin",  # 毛利率
            "debt_ratio": "debt_to_assets",  # 资产负债率
            "current_ratio": "current_ratio",  # 流动比率
            "quick_ratio": "quick_ratio",  # 速动比率
            # 市场数据字段
            "trade_date": "trade_date",  # 交易日期
            "open": "open",  # 开盘价
            "high": "high",  # 最高价
            "low": "low",  # 最低价
            "close": "close",  # 收盘价
            "pre_close": "pre_close",  # 前收盘价
            "change": "change",  # 涨跌额
            "pct_chg": "pct_chg",  # 涨跌幅
            "vol": "vol",  # 成交量
            "amount": "amount",  # 成交额
            "market_cap": "total_mv",  # 总市值
            "circ_mv": "circ_mv",  # 流通市值
        }

    def _get_supported_markets(self) -> List[Market]:
        """获取支持的市场"""
        return [Market.A_STOCK]

    def _get_supported_data_types(self) -> List[DataType]:
        """获取支持的数据类型"""
        return [
            DataType.BASIC_INFO,
            DataType.FINANCIAL,
            DataType.MARKET,
            DataType.TECHNICAL,
        ]

    def _init_client(self):
        """初始化Tushare客户端"""
        try:
            # 幂等：如果已初始化则直接返回
            if self._client is not None:
                return
            ts.set_token(self.token)
            self._client = ts.pro_api()
            self.logger.info(f"Tushare客户端初始化成功, 服务器: {self.baseurl}")
        except Exception as e:
            self.logger.error(f"Tushare客户端初始化失败: {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """健康检查：验证 token 有效性 & 基础接口可用性"""
        result: Dict[str, Any] = {
            "adapter": "tushare",
            "token_present": bool(self.token),
            "token_valid": False,
            "stock_basic_access": False,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            self._init_client()
            # 尝试获取一条基础信息（Tushare 不支持 limit=1，需要取head）
            data = self._client.stock_basic(exchange="", list_status="L")
            if not data.empty:
                result["token_valid"] = True
                result["stock_basic_access"] = True
                result["sample"] = data.head(1).to_dict("records")[0]
        except Exception as e:
            result["error"] = str(e)
        return result

    def _validate_symbol(self, symbol: str, market: Optional[Market]) -> bool:
        """
        验证A股股票代码格式

        Args:
            symbol: 股票代码
            market: 市场（此处应为A股）

        Returns:
            是否有效
        """
        if not symbol:
            return False

        # A股代码格式：6位数字 + 后缀
        # 如：000001.SZ, 600000.SH, 300001.SZ, 688001.SH
        import re

        pattern = r"^\d{6}\.(SH|SZ|BJ)$"
        return bool(re.match(pattern, symbol.upper()))

    async def _wait_for_rate_limit(self):
        """等待以满足请求频率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.request_interval:
            wait_time = self.request_interval - time_since_last_request
            await asyncio.sleep(wait_time)

        self.last_request_time = time.time()

    async def _fetch_data(self, request: DataRequest) -> DataResponse:
        """
        从Tushare获取数据

        Args:
            request: 数据请求参数

        Returns:
            数据响应
        """
        try:
            await self._wait_for_rate_limit()

            if request.data_type == DataType.BASIC_INFO:
                data = await self._fetch_basic_info(request)
            elif request.data_type == DataType.FINANCIAL:
                data = await self._fetch_financial_data(request)
            elif request.data_type == DataType.MARKET:
                data = await self._fetch_market_data(request)
            elif request.data_type == DataType.TECHNICAL:
                data = await self._fetch_technical_data(request)
            else:
                return DataResponse(
                    data=pd.DataFrame(),
                    success=False,
                    message=f"不支持的数据类型: {request.data_type.value}",
                )

            return DataResponse(
                data=data,
                success=True,
                message="数据获取成功",
                total_count=len(data) if data is not None else 0,
            )

        except Exception as e:
            self.logger.error(f"Tushare数据获取失败: {str(e)}")
            return DataResponse(
                data=pd.DataFrame(), success=False, message=f"数据获取失败: {str(e)}"
            )

    async def _fetch_basic_info(self, request: DataRequest) -> pd.DataFrame:
        """获取股票基础信息"""

        def _get_basic_info():
            if request.symbols:
                # 获取指定股票的基础信息
                all_data = []
                for symbol in request.symbols:
                    try:
                        data = self._client.stock_basic(ts_code=symbol)
                        if not data.empty:
                            all_data.append(data)
                    except Exception as e:
                        self.logger.warning(f"获取股票 {symbol} 基础信息失败: {str(e)}")

                return (
                    pd.concat(all_data, ignore_index=True)
                    if all_data
                    else pd.DataFrame()
                )
            else:
                # 获取所有A股基础信息，不应用limit限制
                self.logger.info("开始获取所有A股基础信息...")
                data = self._client.stock_basic(exchange="", list_status="L")
                self.logger.info(f"获取到 {len(data)} 条股票基础信息")

                # 只有在明确指定limit时才应用限制
                if request.limit and request.limit > 0:
                    data = data.head(request.limit)
                    self.logger.info(f"应用limit限制，返回 {len(data)} 条数据")

                return data

        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_basic_info)

    async def _fetch_financial_data(self, request: DataRequest) -> pd.DataFrame:
        """获取财务数据"""

        def _get_financial_data():
            all_data = []

            if not request.symbols:
                # 如果没有指定股票，获取最新的财务数据样本
                basic_stocks = self._client.stock_basic(exchange="", list_status="L")
                symbols = basic_stocks["ts_code"].head(request.limit or 100).tolist()
            else:
                symbols = request.symbols

            for symbol in symbols:
                try:
                    # 获取最新财务指标
                    indicator_data = self._client.fina_indicator(
                        ts_code=symbol,
                        start_date=request.start_date,
                        end_date=request.end_date,
                    )

                    # 获取每日指标（市盈率、市净率等）
                    daily_basic = self._client.daily_basic(
                        ts_code=symbol,
                        start_date=request.start_date,
                        end_date=request.end_date,
                    )

                    if not indicator_data.empty and not daily_basic.empty:
                        # 合并数据，取最新的记录
                        latest_indicator = (
                            indicator_data.iloc[0] if not indicator_data.empty else None
                        )
                        latest_daily = (
                            daily_basic.iloc[0] if not daily_basic.empty else None
                        )

                        if latest_indicator is not None and latest_daily is not None:
                            merged_data = {
                                **latest_indicator.to_dict(),
                                **latest_daily.to_dict(),
                            }
                            all_data.append(merged_data)

                except Exception as e:
                    self.logger.warning(f"获取股票 {symbol} 财务数据失败: {str(e)}")

            return pd.DataFrame(all_data) if all_data else pd.DataFrame()

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_financial_data)

    async def _fetch_market_data(self, request: DataRequest) -> pd.DataFrame:
        """获取市场行情数据"""

        def _get_market_data():
            all_data = []

            if not request.symbols:
                # 获取今日所有股票行情
                trade_date = datetime.now().strftime("%Y%m%d")
                data = self._client.daily(trade_date=trade_date)
                if request.limit:
                    data = data.head(request.limit)
                return data

            for symbol in request.symbols:
                try:
                    data = self._client.daily(
                        ts_code=symbol,
                        start_date=request.start_date,
                        end_date=request.end_date,
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    self.logger.warning(f"获取股票 {symbol} 行情数据失败: {str(e)}")

            return (
                pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_market_data)

    async def _fetch_technical_data(self, request: DataRequest) -> pd.DataFrame:
        """获取技术指标数据"""

        def _get_technical_data():
            all_data = []

            if not request.symbols:
                return pd.DataFrame()  # 技术指标需要指定股票

            for symbol in request.symbols:
                try:
                    # 获取每日基本面数据（包含技术指标）
                    data = self._client.daily_basic(
                        ts_code=symbol,
                        start_date=request.start_date,
                        end_date=request.end_date,
                    )
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    self.logger.warning(f"获取股票 {symbol} 技术数据失败: {str(e)}")

            return (
                pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_technical_data)

    def get_stock_list(self, exchange: Optional[str] = None) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            exchange: 交易所代码（SSE, SZSE）

        Returns:
            股票列表数据
        """
        try:
            data = self._client.stock_basic(exchange=exchange or "", list_status="L")
            return data
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {str(e)}")
            return pd.DataFrame()

    def get_trade_calendar(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            交易日历数据
        """
        try:
            data = self._client.trade_cal(
                exchange="SSE", start_date=start_date, end_date=end_date
            )
            return data
        except Exception as e:
            self.logger.error(f"获取交易日历失败: {str(e)}")
            return pd.DataFrame()

    async def test_connection(self) -> tuple[bool, str]:
        """测试Tushare连接"""
        try:
            # 尝试获取少量基础数据
            test_request = DataRequest(data_type=DataType.BASIC_INFO, limit=1)
            response = await self.get_data(test_request)

            if response.success and not response.data.empty:
                return True, "Tushare连接测试成功"
            else:
                return False, f"Tushare连接测试失败: {response.message}"

        except Exception as e:
            return False, f"Tushare连接测试异常: {str(e)}"
