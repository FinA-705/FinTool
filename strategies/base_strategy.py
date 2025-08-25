"""
基础策略抽象类模块

定义所有选股策略的统一接口和基础功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import pandas as pd
from datetime import datetime


class StrategyType(Enum):
    """策略类型枚举"""

    VALUE = "value"  # 价值投资
    GROWTH = "growth"  # 成长投资
    MOMENTUM = "momentum"  # 动量投资
    QUALITY = "quality"  # 质量投资
    HYBRID = "hybrid"  # 混合策略


@dataclass
class StrategyResult:
    """策略筛选结果"""

    stock_code: str
    stock_name: str
    score: float  # 综合评分 0-100
    rank: int  # 排名
    criteria_scores: Dict[str, float]  # 各项指标得分
    reasons: List[str]  # 选中原因
    warnings: List[str]  # 风险警告
    metadata: Dict[str, Any]  # 额外信息


@dataclass
class StrategyConfig:
    """策略配置"""

    name: str
    version: str
    parameters: Dict[str, Any]
    weight_config: Dict[str, float]  # 各指标权重
    filters: Dict[str, Any]  # 过滤条件
    enabled: bool = True


class BaseStrategy(ABC):
    """基础策略抽象类"""

    def __init__(self, config: Optional[StrategyConfig] = None):
        """
        初始化策略

        Args:
            config: 策略配置，如果为None则使用默认配置
        """
        self.config = config or self.get_default_config()
        self.name = self.config.name
        self.version = self.config.version

    @abstractmethod
    def get_strategy_type(self) -> StrategyType:
        """获取策略类型"""
        pass

    @abstractmethod
    def get_default_config(self) -> StrategyConfig:
        """获取默认配置"""
        pass

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证输入数据是否满足策略要求

        Args:
            data: 股票数据DataFrame

        Returns:
            bool: 数据是否有效
        """
        pass

    @abstractmethod
    def calculate_criteria_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算各项指标得分

        Args:
            data: 股票数据DataFrame

        Returns:
            pd.DataFrame: 包含各项指标得分的DataFrame
        """
        pass

    @abstractmethod
    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        应用过滤条件

        Args:
            data: 股票数据DataFrame

        Returns:
            pd.DataFrame: 过滤后的数据
        """
        pass

    def calculate_composite_score(self, criteria_scores: pd.DataFrame) -> pd.Series:
        """
        计算综合得分

        Args:
            criteria_scores: 各项指标得分DataFrame

        Returns:
            pd.Series: 综合得分
        """
        weights = self.config.weight_config
        composite_scores = pd.Series(0.0, index=criteria_scores.index)

        for criterion, weight in weights.items():
            if criterion in criteria_scores.columns:
                composite_scores += criteria_scores[criterion] * weight

        return composite_scores

    def generate_reasons(self, row: pd.Series, criteria_scores: pd.Series) -> List[str]:
        """
        生成选中原因

        Args:
            row: 股票数据行
            criteria_scores: 该股票的各项指标得分

        Returns:
            List[str]: 选中原因列表
        """
        reasons = []
        # 子类可以重写此方法以提供更具体的原因
        for criterion, score in criteria_scores.items():
            if score > 70:  # 得分高于70的指标
                reasons.append(f"{criterion}表现优秀(得分: {score:.1f})")
        return reasons

    def generate_warnings(
        self, row: pd.Series, criteria_scores: pd.Series
    ) -> List[str]:
        """
        生成风险警告

        Args:
            row: 股票数据行
            criteria_scores: 该股票的各项指标得分

        Returns:
            List[str]: 风险警告列表
        """
        warnings = []
        # 子类可以重写此方法以提供更具体的警告
        for criterion, score in criteria_scores.items():
            if score < 30:  # 得分低于30的指标
                warnings.append(f"{criterion}表现较差(得分: {score:.1f})")
        return warnings

    def screen_stocks(
        self, data: pd.DataFrame, top_n: Optional[int] = None
    ) -> List[StrategyResult]:
        """
        筛选股票

        Args:
            data: 股票数据DataFrame
            top_n: 返回前N只股票，如果为None则返回所有符合条件的股票

        Returns:
            List[StrategyResult]: 筛选结果列表
        """
        # 验证数据
        if not self.validate_data(data):
            raise ValueError("输入数据不满足策略要求")

        # 应用过滤条件
        filtered_data = self.apply_filters(data)

        if filtered_data.empty:
            return []

        # 计算各项指标得分
        criteria_scores = self.calculate_criteria_scores(filtered_data)

        # 计算综合得分
        composite_scores = self.calculate_composite_score(criteria_scores)

        # 排序
        sorted_indices = composite_scores.sort_values(ascending=False).index

        # 限制数量
        if top_n:
            sorted_indices = sorted_indices[:top_n]

        # 生成结果
        results = []
        for rank, idx in enumerate(sorted_indices, 1):
            stock_data = filtered_data.loc[idx]
            stock_criteria_scores = criteria_scores.loc[idx]

            result = StrategyResult(
                stock_code=stock_data.get("stock_code", str(idx)),
                stock_name=stock_data.get("stock_name", "Unknown"),
                score=composite_scores.loc[idx],
                rank=rank,
                criteria_scores=stock_criteria_scores.to_dict(),
                reasons=self.generate_reasons(stock_data, stock_criteria_scores),
                warnings=self.generate_warnings(stock_data, stock_criteria_scores),
                metadata={
                    "strategy_name": self.name,
                    "strategy_version": self.version,
                    "screening_time": datetime.now().isoformat(),
                },
            )
            results.append(result)

        return results

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新策略配置

        Args:
            new_config: 新的配置参数
        """
        # 更新参数
        if "parameters" in new_config:
            self.config.parameters.update(new_config["parameters"])

        # 更新权重
        if "weight_config" in new_config:
            self.config.weight_config.update(new_config["weight_config"])

        # 更新过滤条件
        if "filters" in new_config:
            self.config.filters.update(new_config["filters"])

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "strategy_type": self.get_strategy_type().value,
            "parameters_count": len(self.config.parameters),
            "criteria_count": len(self.config.weight_config),
            "filters_count": len(self.config.filters),
            "enabled": self.config.enabled,
        }
