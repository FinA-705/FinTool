"""
数据导出器
"""
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
from dataclasses import asdict
from .models import ScreeningResult
from .helpers import clean_dict


class DataExporter:
    """数据导出器"""

    def __init__(self, output_dir: Union[str, Path] = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_json(
        self,
        result: ScreeningResult,
        filename: Optional[str] = None,
        pretty: bool = True,
    ) -> str:
        """导出为JSON格式"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screening_result_{timestamp}.json"
        file_path = self.output_dir / filename
        result_dict = asdict(result)
        result_dict = clean_dict(result_dict)
        with open(file_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            else:
                json.dump(result_dict, f, ensure_ascii=False)
        return str(file_path)

    def to_excel(
        self, result: ScreeningResult, filename: Optional[str] = None
    ) -> str:
        """导出为Excel格式"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screening_result_{timestamp}.xlsx"
        file_path = self.output_dir / filename
        stocks_data = []
        for stock in result.stocks:
            row = {
                "股票代码": stock.stock_info.symbol,
                "股票名称": stock.stock_info.name,
                "市场": stock.stock_info.market,
                "行业": stock.stock_info.industry,
                "总分": stock.scores.total_score,
                "价值评分": stock.scores.value_score,
                "质量评分": stock.scores.quality_score,
                "安全评分": stock.scores.safety_score,
                "成长评分": stock.scores.growth_score,
                "推荐": stock.recommendation,
                "当前价格": stock.current_price,
                "PE比率": stock.financial_metrics.pe_ratio,
                "PB比率": stock.financial_metrics.pb_ratio,
                "ROE": stock.financial_metrics.roe,
                "更新时间": stock.last_updated,
            }
            if stock.ai_analysis:
                row["AI评级"] = stock.ai_analysis.rating.value
                row["AI置信度"] = stock.ai_analysis.confidence
            stocks_data.append(row)

        df = pd.DataFrame(stocks_data)
        with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="股票筛选结果", index=False)
            summary_df = pd.DataFrame([result.summary])
            summary_df.to_excel(writer, sheet_name="筛选摘要", index=False)
            config_data = {
                "参数名": list(result.strategy_config.parameters.keys()),
                "参数值": list(result.strategy_config.parameters.values()),
            }
            config_df = pd.DataFrame(config_data)
            config_df.to_excel(writer, sheet_name="策略配置", index=False)
        return str(file_path)

    def to_csv(
        self, result: ScreeningResult, filename: Optional[str] = None
    ) -> str:
        """导出为CSV格式"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screening_result_{timestamp}.csv"
        file_path = self.output_dir / filename
        stocks_data = []
        for stock in result.stocks:
            row = {
                "symbol": stock.stock_info.symbol,
                "name": stock.stock_info.name,
                "market": stock.stock_info.market,
                "industry": stock.stock_info.industry,
                "total_score": stock.scores.total_score,
                "value_score": stock.scores.value_score,
                "quality_score": stock.scores.quality_score,
                "safety_score": stock.scores.safety_score,
                "growth_score": stock.scores.growth_score,
                "recommendation": stock.recommendation,
                "current_price": stock.current_price,
                "pe_ratio": stock.financial_metrics.pe_ratio,
                "pb_ratio": stock.financial_metrics.pb_ratio,
                "roe": stock.financial_metrics.roe,
                "last_updated": stock.last_updated,
            }
            if stock.ai_analysis:
                row["ai_rating"] = stock.ai_analysis.rating.value
                row["ai_confidence"] = stock.ai_analysis.confidence
            stocks_data.append(row)
        df = pd.DataFrame(stocks_data)
        df.to_csv(file_path, index=False, encoding="utf-8")
        return str(file_path)
