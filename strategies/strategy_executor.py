"""
策略执行器模块
"""
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from strategies.formula_parser import StrategyFormulaParser
from utils.logger import get_logger
from utils.validators import DataValidator

logger = get_logger(__name__)


class StrategyExecutor:
    """策略执行器，负责执行公式和数据处理"""

    def __init__(self):
        self.parser = StrategyFormulaParser()
        self.validator = DataValidator()

    def validate_input_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据"""
        if data.empty:
            return False

        # 检查必需字段
        required_fields = ["code", "close"]
        for field in required_fields:
            if field not in data.columns:
                logger.error(f"缺少必需字段: {field}")
                return False
        return True

    def prepare_variables(
        self, data: pd.DataFrame, constants: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """准备策略变量"""
        variables = self.parser._prepare_variables(data, constants)

        # 添加一些有用的计算字段
        if "close" in data.columns and len(data) > 1:
            variables["price_change"] = data["close"].pct_change().fillna(0).values
            variables["price_rank"] = data["close"].rank().values

        if "volume" in data.columns and len(data) > 1:
            variables["volume_rank"] = data["volume"].rank().values

        return variables

    def execute_filters(
        self, filters: List[str], data: pd.DataFrame, variables: Dict[str, Any]
    ) -> pd.DataFrame:
        """执行过滤条件"""
        current_data = data.copy()

        for filter_formula in filters:
            try:
                # 更新变量中的数据引用
                filter_variables = variables.copy()
                filter_variables.update(self.prepare_variables(current_data))

                # 执行过滤
                filter_result = self.parser.execute_formula(
                    filter_formula, current_data, filter_variables
                )

                if isinstance(filter_result, (pd.Series, np.ndarray)):
                    # 确保结果是布尔类型
                    if not str(filter_result.dtype).startswith("bool"):
                        filter_result = filter_result.astype(bool)

                    # 应用过滤
                    if len(filter_result) == len(current_data):
                        current_data = current_data.loc[filter_result]
                    else:
                        logger.warning(
                            f"过滤结果长度不匹配: {len(filter_result)} vs {len(current_data)}"
                        )
                elif not filter_result:
                    # 标量结果应用于所有行
                    current_data = current_data.iloc[0:0]  # 返回空DataFrame
                    break

            except Exception as e:
                logger.error(f"过滤条件执行失败: {filter_formula}, 错误: {e}")
                continue

        return current_data

    def execute_scoring(
        self, score_formula: str, data: pd.DataFrame, variables: Dict[str, Any]
    ) -> pd.Series:
        """执行评分"""
        try:
            score_variables = variables.copy()
            score_variables.update(self.prepare_variables(data))

            result = self.parser.execute_formula(score_formula, data, score_variables)

            if isinstance(result, (pd.Series, np.ndarray)):
                return pd.Series(result, index=data.index, name="score")
            else:
                # 标量结果扩展为所有行
                return pd.Series(result, index=data.index, name="score")

        except Exception as e:
            logger.error(f"评分公式执行失败: {score_formula}, 错误: {e}")
            return pd.Series(0.0, index=data.index, name="score")

    def execute_ranking(
        self, ranking_formula: str, data: pd.DataFrame, variables: Dict[str, Any]
    ) -> pd.Series:
        """执行排序"""
        try:
            ranking_variables = variables.copy()
            ranking_variables.update(self.prepare_variables(data))

            result = self.parser.execute_formula(
                ranking_formula, data, ranking_variables
            )

            if isinstance(result, (pd.Series, np.ndarray)):
                return pd.Series(result, index=data.index, name="ranking").rank(
                    ascending=False
                )
            else:
                return pd.Series(result, index=data.index, name="ranking").rank(
                    ascending=False
                )

        except Exception as e:
            logger.error(f"排序公式执行失败: {ranking_formula}, 错误: {e}")
            return pd.Series(range(len(data)), index=data.index, name="ranking")

    def execute_signals(
        self,
        signal_formulas: Dict[str, str],
        data: pd.DataFrame,
        variables: Dict[str, Any],
    ) -> pd.DataFrame:
        """执行信号计算"""
        signals = pd.DataFrame(index=data.index)

        for signal_name, signal_formula in signal_formulas.items():
            try:
                signal_variables = variables.copy()
                signal_variables.update(self.prepare_variables(data))

                result = self.parser.execute_formula(
                    signal_formula, data, signal_variables
                )

                if isinstance(result, (pd.Series, np.ndarray)):
                    signals[signal_name] = result
                else:
                    signals[signal_name] = result

            except Exception as e:
                logger.error(
                    f"信号公式执行失败: {signal_name}={signal_formula}, 错误: {e}"
                )
                signals[signal_name] = 0

        return signals
