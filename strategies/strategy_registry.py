"""
策略注册和管理模块
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from strategies.formula_parser import StrategyFormulaParser
from strategies.formula_template_manager import StrategyTemplateManager
from strategies.formula_types import FormulaType
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str  # 策略名称
    description: str  # 策略描述
    filters: List[str]  # 过滤条件列表
    score_formula: Optional[str] = None  # 评分公式
    ranking_formula: Optional[str] = None  # 排序公式
    signal_formulas: Dict[str, str] = field(default_factory=dict)  # 信号公式
    risk_formulas: Dict[str, str] = field(default_factory=dict)  # 风险公式
    constants: Dict[str, Any] = field(default_factory=dict)  # 自定义常量
    enabled: bool = True  # 是否启用


class StrategyRegistry:
    """策略注册中心"""

    def __init__(self):
        self.parser = StrategyFormulaParser()
        self.template_manager = StrategyTemplateManager()
        self.loaded_strategies: Dict[str, StrategyConfig] = {}

    def register_strategy(self, strategy_config: StrategyConfig) -> bool:
        """注册策略

        Args:
            strategy_config: 策略配置

        Returns:
            是否注册成功
        """
        try:
            # 验证策略配置
            validation_error = self._validate_strategy_config(strategy_config)
            if validation_error:
                logger.error(f"策略配置验证失败: {validation_error}")
                return False

            # 解析和验证所有公式
            parse_error = self._parse_strategy_formulas(strategy_config)
            if parse_error:
                logger.error(f"策略公式解析失败: {parse_error}")
                return False

            # 注册策略
            self.loaded_strategies[strategy_config.name] = strategy_config
            logger.info(f"策略注册成功: {strategy_config.name}")
            return True

        except Exception as e:
            logger.error(f"策略注册失败: {e}")
            return False

    def load_strategy_from_template(
        self, template_name: str, custom_params: Optional[Dict[str, Any]] = None
    ) -> Optional[StrategyConfig]:
        """从模板加载策略

        Args:
            template_name: 模板名称
            custom_params: 自定义参数

        Returns:
            策略配置
        """
        template = self.template_manager.get_template(template_name)
        if not template:
            logger.error(f"模板不存在: {template_name}")
            return None

        try:
            # 创建策略配置
            config = StrategyConfig(
                name=template.get("name", template_name),
                description=template.get("description", ""),
                filters=template.get("filters", []),
                score_formula=template.get("score"),
                ranking_formula=template.get("ranking"),
                signal_formulas=template.get("signals", {}),
                risk_formulas=template.get("risks", {}),
                constants=custom_params or {},
            )
            return config

        except Exception as e:
            logger.error(f"从模板加载策略失败: {e}")
            return None

    def create_custom_strategy(
        self,
        name: str,
        description: str,
        filters: List[str],
        score_formula: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """创建自定义策略"""
        config = StrategyConfig(
            name=name,
            description=description,
            filters=filters,
            score_formula=score_formula,
            ranking_formula=kwargs.get("ranking_formula"),
            signal_formulas=kwargs.get("signal_formulas", {}),
            risk_formulas=kwargs.get("risk_formulas", {}),
            constants=kwargs.get("constants", {}),
        )
        return self.register_strategy(config)

    def get_strategy(self, strategy_name: str) -> Optional[StrategyConfig]:
        """获取已注册的策略"""
        return self.loaded_strategies.get(strategy_name)

    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略信息"""
        strategy_config = self.get_strategy(strategy_name)
        if not strategy_config:
            return None

        return {
            "name": strategy_config.name,
            "description": strategy_config.description,
            "filters": strategy_config.filters,
            "score_formula": strategy_config.score_formula,
            "ranking_formula": strategy_config.ranking_formula,
            "signal_formulas": strategy_config.signal_formulas,
            "risk_formulas": strategy_config.risk_formulas,
            "constants": strategy_config.constants,
            "enabled": strategy_config.enabled,
        }

    def list_strategies(self) -> List[str]:
        """列出所有已注册的策略"""
        return list(self.loaded_strategies.keys())

    def _validate_strategy_config(self, config: StrategyConfig) -> Optional[str]:
        """验证策略配置"""
        if not config.name:
            return "策略名称不能为空"
        if not config.filters:
            return "过滤条件不能为空"
        if not isinstance(config.filters, list):
            return "过滤条件必须是列表"
        return None

    def _parse_strategy_formulas(self, config: StrategyConfig) -> Optional[str]:
        """解析策略公式"""
        # 解析过滤条件
        for i, filter_formula in enumerate(config.filters):
            parsed = self.parser.parse_formula(filter_formula, FormulaType.FILTER)
            if not parsed.is_valid:
                return f"过滤条件 {i+1} 解析失败: {parsed.error_message}"

        # 解析评分公式
        if config.score_formula:
            parsed = self.parser.parse_formula(config.score_formula, FormulaType.SCORE)
            if not parsed.is_valid:
                return f"评分公式解析失败: {parsed.error_message}"

        # 解析排序公式
        if config.ranking_formula:
            parsed = self.parser.parse_formula(
                config.ranking_formula, FormulaType.RANKING
            )
            if not parsed.is_valid:
                return f"排序公式解析失败: {parsed.error_message}"

        return None
