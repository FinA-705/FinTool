"""
策略配置管理器

负责加载、保存和管理策略配置，利用核心配置管理器实现动态更新。
"""

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config_manager import config_manager

from .base_strategy import StrategyConfig

# 定义默认的策略和参数配置，以便在文件不存在时创建
DEFAULT_STRATEGIES_CONFIG = {
    "schloss": {
        "name": "Walter Schloss Value Strategy",
        "version": "1.0.0",
        "enabled": True,
        "parameters": {
            "min_market_cap": 1000000000,
            "max_pe_ratio": 15,
            "min_pb_ratio": 0.5,
            "max_pb_ratio": 1.5,
            "min_roe": 0.08,
            "max_debt_to_equity": 0.6,
            "min_current_ratio": 1.2,
            "min_revenue_growth": -0.1,
            "exclude_financial": True,
            "exclude_new_listings": True,
            "min_listing_years": 3,
        },
        "weight_config": {
            "value_score": 0.4,
            "quality_score": 0.3,
            "safety_score": 0.2,
            "growth_score": 0.1,
        },
        "filters": {
            "markets": ["A股", "US", "HK"],
            "exclude_sectors": ["银行", "保险", "证券"],
            "min_trading_days": 250,
            "min_avg_volume": 1000000,
        },
    }
}

DEFAULT_PARAMETERS_CONFIG = {
    "scoring": {
        "pe_ratio_ranges": {
            "excellent": [0, 10],
            "good": [10, 15],
            "fair": [15, 25],
            "poor": [25, 999],
        },
        "pb_ratio_ranges": {
            "excellent": [0, 1.0],
            "good": [1.0, 1.5],
            "fair": [1.5, 2.5],
            "poor": [2.5, 999],
        },
        "roe_ranges": {
            "excellent": [0.15, 999],
            "good": [0.10, 0.15],
            "fair": [0.05, 0.10],
            "poor": [0, 0.05],
        },
        "debt_to_equity_ranges": {
            "excellent": [0, 0.3],
            "good": [0.3, 0.5],
            "fair": [0.5, 0.8],
            "poor": [0.8, 999],
        },
    },
    "market_specific": {
        "A股": {
            "currency": "CNY",
            "trading_hours": "09:30-15:00",
            "settlement_days": 1,
        },
        "US": {"currency": "USD", "trading_hours": "09:30-16:00", "settlement_days": 2},
        "HK": {"currency": "HKD", "trading_hours": "09:30-16:00", "settlement_days": 2},
    },
}


