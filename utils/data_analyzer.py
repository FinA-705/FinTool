"""
DataFrame数据分析工具

提供数据统计、分组、聚合等分析功能
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Callable, Literal


class DataAnalyzer:
    """数据分析器"""

    @staticmethod
    def basic_stats(
        df: pd.DataFrame, columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """基础统计信息

        Args:
            df: DataFrame对象
            columns: 指定列名

        Returns:
            统计信息DataFrame
        """
        if columns:
            target_df = df[columns]
        else:
            target_df = df.select_dtypes(include=[np.number])

        return target_df.describe()

    @staticmethod
    def correlation_matrix(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: Literal["pearson", "kendall", "spearman"] = "pearson",
    ) -> pd.DataFrame:
        """计算相关系数矩阵

        Args:
            df: DataFrame对象
            columns: 指定列名
            method: 计算方法

        Returns:
            相关系数矩阵
        """
        if columns:
            target_df = df[columns]
        else:
            target_df = df.select_dtypes(include=[np.number])

        return target_df.corr(method=method)

    @staticmethod
    def group_analysis(
        df: pd.DataFrame,
        group_cols: Union[str, List[str]],
        agg_cols: Optional[Union[str, List[str]]] = None,
        agg_func: str = "mean",
    ) -> pd.DataFrame:
        """分组聚合分析

        Args:
            df: DataFrame对象
            group_cols: 分组列
            agg_cols: 聚合列
            agg_func: 聚合函数

        Returns:
            分组聚合结果
        """
        grouped = df.groupby(group_cols)

        if agg_cols:
            if isinstance(agg_cols, str):
                agg_cols = [agg_cols]
            return grouped[agg_cols].agg(agg_func).reset_index()
        else:
            # 只对数值列进行聚合
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                return grouped[numeric_cols].agg(agg_func).reset_index()
            else:
                return grouped.size().reset_index(name="count")

    @staticmethod
    def value_counts_analysis(
        df: pd.DataFrame,
        column: str,
        normalize: bool = False,
        top_n: Optional[int] = None,
    ) -> pd.Series:
        """值计数分析

        Args:
            df: DataFrame对象
            column: 目标列
            normalize: 是否标准化
            top_n: 返回前N个

        Returns:
            值计数结果
        """
        result = df[column].value_counts(normalize=normalize)

        if top_n:
            result = result.head(top_n)

        return result

    @staticmethod
    def quantile_analysis(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        quantiles: List[float] = [0.25, 0.5, 0.75, 0.9, 0.95, 0.99],
    ) -> pd.DataFrame:
        """分位数分析

        Args:
            df: DataFrame对象
            columns: 指定列名
            quantiles: 分位数列表

        Returns:
            分位数分析结果
        """
        if columns:
            target_df = df[columns]
        else:
            target_df = df.select_dtypes(include=[np.number])

        return target_df.quantile(quantiles)

    @staticmethod
    def rolling_analysis(
        df: pd.DataFrame,
        columns: List[str],
        window: int,
        functions: List[str] = ["mean", "std", "min", "max"],
    ) -> pd.DataFrame:
        """滚动分析

        Args:
            df: DataFrame对象
            columns: 目标列
            window: 窗口大小
            functions: 计算函数

        Returns:
            滚动分析结果
        """
        result = df.copy()

        for col in columns:
            if col in df.columns:
                rolling = df[col].rolling(window=window)

                for func in functions:
                    new_col = f"{col}_{func}_{window}"
                    if hasattr(rolling, func):
                        result[new_col] = getattr(rolling, func)()

        return result

    @staticmethod
    def missing_pattern_analysis(df: pd.DataFrame) -> Dict[str, Any]:
        """缺失值模式分析

        Args:
            df: DataFrame对象

        Returns:
            缺失值分析结果
        """
        missing_data = df.isnull()

        analysis = {
            "总缺失值": missing_data.sum().sum(),
            "按列缺失值": missing_data.sum().to_dict(),
            "缺失值率": (missing_data.sum() / len(df) * 100).to_dict(),
            "完全缺失的列": missing_data.all()[missing_data.all()].index.tolist(),
            "完全不缺失的列": (~missing_data.any())[~missing_data.any()].index.tolist(),
            "缺失值模式": missing_data.value_counts().head(10).to_dict(),
        }

        return analysis

    @staticmethod
    def outlier_analysis(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> Dict[str, Any]:
        """异常值分析

        Args:
            df: DataFrame对象
            columns: 指定列名
            method: 检测方法
            threshold: 阈值

        Returns:
            异常值分析结果
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        outliers = {}

        for col in columns:
            if col not in df.columns:
                continue

            if method == "iqr":
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR

                outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)

            elif method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outlier_mask = z_scores > threshold

            else:
                continue

            outliers[col] = {
                "count": outlier_mask.sum(),
                "percentage": outlier_mask.sum() / len(df) * 100,
                "indices": df[outlier_mask].index.tolist(),
            }

        return outliers

    @staticmethod
    def time_series_analysis(
        df: pd.DataFrame, date_column: str, value_columns: List[str], freq: str = "D"
    ) -> pd.DataFrame:
        """时间序列分析

        Args:
            df: DataFrame对象
            date_column: 日期列
            value_columns: 数值列
            freq: 频率

        Returns:
            时间序列分析结果
        """
        result = df.copy()

        # 确保日期列是datetime类型
        if not pd.api.types.is_datetime64_any_dtype(result[date_column]):
            result[date_column] = pd.to_datetime(result[date_column])

        # 设置日期索引
        result = result.set_index(date_column)

        # 按频率重采样
        resampled = result[value_columns].resample(freq).agg(["mean", "sum", "count"])

        return resampled
