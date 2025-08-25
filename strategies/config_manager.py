"""
策略配置管理器

负责加载、保存和管理策略配置，支持动态配置更新。
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import logging

from .base_strategy import StrategyConfig


class ConfigManager:
    """策略配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录，默认为项目根目录下的config文件夹
        """
        self.config_dir = (
            Path(config_dir) if config_dir else Path(__file__).parent.parent / "config"
        )
        self.config_dir.mkdir(exist_ok=True)

        # 策略配置缓存
        self._config_cache: Dict[str, StrategyConfig] = {}

        # 默认配置文件路径
        self.strategies_config_file = self.config_dir / "strategies.yaml"
        self.parameters_config_file = self.config_dir / "parameters.yaml"

        # 初始化默认配置文件
        self._init_default_configs()

    def _init_default_configs(self) -> None:
        """初始化默认配置文件"""
        if not self.strategies_config_file.exists():
            default_strategies = {
                "schloss": {
                    "name": "Walter Schloss Value Strategy",
                    "version": "1.0.0",
                    "enabled": True,
                    "parameters": {
                        "min_market_cap": 1000000000,  # 10亿最小市值
                        "max_pe_ratio": 15,  # 最大市盈率
                        "min_pb_ratio": 0.5,  # 最小市净率
                        "max_pb_ratio": 1.5,  # 最大市净率
                        "min_roe": 0.08,  # 最小ROE 8%
                        "max_debt_to_equity": 0.6,  # 最大负债权益比
                        "min_current_ratio": 1.2,  # 最小流动比率
                        "min_revenue_growth": -0.1,  # 最小营收增长率
                        "exclude_financial": True,  # 排除金融股
                        "exclude_new_listings": True,  # 排除新上市股票
                        "min_listing_years": 3,  # 最小上市年数
                    },
                    "weight_config": {
                        "value_score": 0.4,  # 估值得分权重
                        "quality_score": 0.3,  # 质量得分权重
                        "safety_score": 0.2,  # 安全得分权重
                        "growth_score": 0.1,  # 成长得分权重
                    },
                    "filters": {
                        "markets": ["A股", "US", "HK"],  # 支持的市场
                        "exclude_sectors": ["银行", "保险", "证券"],  # 排除行业
                        "min_trading_days": 250,  # 最小交易天数
                        "min_avg_volume": 1000000,  # 最小平均成交量
                    },
                }
            }

            with open(self.strategies_config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_strategies, f, default_flow_style=False, allow_unicode=True
                )

        if not self.parameters_config_file.exists():
            default_parameters = {
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
                    "US": {
                        "currency": "USD",
                        "trading_hours": "09:30-16:00",
                        "settlement_days": 2,
                    },
                    "HK": {
                        "currency": "HKD",
                        "trading_hours": "09:30-16:00",
                        "settlement_days": 2,
                    },
                },
            }

            with open(self.parameters_config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    default_parameters, f, default_flow_style=False, allow_unicode=True
                )

    def load_strategy_config(self, strategy_name: str) -> StrategyConfig:
        """
        加载策略配置

        Args:
            strategy_name: 策略名称

        Returns:
            StrategyConfig: 策略配置对象
        """
        # 检查缓存
        if strategy_name in self._config_cache:
            return self._config_cache[strategy_name]

        # 从文件加载
        try:
            with open(self.strategies_config_file, "r", encoding="utf-8") as f:
                strategies_data = yaml.safe_load(f)

            if strategy_name not in strategies_data:
                raise ValueError(f"策略 '{strategy_name}' 配置不存在")

            strategy_data = strategies_data[strategy_name]
            config = StrategyConfig(
                name=strategy_data["name"],
                version=strategy_data["version"],
                parameters=strategy_data["parameters"],
                weight_config=strategy_data["weight_config"],
                filters=strategy_data["filters"],
                enabled=strategy_data.get("enabled", True),
            )

            # 缓存配置
            self._config_cache[strategy_name] = config
            return config

        except Exception as e:
            logging.error(f"加载策略配置失败: {e}")
            raise

    def save_strategy_config(self, strategy_name: str, config: StrategyConfig) -> None:
        """
        保存策略配置

        Args:
            strategy_name: 策略名称
            config: 策略配置对象
        """
        try:
            # 读取现有配置
            if self.strategies_config_file.exists():
                with open(self.strategies_config_file, "r", encoding="utf-8") as f:
                    strategies_data = yaml.safe_load(f) or {}
            else:
                strategies_data = {}

            # 更新配置
            strategies_data[strategy_name] = {
                "name": config.name,
                "version": config.version,
                "enabled": config.enabled,
                "parameters": config.parameters,
                "weight_config": config.weight_config,
                "filters": config.filters,
            }

            # 保存到文件
            with open(self.strategies_config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    strategies_data, f, default_flow_style=False, allow_unicode=True
                )

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
        try:
            with open(self.parameters_config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"加载参数配置失败: {e}")
            return {}

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
        try:
            with open(self.strategies_config_file, "r", encoding="utf-8") as f:
                strategies_data = yaml.safe_load(f) or {}
            return list(strategies_data.keys())
        except Exception:
            return []

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
        if output_file.suffix == ".json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

    def import_config(self, strategy_name: str, config_path: str) -> None:
        """
        从文件导入策略配置

        Args:
            strategy_name: 策略名称
            config_path: 配置文件路径
        """
        config_file = Path(config_path)

        if config_file.suffix == ".json":
            with open(config_file, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        else:
            with open(config_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)

        config = StrategyConfig(**config_dict)
        self.save_strategy_config(strategy_name, config)

    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache.clear()
        logging.info("配置缓存已清除")
