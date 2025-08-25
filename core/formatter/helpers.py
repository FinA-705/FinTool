"""
格式化器的辅助函数
"""
from typing import Any, Dict, List, Optional
from .models import ScoreDetails, AIAnalysis, StockRating, StockResult


def generate_recommendation(
    scores: ScoreDetails, ai_analysis: Optional[AIAnalysis] = None
) -> str:
    """生成投资推荐"""
    total_score = scores.total_score
    if ai_analysis:
        if ai_analysis.rating in [StockRating.STRONG_BUY, StockRating.BUY]:
            if total_score >= 80:
                return "强烈推荐"
            elif total_score >= 60:
                return "推荐"
            else:
                return "谨慎推荐"
        else:
            return "不推荐"
    else:
        if total_score >= 80:
            return "强烈推荐"
        elif total_score >= 60:
            return "推荐"
        elif total_score >= 40:
            return "中性"
        else:
            return "不推荐"


def generate_summary(stocks: List[StockResult]) -> Dict[str, Any]:
    """生成筛选摘要"""
    if not stocks:
        return {
            "total_stocks": 0,
            "avg_score": 0,
            "top_score": 0,
            "recommendations": {},
            "markets": {},
            "industries": {},
        }

    total_stocks = len(stocks)
    scores = [s.scores.total_score for s in stocks]
    avg_score = sum(scores) / total_stocks
    top_score = max(scores)

    recommendations = {}
    for stock in stocks:
        rec = stock.recommendation
        recommendations[rec] = recommendations.get(rec, 0) + 1

    markets = {}
    for stock in stocks:
        market = stock.stock_info.market
        markets[market] = markets.get(market, 0) + 1

    industries = {}
    for stock in stocks:
        industry = stock.stock_info.industry
        industries[industry] = industries.get(industry, 0) + 1

    return {
        "total_stocks": total_stocks,
        "avg_score": round(avg_score, 2),
        "top_score": round(top_score, 2),
        "score_distribution": {
            "excellent": len([s for s in scores if s >= 80]),
            "good": len([s for s in scores if 60 <= s < 80]),
            "fair": len([s for s in scores if 40 <= s < 60]),
            "poor": len([s for s in scores if s < 40]),
        },
        "recommendations": recommendations,
        "markets": markets,
        "industries": dict(list(industries.items())[:10]),
    }


def clean_dict(data: Any) -> Any:
    """递归清理字典数据，移除None值并将Enum转为值"""
    from enum import Enum
    if isinstance(data, dict):
        return {k: clean_dict(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [clean_dict(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    else:
        return data
