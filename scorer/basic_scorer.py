"""
基础评分模块

基于财务指标和技术指标计算股票基础评分
支持多种评分权重和模型配置
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import json


class ScoringMethod(Enum):
    """评分方法枚举"""

    WEIGHTED_SUM = "weighted_sum"
    PERCENTILE_RANK = "percentile_rank"
    Z_SCORE = "z_score"
    COMPOSITE = "composite"


@dataclass
class ScoringConfig:
    """评分配置"""

    method: ScoringMethod = ScoringMethod.WEIGHTED_SUM
    weights: Optional[Dict[str, float]] = None
    normalize: bool = True
    min_score: float = 0.0
    max_score: float = 100.0

    def __post_init__(self):
        if self.weights is None:
            self.weights = self.get_default_weights()

    def get_default_weights(self) -> Dict[str, float]:
        """获取默认权重配置"""
        return {
            "pe_ratio": -0.15,  # 市盈率越低越好
            "pb_ratio": -0.15,  # 市净率越低越好
            "roe": 0.20,  # 净资产收益率越高越好
            "debt_ratio": -0.10,  # 负债率越低越好
            "revenue_growth": 0.15,  # 营收增长率越高越好
            "profit_growth": 0.15,  # 利润增长率越高越好
            "current_ratio": 0.10,  # 流动比率越高越好
            "gross_margin": 0.10,  # 毛利率越高越好
        }


@dataclass
class ScoringResult:
    """评分结果"""

    symbol: str
    total_score: float
    component_scores: Dict[str, float]
    percentile_rank: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "total_score": self.total_score,
            "component_scores": self.component_scores,
            "percentile_rank": self.percentile_rank,
            "metadata": self.metadata,
        }


class BasicScorer:
    """基础评分器

    基于财务指标计算股票的基础评分
    支持多种评分方法和权重配置
    """

    def __init__(self, config: Optional[ScoringConfig] = None):
        """初始化评分器

        Args:
            config: 评分配置，如果为None则使用默认配置
        """
        self.config = config or ScoringConfig()
        self._validate_config()

    def _validate_config(self):
        """验证配置有效性"""
        if not isinstance(self.config.weights, dict):
            raise ValueError("权重配置必须是字典类型")

        if self.config.min_score >= self.config.max_score:
            raise ValueError("最小评分必须小于最大评分")

        # 验证权重总和
        total_weight = sum(abs(w) for w in self.config.weights.values())
        if total_weight == 0:
            raise ValueError("权重总和不能为零")

    def score_single(self, data: Dict[str, Union[float, str]]) -> ScoringResult:
        """对单只股票进行评分

        Args:
            data: 包含财务指标的字典

        Returns:
            评分结果
        """
        symbol = str(data.get("symbol", "UNKNOWN"))

        # 计算各组件评分
        component_scores = self._calculate_component_scores(data)

        # 计算总评分
        total_score = self._calculate_total_score(component_scores)

        # 标准化评分
        if self.config.normalize:
            total_score = self._normalize_score(total_score)

        return ScoringResult(
            symbol=symbol,
            total_score=total_score,
            component_scores=component_scores,
            percentile_rank=0.0,  # 单独评分时无法计算百分位
            metadata={
                "method": self.config.method.value,
                "weights_used": (
                    self.config.weights.copy() if self.config.weights else {}
                ),
            },
        )

    def score_batch(
        self, data_list: List[Dict[str, Union[float, str]]]
    ) -> List[ScoringResult]:
        """批量评分

        Args:
            data_list: 包含多只股票数据的列表

        Returns:
            评分结果列表
        """
        if not data_list:
            return []

        # 先计算所有股票的基础评分
        results = []
        all_scores = []

        for data in data_list:
            result = self.score_single(data)
            results.append(result)
            all_scores.append(result.total_score)

        # 计算百分位排名
        if len(all_scores) > 1:
            for i, result in enumerate(results):
                result.percentile_rank = self._calculate_percentile_rank(
                    result.total_score, all_scores
                )

        return results

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """对DataFrame进行评分

        Args:
            df: 包含股票数据的DataFrame

        Returns:
            包含评分信息的DataFrame
        """
        if df.empty:
            return df

        # 转换为字典列表
        data_list = [
            {
                k: (v if isinstance(v, (int, float, str)) else str(v))
                for k, v in record.items()
            }
            for record in df.to_dict("records")
        ]

        # 批量评分
        results = self.score_batch(data_list)

        # 构造结果DataFrame
        result_df = df.copy()
        result_df["basic_score"] = [r.total_score for r in results]
        result_df["percentile_rank"] = [r.percentile_rank for r in results]

        # 添加组件评分
        if results:
            for component in results[0].component_scores.keys():
                result_df[f"score_{component}"] = [
                    r.component_scores.get(component, 0.0) for r in results
                ]

        return result_df

    def _calculate_component_scores(
        self, data: Dict[str, Union[float, str]]
    ) -> Dict[str, float]:
        """计算各组件评分"""
        component_scores = {}

        if not self.config.weights:
            return component_scores

        for indicator, weight in self.config.weights.items():
            if indicator in data:
                raw_value = data[indicator]
                # 转换为float类型
                try:
                    if isinstance(raw_value, str):
                        raw_value = float(raw_value)
                    elif not isinstance(raw_value, (int, float)):
                        continue
                    score = self._score_indicator(indicator, float(raw_value), weight)
                    component_scores[indicator] = score
                except (ValueError, TypeError):
                    # 无法转换的值跳过
                    continue

        return component_scores

    def _score_indicator(self, indicator: str, value: float, weight: float) -> float:
        """为单个指标评分"""
        if pd.isna(value) or np.isinf(value):
            return 0.0

        # 根据不同指标类型进行评分
        if indicator in ["pe_ratio", "pb_ratio", "debt_ratio"]:
            # 越小越好的指标
            if value <= 0:
                return 0.0
            # 使用倒数评分，然后乘以权重
            score = (1.0 / max(value, 0.01)) * abs(weight) * 10
        elif indicator in [
            "roe",
            "revenue_growth",
            "profit_growth",
            "current_ratio",
            "gross_margin",
        ]:
            # 越大越好的指标
            score = max(value, 0) * abs(weight)
        else:
            # 通用评分：直接使用权重
            score = value * weight

        return score

    def _calculate_total_score(self, component_scores: Dict[str, float]) -> float:
        """计算总评分"""
        if self.config.method == ScoringMethod.WEIGHTED_SUM:
            return sum(component_scores.values())
        elif self.config.method == ScoringMethod.COMPOSITE:
            # 组合评分：加权平均
            if self.config.weights:
                total_weight = sum(abs(w) for w in self.config.weights.values())
                if total_weight > 0:
                    return sum(component_scores.values()) / total_weight * 100

        return sum(component_scores.values())

    def _normalize_score(self, score: float) -> float:
        """标准化评分到指定范围"""
        # 简单的线性标准化
        normalized = max(self.config.min_score, min(self.config.max_score, score))
        return round(normalized, 2)

    def _calculate_percentile_rank(
        self, score: float, all_scores: List[float]
    ) -> float:
        """计算百分位排名"""
        if not all_scores:
            return 0.0

        sorted_scores = sorted(all_scores)
        rank = sorted_scores.index(score) if score in sorted_scores else 0

        percentile = (
            (rank / (len(sorted_scores) - 1)) * 100 if len(sorted_scores) > 1 else 0.0
        )
        return round(percentile, 2)

    def export_results(
        self, results: List[ScoringResult], output_path: Union[str, Path]
    ) -> bool:
        """导出评分结果

        Args:
            results: 评分结果列表
            output_path: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为可序列化的格式
            export_data = {
                "config": {
                    "method": self.config.method.value,
                    "weights": self.config.weights,
                    "normalize": self.config.normalize,
                    "score_range": [self.config.min_score, self.config.max_score],
                },
                "results": [result.to_dict() for result in results],
                "summary": {
                    "total_stocks": len(results),
                    "avg_score": (
                        sum(r.total_score for r in results) / len(results)
                        if results
                        else 0
                    ),
                    "score_distribution": self._get_score_distribution(results),
                },
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出评分结果失败: {e}")
            return False

    def _get_score_distribution(self, results: List[ScoringResult]) -> Dict[str, int]:
        """获取评分分布统计"""
        if not results:
            return {}

        scores = [r.total_score for r in results]
        return {
            "excellent": len([s for s in scores if s >= 80]),
            "good": len([s for s in scores if 60 <= s < 80]),
            "average": len([s for s in scores if 40 <= s < 60]),
            "poor": len([s for s in scores if s < 40]),
        }


# 使用示例
if __name__ == "__main__":
    # 示例数据
    sample_data = [
        {
            "symbol": "000001.SZ",
            "pe_ratio": 12.5,
            "pb_ratio": 1.2,
            "roe": 15.8,
            "debt_ratio": 0.45,
            "revenue_growth": 8.5,
            "profit_growth": 12.3,
            "current_ratio": 1.8,
            "gross_margin": 25.6,
        },
        {
            "symbol": "000002.SZ",
            "pe_ratio": 18.2,
            "pb_ratio": 2.1,
            "roe": 12.4,
            "debt_ratio": 0.52,
            "revenue_growth": 5.2,
            "profit_growth": 8.1,
            "current_ratio": 1.5,
            "gross_margin": 22.3,
        },
    ]

    # 创建评分器
    scorer = BasicScorer()

    # 批量评分
    results = scorer.score_batch(sample_data)

    # 打印结果
    for result in results:
        print(f"股票: {result.symbol}")
        print(f"总评分: {result.total_score}")
        print(f"百分位排名: {result.percentile_rank}")
        print("---")
