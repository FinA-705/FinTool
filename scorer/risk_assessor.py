"""
风险评估模块

计算波动率、最大回撤、VaR等风险指标
提供全面的风险分析和评估功能
"""

from .assessor import *
import warnings

warnings.filterwarnings("ignore")

# 使用示例
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from datetime import datetime

    # 创建示例价格数据
    dates = pd.date_range("2023-01-01", "2024-01-01", freq="D")
    np.random.seed(42)

    # 模拟股票价格走势
    returns = np.random.normal(0.0005, 0.02, len(dates))  # 日收益率
    prices = 100 * (1 + returns).cumprod()  # 累积价格
    price_series = pd.Series(prices, index=dates, name="000001.SZ")

    # 创建风险评估器
    assessor = RiskAssessor()

    # 评估风险
    assessment = assessor.assess_single(price_series)

    print(f"股票: {assessment.symbol}")
    print(f"风险等级: {assessment.risk_level.value}")
    print(f"风险评分: {assessment.risk_score}")
    print(f"年化波动率: {assessment.metrics.volatility:.2%}")
    print(f"最大回撤: {assessment.metrics.max_drawdown:.2%}")
    print(f"95% VaR: {assessment.metrics.var_95:.2%}")
    print(f"夏普比率: {assessment.metrics.sharpe_ratio:.2f}")
    print("\n风险警告:")
    for warning in assessment.warnings:
        print(f"- {warning}")
    print("\n投资建议:")
    for rec in assessment.recommendations:
        print(f"- {rec}")
