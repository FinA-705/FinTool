"""
Yahoo Finance数据源适配器

实现基于yfinance库的全球股票数据获取功能。
支持美股、港股等国际市场数据。
"""

import asyncio
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import logging
import re

from .base import BaseAdapter, DataRequest, DataResponse, Market, DataType


class YFinanceAdapter(BaseAdapter):
    """
    Yahoo Finance数据源适配器

    提供全球股票市场数据获取能力，包括：
    - 股票基础信息
    - 历史行情数据
    - 财务数据（有限）
    - 实时行情数据
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Yahoo Finance适配器

        Args:
            config: 配置参数
        """
        super().__init__(config)
        # Yahoo Finance不需要API密钥

    def _get_field_map(self) -> Dict[str, str]:
        """
        获取Yahoo Finance字段到标准字段的映射

        Returns:
            字段映射字典
        """
        return {
            # 基础信息字段
            "symbol": "symbol",
            "name": "shortName",
            "long_name": "longName",
            "industry": "industry",
            "sector": "sector",
            "country": "country",
            "currency": "currency",
            "market_cap": "marketCap",
            "enterprise_value": "enterpriseValue",
            "shares_outstanding": "sharesOutstanding",
            "float_shares": "floatShares",
            # 估值指标
            "pe": "trailingPE",
            "forward_pe": "forwardPE",
            "pb": "priceToBook",
            "ps": "priceToSalesTrailing12Months",
            "peg": "pegRatio",
            "ev_revenue": "enterpriseToRevenue",
            "ev_ebitda": "enterpriseToEbitda",
            # 财务指标
            "revenue": "totalRevenue",
            "profit": "netIncomeToCommon",
            "roe": "returnOnEquity",
            "roa": "returnOnAssets",
            "gross_margin": "grossMargins",
            "operating_margin": "operatingMargins",
            "profit_margin": "profitMargins",
            "debt_ratio": "debtToEquity",
            "current_ratio": "currentRatio",
            "quick_ratio": "quickRatio",
            # 分红相关
            "dividend_yield": "dividendYield",
            "dividend_rate": "dividendRate",
            "payout_ratio": "payoutRatio",
            # 市场数据字段
            "trade_date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "adj_close": "Adj Close",
            "volume": "Volume",
            # 其他指标
            "beta": "beta",
            "week_52_high": "52WeekHigh",
            "week_52_low": "52WeekLow",
            "avg_volume": "averageVolume",
            "avg_volume_10day": "averageVolume10days",
        }

    def _get_supported_markets(self) -> List[Market]:
        """获取支持的市场"""
        return [Market.US_STOCK, Market.HK_STOCK]

    def _get_supported_data_types(self) -> List[DataType]:
        """获取支持的数据类型"""
        return [DataType.BASIC_INFO, DataType.FINANCIAL, DataType.MARKET]

    def _init_client(self):
        """初始化Yahoo Finance客户端"""
        # Yahoo Finance不需要特殊初始化
        self._client = yf
        self.logger.info("Yahoo Finance客户端初始化成功")

    def _validate_symbol(self, symbol: str, market: Optional[Market]) -> bool:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码
            market: 市场

        Returns:
            是否有效
        """
        if not symbol:
            return False

        if market == Market.US_STOCK:
            # 美股代码：1-5个字母，可能包含点号
            pattern = r"^[A-Z]{1,5}(\.[A-Z])?$"
            return bool(re.match(pattern, symbol.upper()))
        elif market == Market.HK_STOCK:
            # 港股代码：4位数字 + .HK后缀
            pattern = r"^\d{4}\.HK$"
            return bool(re.match(pattern, symbol.upper()))
        else:
            # 其他市场，基础验证
            return len(symbol) > 0

    async def _fetch_data(self, request: DataRequest) -> DataResponse:
        """
        从Yahoo Finance获取数据

        Args:
            request: 数据请求参数

        Returns:
            数据响应
        """
        try:
            if request.data_type == DataType.BASIC_INFO:
                data = await self._fetch_basic_info(request)
            elif request.data_type == DataType.FINANCIAL:
                data = await self._fetch_financial_data(request)
            elif request.data_type == DataType.MARKET:
                data = await self._fetch_market_data(request)
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
            self.logger.error(f"Yahoo Finance数据获取失败: {str(e)}")
            return DataResponse(
                data=pd.DataFrame(), success=False, message=f"数据获取失败: {str(e)}"
            )

    async def _fetch_basic_info(self, request: DataRequest) -> pd.DataFrame:
        """获取股票基础信息"""

        def _get_basic_info():
            all_data = []

            if not request.symbols:
                # Yahoo Finance无法直接获取所有股票列表
                # 返回空DataFrame，建议用户提供具体股票代码
                return pd.DataFrame()

            for symbol in request.symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info

                    if info and "symbol" in info:
                        # 添加symbol字段确保数据完整性
                        info["symbol"] = symbol
                        all_data.append(info)

                except Exception as e:
                    self.logger.warning(f"获取股票 {symbol} 基础信息失败: {str(e)}")

            return pd.DataFrame(all_data) if all_data else pd.DataFrame()

        # 在线程池中执行同步操作
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_basic_info)

    async def _fetch_financial_data(self, request: DataRequest) -> pd.DataFrame:
        """获取财务数据"""

        def _get_financial_data():
            all_data = []

            if not request.symbols:
                return pd.DataFrame()

            for symbol in request.symbols:
                try:
                    ticker = yf.Ticker(symbol)

                    # 获取基础财务信息
                    info = ticker.info
                    if info:
                        # 提取财务相关字段
                        financial_data = {
                            "symbol": symbol,
                            "marketCap": info.get("marketCap"),
                            "enterpriseValue": info.get("enterpriseValue"),
                            "trailingPE": info.get("trailingPE"),
                            "forwardPE": info.get("forwardPE"),
                            "priceToBook": info.get("priceToBook"),
                            "priceToSalesTrailing12Months": info.get(
                                "priceToSalesTrailing12Months"
                            ),
                            "returnOnEquity": info.get("returnOnEquity"),
                            "returnOnAssets": info.get("returnOnAssets"),
                            "grossMargins": info.get("grossMargins"),
                            "operatingMargins": info.get("operatingMargins"),
                            "profitMargins": info.get("profitMargins"),
                            "debtToEquity": info.get("debtToEquity"),
                            "currentRatio": info.get("currentRatio"),
                            "quickRatio": info.get("quickRatio"),
                            "dividendYield": info.get("dividendYield"),
                            "payoutRatio": info.get("payoutRatio"),
                            "beta": info.get("beta"),
                        }
                        all_data.append(financial_data)

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
                return pd.DataFrame()

            # 设置时间范围
            if request.start_date and request.end_date:
                start_date = request.start_date
                end_date = request.end_date
            else:
                # 默认获取最近30天数据
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)

            for symbol in request.symbols:
                try:
                    ticker = yf.Ticker(symbol)

                    # 获取历史数据
                    hist_data = ticker.history(start=start_date, end=end_date)

                    if not hist_data.empty:
                        # 重置索引，将日期作为列
                        hist_data.reset_index(inplace=True)
                        hist_data["symbol"] = symbol
                        all_data.append(hist_data)

                except Exception as e:
                    self.logger.warning(f"获取股票 {symbol} 行情数据失败: {str(e)}")

            return (
                pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_market_data)

    def get_real_time_price(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取实时价格数据

        Args:
            symbols: 股票代码列表

        Returns:
            实时价格数据
        """
        try:
            if len(symbols) == 1:
                ticker = yf.Ticker(symbols[0])
                data = ticker.history(period="1d", interval="1m").tail(1)
                data["symbol"] = symbols[0]
                return data
            else:
                # 批量获取
                tickers = yf.Tickers(" ".join(symbols))
                all_data = []

                for symbol in symbols:
                    try:
                        data = (
                            tickers.tickers[symbol]
                            .history(period="1d", interval="1m")
                            .tail(1)
                        )
                        if not data.empty:
                            data["symbol"] = symbol
                            all_data.append(data)
                    except Exception as e:
                        self.logger.warning(f"获取 {symbol} 实时价格失败: {str(e)}")

                return (
                    pd.concat(all_data, ignore_index=True)
                    if all_data
                    else pd.DataFrame()
                )

        except Exception as e:
            self.logger.error(f"获取实时价格失败: {str(e)}")
            return pd.DataFrame()

    async def test_connection(self) -> tuple[bool, str]:
        """测试Yahoo Finance连接"""
        try:
            # 测试获取苹果公司股票信息
            test_request = DataRequest(symbols=["AAPL"], data_type=DataType.BASIC_INFO)
            response = await self.get_data(test_request)

            if response.success and not response.data.empty:
                return True, "Yahoo Finance连接测试成功"
            else:
                return False, f"Yahoo Finance连接测试失败: {response.message}"

        except Exception as e:
            return False, f"Yahoo Finance连接测试异常: {str(e)}"
