"""
AI评分模块

集成AI模型(如GPT-4)进行智能股票评分
输出结构化JSON评分和理由
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
import time
import hashlib
from pathlib import Path


class AIProvider(Enum):
    """AI服务提供商枚举"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL_LLM = "local_llm"


@dataclass
class AIConfig:
    """AI评分配置"""

    provider: AIProvider = AIProvider.OPENAI
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.3
    timeout: int = 30
    retry_times: int = 3
    cache_enabled: bool = True


@dataclass
class AIReason:
    """AI评分理由"""

    category: str
    score: float
    reasoning: str
    confidence: float


@dataclass
class AIScoringResult:
    """AI评分结果"""

    symbol: str
    total_score: float
    reasons: List[AIReason]
    summary: str
    confidence: float
    model_used: str
    processing_time: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "symbol": self.symbol,
            "total_score": self.total_score,
            "reasons": [
                {
                    "category": r.category,
                    "score": r.score,
                    "reasoning": r.reasoning,
                    "confidence": r.confidence,
                }
                for r in self.reasons
            ],
            "summary": self.summary,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "processing_time": self.processing_time,
        }


class AIScorer:
    """AI评分器

    使用大语言模型进行智能股票分析和评分
    支持多种AI服务提供商和模型
    """

    def __init__(self, config: Optional[AIConfig] = None):
        """初始化AI评分器

        Args:
            config: AI评分配置
        """
        self.config = config or AIConfig()
        self.cache: Dict[str, AIScoringResult] = {}

        # 验证配置
        self._validate_config()

    def _validate_config(self):
        """验证配置有效性"""
        if self.config.provider != AIProvider.LOCAL_LLM and not self.config.api_key:
            print(f"警告: {self.config.provider.value} 需要设置 API Key")

        if self.config.max_tokens <= 0:
            raise ValueError("max_tokens 必须大于0")

        if not 0 <= self.config.temperature <= 2:
            raise ValueError("temperature 必须在0-2之间")

    def score_single(self, data: Dict[str, Union[float, str]]) -> AIScoringResult:
        """对单只股票进行AI评分

        Args:
            data: 包含股票财务数据的字典

        Returns:
            AI评分结果
        """
        symbol = str(data.get("symbol", "UNKNOWN"))

        # 检查缓存
        cache_key = None
        if self.config.cache_enabled:
            cache_key = self._generate_cache_key(data)
            if cache_key in self.cache:
                return self.cache[cache_key]

        start_time = time.time()

        try:
            # 模拟AI评分逻辑（实际使用中需要调用真实的AI API）
            result = self._simulate_ai_scoring(data, symbol, time.time() - start_time)

            # 缓存结果
            if self.config.cache_enabled and cache_key:
                self.cache[cache_key] = result

            return result

        except Exception as e:
            # 返回默认结果
            return AIScoringResult(
                symbol=symbol,
                total_score=50.0,
                reasons=[
                    AIReason(
                        category="error",
                        score=50.0,
                        reasoning=f"AI评分失败: {str(e)}",
                        confidence=0.0,
                    )
                ],
                summary="AI评分服务暂时不可用",
                confidence=0.0,
                model_used=self.config.model,
                processing_time=time.time() - start_time,
            )

    def score_batch(
        self, data_list: List[Dict[str, Union[float, str]]]
    ) -> List[AIScoringResult]:
        """批量AI评分

        Args:
            data_list: 包含多只股票数据的列表

        Returns:
            AI评分结果列表
        """
        if not data_list:
            return []

        # 简化版本：顺序处理（实际使用中可以改为异步并发）
        results = []
        for data in data_list:
            result = self.score_single(data)
            results.append(result)

        return results

    def _simulate_ai_scoring(
        self, data: Dict[str, Union[float, str]], symbol: str, processing_time: float
    ) -> AIScoringResult:
        """模拟AI评分（实际使用中需要替换为真实的AI API调用）"""

        # 提取关键指标
        pe_ratio = self._get_float_value(data, "pe_ratio", 15.0)
        pb_ratio = self._get_float_value(data, "pb_ratio", 2.0)
        roe = self._get_float_value(data, "roe", 10.0)
        debt_ratio = self._get_float_value(data, "debt_ratio", 0.5)
        revenue_growth = self._get_float_value(data, "revenue_growth", 5.0)
        profit_growth = self._get_float_value(data, "profit_growth", 5.0)

        # 模拟AI分析各个维度
        reasons = []

        # 估值分析
        valuation_score = max(
            0, min(100, 100 - (pe_ratio - 10) * 3 - (pb_ratio - 1) * 20)
        )
        reasons.append(
            AIReason(
                category="估值水平",
                score=valuation_score,
                reasoning=f"市盈率{pe_ratio:.1f}倍，市净率{pb_ratio:.1f}倍，估值{'合理' if valuation_score > 60 else '偏高' if valuation_score > 30 else '过高'}",
                confidence=0.8,
            )
        )

        # 盈利能力分析
        profitability_score = min(100, max(0, roe * 5))
        reasons.append(
            AIReason(
                category="盈利能力",
                score=profitability_score,
                reasoning=f"净资产收益率{roe:.1f}%，盈利能力{'优秀' if roe > 15 else '良好' if roe > 10 else '一般'}",
                confidence=0.9,
            )
        )

        # 财务健康
        financial_health_score = max(0, min(100, (1 - debt_ratio) * 100))
        reasons.append(
            AIReason(
                category="财务健康",
                score=financial_health_score,
                reasoning=f"负债率{debt_ratio:.1%}，财务结构{'稳健' if debt_ratio < 0.5 else '一般' if debt_ratio < 0.7 else '风险较高'}",
                confidence=0.85,
            )
        )

        # 成长性分析
        growth_score = min(100, max(0, (revenue_growth + profit_growth) * 2.5))
        reasons.append(
            AIReason(
                category="成长性",
                score=growth_score,
                reasoning=f"营收增长{revenue_growth:.1f}%，利润增长{profit_growth:.1f}%，成长{'强劲' if growth_score > 70 else '稳定' if growth_score > 40 else '缓慢'}",
                confidence=0.75,
            )
        )

        # 计算总分（加权平均）
        total_score = (
            valuation_score * 0.25
            + profitability_score * 0.3
            + financial_health_score * 0.25
            + growth_score * 0.2
        )

        # 生成投资建议
        if total_score >= 80:
            summary = "优质标的，建议重点关注"
        elif total_score >= 60:
            summary = "基本面良好，可适度配置"
        elif total_score >= 40:
            summary = "表现一般，需谨慎评估"
        else:
            summary = "基本面较弱，建议回避"

        return AIScoringResult(
            symbol=symbol,
            total_score=round(total_score, 2),
            reasons=reasons,
            summary=summary,
            confidence=0.8,
            model_used=self.config.model,
            processing_time=processing_time,
        )

    def _get_float_value(
        self, data: Dict[str, Union[float, str]], key: str, default: float
    ) -> float:
        """安全获取浮点数值"""
        try:
            value = data.get(key, default)
            if isinstance(value, str):
                return float(value)
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    def _generate_cache_key(self, data: Dict[str, Union[float, str]]) -> str:
        """生成缓存键"""
        # 使用关键数据生成哈希
        key_data = {k: v for k, v in data.items() if k != "timestamp"}
        content = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    def export_results(
        self, results: List[AIScoringResult], output_path: Union[str, Path]
    ) -> bool:
        """导出AI评分结果

        Args:
            results: AI评分结果列表
            output_path: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                "config": {
                    "provider": self.config.provider.value,
                    "model": self.config.model,
                    "temperature": self.config.temperature,
                },
                "results": [result.to_dict() for result in results],
                "summary": {
                    "total_stocks": len(results),
                    "avg_score": (
                        sum(r.total_score for r in results) / len(results)
                        if results
                        else 0
                    ),
                    "avg_confidence": (
                        sum(r.confidence for r in results) / len(results)
                        if results
                        else 0
                    ),
                    "avg_processing_time": (
                        sum(r.processing_time for r in results) / len(results)
                        if results
                        else 0
                    ),
                },
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            print(f"导出AI评分结果失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 示例数据
    sample_data = {
        "symbol": "000001.SZ",
        "pe_ratio": 12.5,
        "pb_ratio": 1.2,
        "roe": 15.8,
        "debt_ratio": 0.45,
        "revenue_growth": 8.5,
        "profit_growth": 12.3,
    }

    # 配置AI评分器
    config = AIConfig(provider=AIProvider.OPENAI, model="gpt-4", cache_enabled=True)

    scorer = AIScorer(config)
    result = scorer.score_single(sample_data)

    print(f"股票: {result.symbol}")
    print(f"AI评分: {result.total_score}")
    print(f"置信度: {result.confidence}")
    print(f"总结: {result.summary}")
    print("\n详细分析:")
    for reason in result.reasons:
        print(f"- {reason.category}: {reason.score:.1f}分 - {reason.reasoning}")
