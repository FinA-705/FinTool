"""
数据源适配器工厂

提供统一的适配器创建和管理功能。
支持动态注册和创建各种数据源适配器。
"""

from typing import Dict, Type, Any, List, Optional
import logging
from .base import BaseAdapter, Market
from .tushare_adapter import TushareAdapter
from .yfinance_adapter import YFinanceAdapter


class AdapterFactory:
    """
    数据源适配器工厂类

    负责创建和管理各种数据源适配器，提供统一的访问接口。
    """

    # 注册的适配器类
    _adapters: Dict[str, Type[BaseAdapter]] = {
        "tushare": TushareAdapter,
        "yfinance": YFinanceAdapter,
    }

    # 市场到默认适配器的映射
    _market_adapters: Dict[Market, List[str]] = {
        Market.A_STOCK: ["tushare"],
        Market.US_STOCK: ["yfinance"],
        Market.HK_STOCK: ["yfinance"],
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._instances: Dict[str, BaseAdapter] = {}

    @classmethod
    def register_adapter(cls, name: str, adapter_class: Type[BaseAdapter]):
        """
        注册新的适配器类

        Args:
            name: 适配器名称
            adapter_class: 适配器类
        """
        cls._adapters[name] = adapter_class
        logging.getLogger(cls.__name__).info(f"注册适配器: {name}")

    @classmethod
    def get_available_adapters(cls) -> List[str]:
        """
        获取所有可用的适配器名称

        Returns:
            适配器名称列表
        """
        return list(cls._adapters.keys())

    @classmethod
    def get_adapters_for_market(cls, market: Market) -> List[str]:
        """
        获取支持指定市场的适配器

        Args:
            market: 市场枚举

        Returns:
            适配器名称列表
        """
        return cls._market_adapters.get(market, [])

    def create_adapter(self, name: str, config: Dict[str, Any]) -> BaseAdapter:
        """
        创建适配器实例

        Args:
            name: 适配器名称
            config: 配置参数

        Returns:
            适配器实例

        Raises:
            ValueError: 当适配器不存在时
        """
        if name not in self._adapters:
            raise ValueError(
                f"未知的适配器: {name}. 可用适配器: {list(self._adapters.keys())}"
            )

        try:
            adapter_class = self._adapters[name]
            adapter = adapter_class(config)
            self.logger.info(f"成功创建适配器: {name}")
            return adapter
        except Exception as e:
            self.logger.error(f"创建适配器 {name} 失败: {str(e)}")
            raise

    def get_or_create_adapter(self, name: str, config: Dict[str, Any]) -> BaseAdapter:
        """
        获取或创建适配器实例（单例模式）

        Args:
            name: 适配器名称
            config: 配置参数

        Returns:
            适配器实例
        """
        if name not in self._instances:
            self._instances[name] = self.create_adapter(name, config)
        return self._instances[name]

    def create_market_adapters(
        self, market: Market, configs: Dict[str, Dict[str, Any]]
    ) -> List[BaseAdapter]:
        """
        创建指定市场的所有适配器

        Args:
            market: 市场枚举
            configs: 各适配器的配置字典

        Returns:
            适配器实例列表
        """
        adapters = []
        adapter_names = self.get_adapters_for_market(market)

        for name in adapter_names:
            if name in configs:
                try:
                    adapter = self.create_adapter(name, configs[name])
                    adapters.append(adapter)
                except Exception as e:
                    self.logger.error(
                        f"创建市场 {market.value} 的适配器 {name} 失败: {str(e)}"
                    )
            else:
                self.logger.warning(f"缺少适配器 {name} 的配置")

        return adapters

    def get_adapter_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取适配器信息

        Args:
            name: 适配器名称

        Returns:
            适配器信息字典，如果不存在则返回None
        """
        if name not in self._adapters:
            return None

        adapter_class = self._adapters[name]

        # 尝试创建临时实例获取信息（使用空配置）
        try:
            temp_config = {}
            if name == "tushare":
                temp_config = {"token": "dummy_token"}

            temp_adapter = adapter_class(temp_config)
            return temp_adapter.get_supported_info()
        except Exception:
            # 如果无法创建实例，返回基础信息
            return {
                "name": name,
                "class": adapter_class.__name__,
                "module": adapter_class.__module__,
                "doc": adapter_class.__doc__,
            }

    def get_all_adapters_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有适配器的信息

        Returns:
            所有适配器信息字典
        """
        result = {}
        for name in self._adapters.keys():
            info = self.get_adapter_info(name)
            if info is not None:
                result[name] = info
        return result

    async def test_all_adapters(
        self, configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, tuple[bool, str]]:
        """
        测试所有适配器的连接

        Args:
            configs: 各适配器的配置字典

        Returns:
            测试结果字典 {适配器名称: (是否成功, 消息)}
        """
        results = {}

        for name in self._adapters.keys():
            if name in configs:
                try:
                    adapter = self.create_adapter(name, configs[name])
                    success, message = await adapter.test_connection()
                    results[name] = (success, message)
                except Exception as e:
                    results[name] = (False, f"创建适配器失败: {str(e)}")
            else:
                results[name] = (False, "缺少配置")

        return results

    def clear_instances(self):
        """清除所有适配器实例"""
        self._instances.clear()
        self.logger.info("已清除所有适配器实例")

    def __repr__(self) -> str:
        return f"AdapterFactory(adapters={len(self._adapters)}, instances={len(self._instances)})"


# 全局工厂实例
adapter_factory = AdapterFactory()
