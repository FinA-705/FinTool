"""
风险等级评估和报告生成
"""

from typing import List, Tuple
from .models import RiskMetrics, RiskLevel


class ReportGenerator:
    """风险报告生成器"""

    def assess_risk_level(self, metrics: RiskMetrics) -> Tuple[RiskLevel, float]:
        """评估风险等级和评分"""
        weights = {
            "volatility": 0.3,
            "max_drawdown": 0.25,
            "var": 0.2,
            "sharpe": 0.15,
            "sortino": 0.1,
        }
        vol_score = min(100, max(0, metrics.volatility * 100))
        dd_score = min(100, max(0, abs(metrics.max_drawdown) * 100))
        var_score = min(100, max(0, abs(metrics.var_95) * 200))
        sharpe_score = max(0, min(100, 50 - metrics.sharpe_ratio * 25))
        sortino_score = max(0, min(100, 50 - metrics.sortino_ratio * 25))

        risk_score = (
            vol_score * weights["volatility"]
            + dd_score * weights["max_drawdown"]
            + var_score * weights["var"]
            + sharpe_score * weights["sharpe"]
            + sortino_score * weights["sortino"]
        )

        if risk_score >= 80:
            risk_level = RiskLevel.VERY_HIGH
        elif risk_score >= 60:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 20:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.VERY_LOW
        return risk_level, round(risk_score, 2)

    def generate_warnings(self, metrics: RiskMetrics) -> List[str]:
        """生成风险警告"""
        warnings = []
        if metrics.volatility > 0.4:
            warnings.append("波动率过高，价格波动剧烈")
        if metrics.max_drawdown < -0.3:
            warnings.append("历史最大回撤较大，存在较高下跌风险")
        if metrics.var_95 < -0.1:
            warnings.append("单日潜在损失较大，风险集中度高")
        if metrics.sharpe_ratio < 0:
            warnings.append("风险调整后收益为负，投资效率低")
        if metrics.beta is not None and metrics.beta > 1.5:
            warnings.append("Beta系数过高，对市场波动敏感")
        if not warnings:
            warnings.append("暂无特别风险警告")
        return warnings

    def generate_recommendations(
        self, metrics: RiskMetrics, risk_level: RiskLevel
    ) -> List[str]:
        """生成投资建议"""
        recommendations = []
        if risk_level == RiskLevel.VERY_HIGH:
            recommendations.extend(
                ["风险极高，建议回避或严格控制仓位", "如持有需设置严格止损"]
            )
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend(["风险较高，建议小仓位参与", "密切关注市场变化"])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend(["风险适中，可适度配置", "建议分散投资"])
        elif risk_level == RiskLevel.LOW:
            recommendations.extend(["风险较低，可作为核心持仓", "适合长期持有"])
        else:
            recommendations.extend(["风险很低，优质的防御性标的", "适合稳健型投资者"])

        if metrics.sharpe_ratio > 1:
            recommendations.append("夏普比率优秀，风险调整后收益良好")
        if metrics.beta is not None and 0.8 <= metrics.beta <= 1.2:
            recommendations.append("Beta系数适中，与市场相关性合理")
        return recommendations
