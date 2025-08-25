"""
数据源适配器基类

提供统一的数据源接口，所有数据源适配器都需要继承此基类并实现抽象方法。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import asyncio
import logging
from datetime import datetime, date


class Market(Enum):
    """市场枚举"""

    A_STOCK = "A股"
    US_STOCK = "美股"
    HK_STOCK = "港股"


class DataType(Enum):
    """数据类型枚举"""

    BASIC_INFO = "basic_info"  # 基础信息
    FINANCIAL = "financial"  # 财务数据
    MARKET = "market"  # 市场数据
    TECHNICAL = "technical"  # 技术指标
    NEWS = "news"  # 新闻数据


@dataclass
class DataRequest:
    """数据请求参数"""

    symbols: Optional[List[str]] = None  # 股票代码列表
    market: Optional[Market] = None  # 市场
    data_type: DataType = DataType.BASIC_INFO  # 数据类型
    start_date: Optional[Union[str, date]] = None  # 开始日期
    end_date: Optional[Union[str, date]] = None  # 结束日期
    fields: Optional[List[str]] = None  # 指定字段
    limit: Optional[int] = None  # 返回条数限制
    extra_params: Optional[Dict[str, Any]] = None  # 额外参数


@dataclass
class DataResponse:
    """数据响应结果"""

    data: pd.DataFrame  # 数据内容
    success: bool = True  # 请求是否成功
    message: str = ""  # 响应消息
    total_count: Optional[int] = None  # 总记录数
    request_info: Optional[DataRequest] = None  # 原始请求信息
    source: str = ""  # 数据源名称
    timestamp: Optional[datetime] = None  # 数据时间戳

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BaseAdapter(ABC):
    """
    数据源适配器基类

    所有数据源适配器都必须继承此类并实现抽象方法。
    提供统一的数据获取接口和标准化的数据格式。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 配置参数字典
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.field_map = self._get_field_map()
        self.supported_markets = self._get_supported_markets()
        self.supported_data_types = self._get_supported_data_types()

        # 请求配置
        self.timeout = config.get("timeout", 30)
        self.retry_times = config.get("retry_times", 3)
        self.max_concurrent = config.get("max_concurrent", 10)

        # 初始化客户端
        self._client = None
        self._init_client()

    @property
    def name(self) -> str:
        """适配器名称"""
        return self.__class__.__name__.replace("Adapter", "").lower()

    @abstractmethod
    def _get_field_map(self) -> Dict[str, str]:
        """
        获取字段映射配置

        Returns:
            字段映射字典，格式为 {标准字段名: 数据源字段名}
        """
        pass

    @abstractmethod
    def _get_supported_markets(self) -> List[Market]:
        """
        获取支持的市场列表

        Returns:
            支持的市场枚举列表
        """
        pass

    @abstractmethod
    def _get_supported_data_types(self) -> List[DataType]:
        """
        获取支持的数据类型列表

        Returns:
            支持的数据类型枚举列表
        """
        pass

    @abstractmethod
    def _init_client(self):
        """初始化数据源客户端"""
        pass

    @abstractmethod
    async def _fetch_data(self, request: DataRequest) -> DataResponse:
        """
        从数据源获取原始数据

        Args:
            request: 数据请求参数

        Returns:
            原始数据响应
        """
        pass

    def _validate_request(self, request: DataRequest) -> Tuple[bool, str]:
        """
        验证请求参数

        Args:
            request: 数据请求参数

        Returns:
            (是否有效, 错误信息)
        """
        # 检查市场支持
        if request.market and request.market not in self.supported_markets:
            return False, f"不支持的市场: {request.market.value}"

        # 检查数据类型支持
        if request.data_type not in self.supported_data_types:
            return False, f"不支持的数据类型: {request.data_type.value}"

        # 检查股票代码格式（如果有）
        if request.symbols:
            for symbol in request.symbols:
                if not self._validate_symbol(symbol, request.market):
                    return False, f"无效的股票代码: {symbol}"

        return True, ""

    def _validate_symbol(self, symbol: str, market: Optional[Market]) -> bool:
        """
        验证股票代码格式

        Args:
            symbol: 股票代码
            market: 市场

        Returns:
            是否有效
        """
        # 基础验证：不能为空
        if not symbol or not symbol.strip():
            return False

        # 各市场具体验证逻辑由子类实现
        return True

    def _standardize_data(
        self, data: pd.DataFrame, request: DataRequest
    ) -> pd.DataFrame:
        """
        标准化数据格式

        Args:
            data: 原始数据
            request: 请求参数

        Returns:
            标准化后的数据
        """
        if data.empty:
            return data

        # 字段名映射
        reverse_field_map = {v: k for k, v in self.field_map.items()}
        data = data.rename(columns=reverse_field_map)

        # 数据类型转换
        data = self._convert_data_types(data, request.data_type)

        # 添加元数据列
        data["data_source"] = self.name
        data["update_time"] = datetime.now()

        return data

    def _convert_data_types(
        self, data: pd.DataFrame, data_type: DataType
    ) -> pd.DataFrame:
        """
        转换数据类型

        Args:
            data: 数据
            data_type: 数据类型

        Returns:
            转换后的数据
        """
        # 通用数值字段转换
        numeric_fields = [
            "pe",
            "pb",
            "roe",
            "revenue",
            "profit",
            "debt_ratio",
            "market_cap",
            "price",
            "volume",
            "turnover",
        ]

        for field in numeric_fields:
            if field in data.columns:
                data[field] = pd.to_numeric(data[field], errors="coerce")

        # 日期字段转换
        date_fields = ["trade_date", "report_date", "list_date"]
        for field in date_fields:
            if field in data.columns:
                data[field] = pd.to_datetime(data[field], errors="coerce")

        return data

    async def get_data(self, request: DataRequest) -> DataResponse:
        """
        获取数据的主入口方法

        Args:
            request: 数据请求参数

        Returns:
            标准化的数据响应
        """
        # 参数验证
        is_valid, error_msg = self._validate_request(request)
        if not is_valid:
            return DataResponse(
                data=pd.DataFrame(),
                success=False,
                message=error_msg,
                request_info=request,
                source=self.name,
            )

        try:
            # 获取原始数据
            response = await self._fetch_data(request)

            if response.success and not response.data.empty:
                # 标准化数据
                response.data = self._standardize_data(response.data, request)
                response.source = self.name
                response.request_info = request

                self.logger.info(f"成功获取数据: {len(response.data)} 条记录")
            else:
                self.logger.warning(f"获取数据失败或为空: {response.message}")

            return response

        except Exception as e:
            self.logger.error(f"获取数据异常: {str(e)}")
            return DataResponse(
                data=pd.DataFrame(),
                success=False,
                message=f"获取数据异常: {str(e)}",
                request_info=request,
                source=self.name,
            )

    async def get_batch_data(self, requests: List[DataRequest]) -> List[DataResponse]:
        """
        批量获取数据

        Args:
            requests: 数据请求列表

        Returns:
            数据响应列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def limited_get_data(request):
            async with semaphore:
                return await self.get_data(request)

        tasks = [limited_get_data(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.append(
                    DataResponse(
                        data=pd.DataFrame(),
                        success=False,
                        message=f"批量请求异常: {str(response)}",
                        request_info=requests[i],
                        source=self.name,
                    )
                )
            else:
                results.append(response)

        return results

    def get_field_mapping(self) -> Dict[str, str]:
        """
        获取字段映射配置

        Returns:
            字段映射字典
        """
        return self.field_map.copy()

    def get_supported_info(self) -> Dict[str, Any]:
        """
        获取适配器支持信息

        Returns:
            支持信息字典
        """
        return {
            "name": self.name,
            "supported_markets": [market.value for market in self.supported_markets],
            "supported_data_types": [dt.value for dt in self.supported_data_types],
            "field_mapping": self.field_map,
            "config": {
                k: v
                for k, v in self.config.items()
                if "key" not in k.lower() and "token" not in k.lower()
            },
        }

    async def test_connection(self) -> Tuple[bool, str]:
        """
        测试连接

        Returns:
            (连接是否成功, 测试信息)
        """
        try:
            test_request = DataRequest(data_type=DataType.BASIC_INFO, limit=1)
            response = await self.get_data(test_request)
            return response.success, response.message
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, markets={len(self.supported_markets)})"
