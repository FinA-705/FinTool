"""
核心输出格式化器
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime

from .models import (
    StockInfo,
    ScoreDetails,
    FinancialMetrics,
    AIAnalysis,
    StockRating,
    StockResult,
    StrategyConfig,
    ExecutionInfo,
    ScreeningResult,
)
from .helpers import generate_recommendation, generate_summary
from .exporters import DataExporter


class CoreOutputFormatter:
    """
    核心输出格式化器
    功能：
    1. 生成标准化的数据结构
    2. 组合不同的数据部分形成完整结果
    3. 调用导出器完成文件输出
    """

    def __init__(self, output_dir: Union[str, Path] = "output"):
        self.exporter = DataExporter(output_dir)

    def format_stock_result(
        self,
        stock_data: Dict[str, Any],
        scores: Dict[str, float],
        ai_analysis: Optional[Dict[str, Any]] = None,
    ) -> StockResult:
        """格式化单个股票结果"""
        stock_info = StockInfo(
            symbol=stock_data.get("symbol", ""),
            name=stock_data.get("name", ""),
            market=stock_data.get("market", ""),
            sector=stock_data.get("sector", ""),
            industry=stock_data.get("industry", ""),
            market_cap=stock_data.get("market_cap"),
            currency=stock_data.get("currency", "CNY"),
        )
        score_details = ScoreDetails(
            total_score=scores.get("total_score", 0.0),
            value_score=scores.get("value_score", 0.0),
            quality_score=scores.get("quality_score", 0.0),
            safety_score=scores.get("safety_score", 0.0),
            growth_score=scores.get("growth_score", 0.0),
            ai_score=scores.get("ai_score"),
            risk_score=scores.get("risk_score"),
        )
        financial_metrics = FinancialMetrics(
            pe_ratio=stock_data.get("pe_ratio"),
            pb_ratio=stock_data.get("pb_ratio"),
            roe=stock_data.get("roe"),
            debt_ratio=stock_data.get("debt_ratio"),
            current_ratio=stock_data.get("current_ratio"),
            revenue_growth=stock_data.get("revenue_growth"),
            profit_growth=stock_data.get("profit_growth"),
            gross_margin=stock_data.get("gross_margin"),
            net_margin=stock_data.get("net_margin"),
        )
        ai_result = None
        if ai_analysis:
            ai_result = AIAnalysis(
                rating=StockRating(ai_analysis.get("rating", StockRating.HOLD.value)),
                confidence=ai_analysis.get("confidence", 0.5),
                reasoning=ai_analysis.get("reasoning", ""),
                key_strengths=ai_analysis.get("key_strengths", []),
                key_risks=ai_analysis.get("key_risks", []),
                price_target=ai_analysis.get("price_target"),
                investment_horizon=ai_analysis.get("investment_horizon", "中长期"),
            )
        recommendation = generate_recommendation(score_details, ai_result)
        return StockResult(
            stock_info=stock_info,
            scores=score_details,
            financial_metrics=financial_metrics,
            ai_analysis=ai_result,
            current_price=stock_data.get("current_price"),
            recommendation=recommendation,
        )

    def format_screening_result(
        self,
        stocks: List[StockResult],
        strategy_config: Dict[str, Any],
        execution_info: Dict[str, Any],
        summary: Optional[Dict[str, Any]] = None,
    ) -> ScreeningResult:
        """格式化完整筛选结果"""
        strategy = StrategyConfig(
            strategy_name=strategy_config.get("name", ""),
            version=strategy_config.get("version", "1.0"),
            parameters=strategy_config.get("parameters", {}),
            description=strategy_config.get("description", ""),
        )
        execution = ExecutionInfo(
            execution_id=execution_info.get("execution_id", ""),
            start_time=execution_info.get("start_time", ""),
            end_time=execution_info.get("end_time", ""),
            duration_seconds=execution_info.get("duration_seconds", 0.0),
            total_stocks_analyzed=execution_info.get("total_stocks_analyzed", 0),
            successful_analyses=execution_info.get("successful_analyses", 0),
            failed_analyses=execution_info.get("failed_analyses", 0),
            data_sources=execution_info.get("data_sources", []),
        )
        if summary is None:
            summary = generate_summary(stocks)
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "format_version": "2024.1",
            "total_results": len(stocks),
            "top_score": max((s.scores.total_score for s in stocks), default=0),
            "avg_score": (
                sum(s.scores.total_score for s in stocks) / len(stocks) if stocks else 0
            ),
        }
        return ScreeningResult(
            strategy_config=strategy,
            execution_info=execution,
            stocks=stocks,
            summary=summary,
            metadata=metadata,
        )

    def export_to_json(self, *args, **kwargs) -> str:
        return self.exporter.to_json(*args, **kwargs)

    def export_to_excel(self, *args, **kwargs) -> str:
        return self.exporter.to_excel(*args, **kwargs)

    def export_to_csv(self, *args, **kwargs) -> str:
        return self.exporter.to_csv(*args, **kwargs)
