"""
策略模板管理器

管理和验证策略模板
"""

from typing import Dict, List, Optional, Tuple, Any


class StrategyTemplateManager:
    """策略模板管理器"""

    def __init__(self):
        """初始化模板管理器"""
        self.templates = self._load_default_templates()

    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载默认模板"""
        return {
            "schloss_basic": {
                "name": "施洛斯基础策略",
                "description": "Walter Schloss经典价值投资策略",
                "filters": [
                    "market_cap > MIN_MARKET_CAP",
                    "pe > 0 and pe < MAX_PE",
                    "pb > 0 and pb < 1.5",
                    "current_ratio > MIN_CURRENT_RATIO",
                    "debt_ratio < MAX_DEBT_RATIO",
                    "roe > MIN_ROE",
                ],
                "score": "RANK(pb) * 0.3 + RANK(pe) * 0.3 + RANK(1/roe) * 0.4",
                "type": "value_investing",
            },
            "momentum_strategy": {
                "name": "动量策略",
                "description": "基于价格动量的选股策略",
                "filters": [
                    "volume > MEAN(volume) * 1.5",
                    "close > sma_20",
                    "MOMENTUM(close, 20) > 0.1",
                ],
                "score": "MOMENTUM(close, 10) * 0.5 + MOMENTUM(close, 30) * 0.5",
                "type": "momentum",
            },
            "quality_growth": {
                "name": "质量成长策略",
                "description": "高质量成长股选择策略",
                "filters": [
                    "roe > 0.15",
                    "roa > 0.08",
                    "debt_ratio < 0.3",
                    "revenue_growth > 0.1",
                ],
                "score": "roe * 0.4 + roa * 0.3 + (1 - debt_ratio) * 0.3",
                "type": "quality_growth",
            },
        }

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取策略模板"""
        return self.templates.get(template_name)

    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.templates.keys())

    def add_template(self, name: str, template: Dict[str, Any]):
        """添加自定义模板"""
        self.templates[name] = template

    def validate_template(self, template: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证模板格式"""
        required_fields = ["name", "description", "filters", "score", "type"]

        for field in required_fields:
            if field not in template:
                return False, f"缺少必需字段: {field}"

        if not isinstance(template["filters"], list):
            return False, "filters必须是列表"

        return True, None
