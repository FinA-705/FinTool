"""
策略工厂模块

负责创建和管理不同类型的投资策略实例，支持策略插件扩展。
"""

from typing import Dict, Type, Optional, List
import logging
from abc import ABC, abstractmethod

from .base_strategy import BaseStrategy, StrategyConfig
from .schloss_strategy import SchlossStrategy
from .config_manager import ConfigManager


class StrategyFactory:
    """策略工厂类"""

    # 注册的策略类
    _strategies: Dict[str, Type[BaseStrategy]] = {
        "schloss": SchlossStrategy,
        "walter_schloss": SchlossStrategy,  # 别名
        "value": SchlossStrategy,  # 别名
    }

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[BaseStrategy]) -> None:
        """
        注册新的策略类

        Args:
            name: 策略名称
            strategy_class: 策略类
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"策略类 {strategy_class} 必须继承自 BaseStrategy")

        cls._strategies[name.lower()] = strategy_class
        logging.info(f"策略已注册: {name}")

    @classmethod
    def unregister_strategy(cls, name: str) -> None:
        """
        取消注册策略

        Args:
            name: 策略名称
        """
        name_lower = name.lower()
        if name_lower in cls._strategies:
            del cls._strategies[name_lower]
            logging.info(f"策略已取消注册: {name}")

    @classmethod
    def create_strategy(
        cls, name: str, config: Optional[StrategyConfig] = None
    ) -> BaseStrategy:
        """
        创建策略实例

        Args:
            name: 策略名称
            config: 策略配置，如果为None则使用默认配置

        Returns:
            BaseStrategy: 策略实例
        """
        name_lower = name.lower()

        if name_lower not in cls._strategies:
            available_strategies = list(cls._strategies.keys())
            raise ValueError(f"未知策略: {name}. 可用策略: {available_strategies}")

        strategy_class = cls._strategies[name_lower]

        try:
            strategy = strategy_class(config)
            logging.info(f"策略实例已创建: {name} ({strategy_class.__name__})")
            return strategy
        except Exception as e:
            logging.error(f"创建策略实例失败: {name}, 错误: {e}")
            raise

    @classmethod
    def create_strategy_with_config_file(
        cls, name: str, config_name: Optional[str] = None
    ) -> BaseStrategy:
        """
        从配置文件创建策略实例

        Args:
            name: 策略名称
            config_name: 配置名称，如果为None则使用策略名称

        Returns:
            BaseStrategy: 策略实例
        """
        config_manager = ConfigManager()
        config_key = config_name or name.lower()

        try:
            config = config_manager.load_strategy_config(config_key)
            return cls.create_strategy(name, config)
        except Exception as e:
            logging.warning(f"从配置文件加载失败，使用默认配置: {e}")
            return cls.create_strategy(name)

    @classmethod
    def list_available_strategies(cls) -> List[str]:
        """
        列出所有可用策略

        Returns:
            List[str]: 策略名称列表
        """
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_info(cls, name: str) -> Dict[str, str]:
        """
        获取策略信息

        Args:
            name: 策略名称

        Returns:
            Dict[str, str]: 策略信息
        """
        name_lower = name.lower()

        if name_lower not in cls._strategies:
            raise ValueError(f"未知策略: {name}")

        strategy_class = cls._strategies[name_lower]

        # 创建临时实例以获取信息
        try:
            temp_strategy = strategy_class()
            return {
                "name": name,
                "class_name": strategy_class.__name__,
                "strategy_type": temp_strategy.get_strategy_type().value,
                "version": temp_strategy.config.version,
                "description": strategy_class.__doc__ or "无描述",
            }
        except Exception as e:
            return {
                "name": name,
                "class_name": strategy_class.__name__,
                "strategy_type": "unknown",
                "version": "unknown",
                "description": f"获取信息失败: {e}",
            }

    @classmethod
    def validate_strategy(cls, name: str) -> bool:
        """
        验证策略是否可用

        Args:
            name: 策略名称

        Returns:
            bool: 策略是否可用
        """
        try:
            strategy = cls.create_strategy(name)
            return True
        except Exception as e:
            logging.error(f"策略验证失败: {name}, 错误: {e}")
            return False


class StrategyPlugin(ABC):
    """策略插件基类"""

    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name

    def register(self) -> None:
        """注册插件中的所有策略"""
        strategies = self.get_strategies()
        for name, strategy_class in strategies.items():
            StrategyFactory.register_strategy(name, strategy_class)
            logging.info(f"插件策略已注册: {name} (来自 {self.plugin_name})")

    def unregister(self) -> None:
        """取消注册插件中的所有策略"""
        strategies = self.get_strategies()
        for name in strategies.keys():
            StrategyFactory.unregister_strategy(name)
            logging.info(f"插件策略已取消注册: {name} (来自 {self.plugin_name})")

    @abstractmethod
    def get_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        """
        获取插件提供的策略

        Returns:
            Dict[str, Type[BaseStrategy]]: 策略名称到策略类的映射
        """
        return {}


# 默认策略插件示例
class DefaultStrategiesPlugin(StrategyPlugin):
    """默认策略插件"""

    def __init__(self):
        super().__init__("default_strategies")

    def get_strategies(self) -> Dict[str, Type[BaseStrategy]]:
        """获取默认策略"""
        return {
            "schloss": SchlossStrategy,
            "walter_schloss": SchlossStrategy,
            "value_investing": SchlossStrategy,
        }


# 自动注册默认策略
def _auto_register_defaults():
    """自动注册默认策略"""
    try:
        default_plugin = DefaultStrategiesPlugin()
        # 默认策略已经在工厂中注册，这里不需要重复注册
        logging.info("默认策略已加载")
    except Exception as e:
        logging.error(f"加载默认策略失败: {e}")


# 模块加载时自动注册
_auto_register_defaults()
