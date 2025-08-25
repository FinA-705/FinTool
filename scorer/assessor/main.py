"""
风险评估主类
"""
import json
from pathlib import Path
from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime

from .models import RiskConfig, RiskAssessment, RiskLevel, RiskMetrics
from .calculator import MetricsCalculator
from .reporter import ReportGenerator


class RiskAssessor:
    """风险评估器"""

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self._validate_config()
        self.calculator = MetricsCalculator(self.config)
        self.reporter = ReportGenerator()

    def _validate_config(self):
        if not 0 < self.config.confidence_level < 1:
            raise ValueError("置信水平必须在0-1之间")
        if self.config.risk_free_rate < 0:
            raise ValueError("无风险利率不能为负")
        if self.config.lookback_days <= 0:
            raise ValueError("回望天数必须大于0")
        if self.config.min_periods <= 0:
            raise ValueError("最小计算周期必须大于0")

    def assess_single(
        self, price_data: pd.Series, market_data: Optional[pd.Series] = None
    ) -> RiskAssessment:
        """评估单只股票的风险"""
        if price_data.empty:
            raise ValueError("价格数据不能为空")
        symbol = str(price_data.name) if price_data.name is not None else "UNKNOWN"
        returns = price_data.pct_change().dropna()
        if len(returns) < self.config.min_periods:
            raise ValueError(f"数据不足，至少需要{self.config.min_periods}个交易日")

        market_returns = market_data.pct_change().dropna() if market_data is not None else None
        metrics = self.calculator.calculate(returns, market_returns)
        risk_level, risk_score = self.reporter.assess_risk_level(metrics)
        warnings = self.reporter.generate_warnings(metrics)
        recommendations = self.reporter.generate_recommendations(metrics, risk_level)

        return RiskAssessment(
            symbol=symbol,
            risk_level=risk_level,
            risk_score=risk_score,
            metrics=metrics,
            warnings=warnings,
            recommendations=recommendations,
            assessment_date=datetime.now(),
        )

    def assess_batch(
        self,
        price_data_dict: Dict[str, pd.Series],
        market_data: Optional[pd.Series] = None,
    ) -> Dict[str, RiskAssessment]:
        """批量评估多只股票的风险"""
        results = {}
        for symbol, price_data in price_data_dict.items():
            try:
                price_data.name = symbol
                assessment = self.assess_single(price_data, market_data)
                results[symbol] = assessment
            except Exception as e:
                results[symbol] = RiskAssessment(
                    symbol=symbol,
                    risk_level=RiskLevel.MEDIUM,
                    risk_score=50.0,
                    metrics=RiskMetrics(0, 0, 0, 0, 0, 0),
                    warnings=[f"评估失败: {str(e)}"],
                    recommendations=["数据不足，建议谨慎投资"],
                    assessment_date=datetime.now(),
                )
        return results

    def export_results(
        self,
        assessments: Union[RiskAssessment, Dict[str, RiskAssessment]],
        output_path: Union[str, Path],
    ) -> bool:
        """导出风险评估结果"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(assessments, RiskAssessment):
                results_list = [assessments]
                summary_data = {
                    "total_stocks": 1,
                    "risk_distribution": {assessments.risk_level.value: 1},
                }
            else:
                results_list = list(assessments.values())
                risk_distribution = {}
                for assessment in results_list:
                    level = assessment.risk_level.value
                    risk_distribution[level] = risk_distribution.get(level, 0) + 1
                summary_data = {
                    "total_stocks": len(results_list),
                    "avg_risk_score": sum(a.risk_score for a in results_list)
                    / len(results_list),
                    "risk_distribution": risk_distribution,
                }
            export_data = {
                "config": {
                    "confidence_level": self.config.confidence_level,
                    "risk_free_rate": self.config.risk_free_rate,
                    "lookback_days": self.config.lookback_days,
                },
                "results": [assessment.to_dict() for assessment in results_list],
                "summary": summary_data,
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出风险评估结果失败: {e}")
            return False