class StrategyConfigManager:
    """
    策略配置管理器
    - 使用 core.config_manager 来处理文件IO和热更新
    - 提供面向策略业务的接口
    """

    def __init__(self):
        """初始化策略配置管理器"""
        self._init_default_configs()
        # 策略配置的本地缓存，用于快速访问和对象转换
        self._config_cache: Dict[str, StrategyConfig] = {}

    def _init_default_configs(self) -> None:
        """
        如果配置文件不存在，则使用核心配置管理器创建它们。
        """
        # 优先尝试从文件系统加载；仅在文件确实不存在时才写入默认配置
        try:
            # 如果存在 config/strategies.yaml|yml|json 将其加载到内存
            config_manager.load_config("strategies", watch=True)
        except FileNotFoundError:
            logging.info("未找到 'strategies' 配置文件，正在创建默认配置...")
            config_manager.configs["strategies"] = DEFAULT_STRATEGIES_CONFIG
            config_manager.save_config("strategies")

        try:
            config_manager.load_config("parameters", watch=True)
        except FileNotFoundError:
            logging.info("未找到 'parameters' 配置文件，正在创建默认配置...")
            config_manager.configs["parameters"] = DEFAULT_PARAMETERS_CONFIG
            config_manager.save_config("parameters")

    def load_strategy_config(self, strategy_name: str) -> StrategyConfig:
        """
        加载策略配置

        Args:
            strategy_name: 策略名称

        Returns:
            StrategyConfig: 策略配置对象
        """
        if strategy_name in self._config_cache:
            return self._config_cache[strategy_name]

        strategy_data = config_manager.get_config("strategies", strategy_name)

        if not strategy_data:
            raise ValueError(f"策略 '{strategy_name}' 配置不存在")

        try:
            config = StrategyConfig(
                name=strategy_data.get("name", "Unknown Strategy"),
                version=strategy_data.get("version", "0.0.0"),
                parameters=strategy_data.get("parameters", {}),
                weight_config=strategy_data.get("weight_config", {}),
                filters=strategy_data.get("filters", {}),
                enabled=strategy_data.get("enabled", True),
            )
            self._config_cache[strategy_name] = config
            return config
        except Exception as e:
            logging.error(f"解析策略配置 '{strategy_name}' 失败: {e}")
            raise

    def save_strategy_config(self, strategy_name: str, config: StrategyConfig) -> None:
        """
        保存策略配置

        Args:
            strategy_name: 策略名称
            config: 策略配置对象
        """
        try:
            config_dict = asdict(config)
            config_manager.set_config("strategies", strategy_name, config_dict)
            config_manager.save_config("strategies")
            # 更新缓存
            self._config_cache[strategy_name] = config
            logging.info(f"策略配置已保存: {strategy_name}")
        except Exception as e:
            logging.error(f"保存策略配置失败: {e}")
            raise

    def update_strategy_parameters(
        self, strategy_name: str, parameters: Dict[str, Any]
    ) -> None:
        """
        更新策略参数

        Args:
            strategy_name: 策略名称
            parameters: 新的参数
        """
        config = self.load_strategy_config(strategy_name)
        config.parameters.update(parameters)
        self.save_strategy_config(strategy_name, config)

    def update_strategy_weights(
        self, strategy_name: str, weights: Dict[str, float]
    ) -> None:
        """
        更新策略权重

        Args:
            strategy_name: 策略名称
            weights: 新的权重配置
        """
        config = self.load_strategy_config(strategy_name)
        config.weight_config.update(weights)
        self.save_strategy_config(strategy_name, config)

    def load_parameters_config(self) -> Dict[str, Any]:
        """加载通用参数配置"""
        # 确保已加载参数配置
        try:
            if "parameters" not in config_manager.configs:
                config_manager.load_config("parameters")
        except FileNotFoundError:
            # 未提供参数配置文件时，返回空配置
            return {}
        return config_manager.get_config("parameters", default={})

    def get_scoring_ranges(self, metric_name: str) -> Dict[str, List[float]]:
        """
        获取指标评分区间

        Args:
            metric_name: 指标名称

        Returns:
            Dict[str, List[float]]: 评分区间配置
        """
        params = self.load_parameters_config()
        scoring_config = params.get("scoring", {})
        return scoring_config.get(f"{metric_name}_ranges", {})

    def get_market_config(self, market_name: str) -> Dict[str, Any]:
        """
        获取市场特定配置

        Args:
            market_name: 市场名称

        Returns:
            Dict[str, Any]: 市场配置
        """
        params = self.load_parameters_config()
        market_config = params.get("market_specific", {})
        return market_config.get(market_name, {})

    def list_available_strategies(self) -> List[str]:
        """列出所有可用策略"""
        # 确保已加载策略配置文件
        try:
            if "strategies" not in config_manager.configs:
                config_manager.load_config("strategies")
        except FileNotFoundError:
            return []

        strategies_data = config_manager.get_config("strategies", default={})
        return list(strategies_data.keys())

    def export_config(self, strategy_name: str, output_path: str) -> None:
        """
        导出策略配置到文件

        Args:
            strategy_name: 策略名称
            output_path: 输出文件路径
        """
        config = self.load_strategy_config(strategy_name)
        config_dict = asdict(config)
        output_file = Path(output_path)

        # 使用核心配置管理器的保存功能
        temp_config_name = f"export_{strategy_name}"
        config_manager.configs[temp_config_name] = config_dict
        config_manager.save_config(temp_config_name, file_path=output_file)
        del config_manager.configs[temp_config_name]  # 清理临时配置

    def import_config(self, strategy_name: str, config_path: str) -> None:
        """
        从文件导入策略配置

        Args:
            strategy_name: 策略名称
            config_path: 配置文件路径
        """
        # 使用核心配置管理器的加载功能
        temp_config_name = f"import_{strategy_name}"
        config_dict = config_manager.load_config(
            temp_config_name, file_path=config_path, watch=False
        )
        del config_manager.configs[temp_config_name]  # 清理临时配置

        config = StrategyConfig(**config_dict)
        self.save_strategy_config(strategy_name, config)

    def clear_cache(self) -> None:
        """清除策略配置的本地对象缓存"""
        self._config_cache.clear()
        logging.info("策略配置缓存已清除")


# 创建一个单例实例供其他模块使用
strategy_config_manager = StrategyConfigManager()

# 兼容旧代码：某些模块会从 strategies.config_manager 导入 `ConfigManager`，
# 将类别名提供回去，以便现有调用 `ConfigManager()` 的代码继续工作。
ConfigManager = StrategyConfigManager
