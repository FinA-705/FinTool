"""
策略公式常量定义

包含预定义的财务字段、函数库和施洛斯策略常量
"""

from typing import Set


# 预定义的财务字段
FINANCIAL_FIELDS: Set[str] = {
    # 基础字段
    "price",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "market_cap",
    "pe",
    "pb",
    "ps",
    "pcf",
    "roe",
    "roa",
    "roic",
    "debt_ratio",
    "current_ratio",
    "quick_ratio",
    "gross_margin",
    "net_margin",
    "operating_margin",
    "revenue",
    "net_income",
    "total_assets",
    "total_debt",
    "free_cash_flow",
    "dividend_yield",
    # 技术指标
    "sma_5",
    "sma_10",
    "sma_20",
    "sma_50",
    "sma_200",
    "ema_5",
    "ema_10",
    "ema_20",
    "ema_50",
    "ema_200",
    "rsi",
    "macd",
    "macd_signal",
    "macd_hist",
    "bb_upper",
    "bb_middle",
    "bb_lower",
    "bb_width",
    "volume_sma",
    "price_change",
    "volume_change",
    # 风险指标
    "volatility",
    "beta",
    "sharpe_ratio",
    "max_drawdown",
    "var_95",
    "cvar_95",
    "calmar_ratio",
    "sortino_ratio",
    # 行业和市场
    "industry",
    "sector",
    "market",
    "listing_date",
    "trading_status",
    "is_st",
    "is_suspended",
}

# 预定义的函数库
FORMULA_FUNCTIONS: Set[str] = {
    # 数学函数
    "abs",
    "min",
    "max",
    "sum",
    "mean",
    "median",
    "std",
    "var",
    "sqrt",
    "log",
    "log10",
    "exp",
    "sin",
    "cos",
    "tan",
    "round",
    "ceil",
    "floor",
    "pow",
    # 技术分析函数
    "SMA",
    "EMA",
    "RSI",
    "MACD",
    "BOLLINGER",
    "STDEV",
    "CORR",
    "RETURN",
    "DRAWDOWN",
    "RANK",
    "PERCENTILE",
    # 逻辑函数
    "IF",
    "IFS",
    "AND",
    "OR",
    "NOT",
    "ISNULL",
    "ISNAN",
    # 时间函数
    "DAYS",
    "MONTHS",
    "YEARS",
    "TODAY",
    "DATE",
    # 聚合函数
    "COUNT",
    "UNIQUE",
    "DISTINCT",
    "GROUPBY",
}

# 施洛斯策略预定义常量
SCHLOSS_CONSTANTS = {
    "MIN_MARKET_CAP": 100000000,  # 最小市值1亿
    "MAX_PE": 15,  # 最大市盈率
    "MIN_CURRENT_RATIO": 1.5,  # 最小流动比率
    "MAX_DEBT_RATIO": 0.5,  # 最大负债率
    "MIN_ROE": 0.1,  # 最小ROE 10%
    "MIN_TRADING_DAYS": 252,  # 最小交易天数
    "BEAR_MARKET_THRESHOLD": -0.2,  # 熊市阈值
    "VALUE_PERCENTILE": 0.3,  # 价值股百分位
}
