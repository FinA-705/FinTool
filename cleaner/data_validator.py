"""
数据验证和缺失值处理模块

负责数据质量检查、异常值识别和缺失值填充
"""

from typing import Dict, List, Optional, Any, Union, Callable
import pandas as pd
import numpy as np
from enum import Enum
from .field_mapper import StandardFields


class MissingValueStrategy(Enum):
    """缺失值处理策略"""

    DROP = "drop"  # 删除包含缺失值的行
    FILL_ZERO = "fill_zero"  # 用0填充
    FILL_MEAN = "fill_mean"  # 用均值填充
    FILL_MEDIAN = "fill_median"  # 用中位数填充
    FILL_MODE = "fill_mode"  # 用众数填充
    FILL_FORWARD = "fill_forward"  # 前向填充
    FILL_BACKWARD = "fill_backward"  # 后向填充
    INTERPOLATE = "interpolate"  # 线性插值
    CUSTOM = "custom"  # 自定义填充值


class OutlierDetectionMethod(Enum):
    """异常值检测方法"""

    IQR = "iqr"  # 四分位距法
    Z_SCORE = "z_score"  # Z分数法
    MODIFIED_Z_SCORE = "modified_z_score"  # 修正Z分数法
    ISOLATION_FOREST = "isolation_forest"  # 孤立森林
    CUSTOM = "custom"  # 自定义方法


class DataValidator:
    """数据验证和处理器"""

    def __init__(self):
        self._validation_rules = self._initialize_validation_rules()
        self._default_strategies = self._initialize_default_strategies()

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化数据验证规则"""
        return {
            StandardFields.PE_RATIO: {
                "min_value": 0,
                "max_value": 1000,
                "data_type": "float",
                "allow_negative": False,
            },
            StandardFields.PB_RATIO: {
                "min_value": 0,
                "max_value": 100,
                "data_type": "float",
                "allow_negative": False,
            },
            StandardFields.PS_RATIO: {
                "min_value": 0,
                "max_value": 1000,
                "data_type": "float",
                "allow_negative": False,
            },
            StandardFields.ROE: {
                "min_value": -1,
                "max_value": 1,
                "data_type": "float",
                "allow_negative": True,
            },
            StandardFields.ROA: {
                "min_value": -1,
                "max_value": 1,
                "data_type": "float",
                "allow_negative": True,
            },
            StandardFields.DEBT_RATIO: {
                "min_value": 0,
                "max_value": 1,
                "data_type": "float",
                "allow_negative": False,
            },
            StandardFields.VOLUME: {
                "min_value": 0,
                "data_type": "int",
                "allow_negative": False,
            },
            StandardFields.MARKET_CAP: {
                "min_value": 0,
                "data_type": "float",
                "allow_negative": False,
            },
            StandardFields.CLOSE: {
                "min_value": 0,
                "data_type": "float",
                "allow_negative": False,
            },
        }

    def _initialize_default_strategies(self) -> Dict[str, MissingValueStrategy]:
        """初始化默认的缺失值处理策略"""
        return {
            StandardFields.PE_RATIO: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.PB_RATIO: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.PS_RATIO: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.ROE: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.ROA: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.DEBT_RATIO: MissingValueStrategy.FILL_MEDIAN,
            StandardFields.VOLUME: MissingValueStrategy.FILL_ZERO,
            StandardFields.MARKET_CAP: MissingValueStrategy.DROP,
            StandardFields.CLOSE: MissingValueStrategy.DROP,
            StandardFields.SYMBOL: MissingValueStrategy.DROP,
            StandardFields.NAME: MissingValueStrategy.DROP,
        }

    def validate_data_types(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """
        验证数据类型

        Args:
            data: 要验证的数据框

        Returns:
            验证结果字典，包含错误信息
        """
        errors = {}

        for column in data.columns:
            if column in self._validation_rules:
                rules = self._validation_rules[column]
                expected_type = rules.get("data_type")

                if expected_type:
                    column_errors = []

                    if expected_type == "float":
                        # 检查是否可以转换为浮点数
                        try:
                            pd.to_numeric(data[column], errors="raise")
                        except (ValueError, TypeError):
                            column_errors.append(
                                f"列 {column} 包含无法转换为浮点数的值"
                            )

                    elif expected_type == "int":
                        # 检查是否可以转换为整数
                        try:
                            pd.to_numeric(
                                data[column], errors="raise", downcast="integer"
                            )
                        except (ValueError, TypeError):
                            column_errors.append(f"列 {column} 包含无法转换为整数的值")

                    if column_errors:
                        errors[column] = column_errors

        return errors

    def validate_value_ranges(self, data: pd.DataFrame) -> Dict[str, List[str]]:
        """
        验证数值范围

        Args:
            data: 要验证的数据框

        Returns:
            验证结果字典，包含错误信息
        """
        errors = {}

        for column in data.columns:
            if column in self._validation_rules:
                rules = self._validation_rules[column]
                column_errors = []

                # 转换为数值类型进行验证
                numeric_data = pd.to_numeric(data[column], errors="coerce")

                # 检查最小值
                min_value = rules.get("min_value")
                if min_value is not None:
                    invalid_count = (numeric_data < min_value).sum()
                    if invalid_count > 0:
                        column_errors.append(
                            f"列 {column} 有 {invalid_count} 个值小于最小值 {min_value}"
                        )

                # 检查最大值
                max_value = rules.get("max_value")
                if max_value is not None:
                    invalid_count = (numeric_data > max_value).sum()
                    if invalid_count > 0:
                        column_errors.append(
                            f"列 {column} 有 {invalid_count} 个值大于最大值 {max_value}"
                        )

                # 检查负值
                allow_negative = rules.get("allow_negative", True)
                if not allow_negative:
                    negative_count = (numeric_data < 0).sum()
                    if negative_count > 0:
                        column_errors.append(f"列 {column} 有 {negative_count} 个负值")

                if column_errors:
                    errors[column] = column_errors

        return errors

    def detect_outliers(
        self,
        data: pd.DataFrame,
        method: OutlierDetectionMethod = OutlierDetectionMethod.IQR,
        threshold: float = 3.0,
    ) -> Dict[str, pd.Index]:
        """
        检测异常值

        Args:
            data: 要检测的数据框
            method: 检测方法
            threshold: 阈值

        Returns:
            异常值索引字典
        """
        outliers = {}

        for column in data.select_dtypes(include=[np.number]).columns:
            column_data = data[column].dropna()

            if len(column_data) == 0:
                continue

            if method == OutlierDetectionMethod.IQR:
                Q1 = column_data.quantile(0.25)
                Q3 = column_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_mask = (column_data < lower_bound) | (column_data > upper_bound)

            elif method == OutlierDetectionMethod.Z_SCORE:
                z_scores = np.abs(
                    (column_data - column_data.mean()) / column_data.std()
                )
                outlier_mask = z_scores > threshold

            elif method == OutlierDetectionMethod.MODIFIED_Z_SCORE:
                median = column_data.median()
                mad = np.median(np.abs(column_data - median))
                if mad != 0:
                    modified_z_scores = 0.6745 * (column_data - median) / float(mad)
                    outlier_mask = np.abs(modified_z_scores) > threshold
                else:
                    outlier_mask = pd.Series(
                        [False] * len(column_data), index=column_data.index
                    )

            else:
                continue

            if outlier_mask.any():
                outliers[column] = column_data[outlier_mask].index

        return outliers

    def handle_missing_values(
        self,
        data: pd.DataFrame,
        strategies: Optional[Dict[str, MissingValueStrategy]] = None,
        custom_values: Optional[Dict[str, Any]] = None,
    ) -> pd.DataFrame:
        """
        处理缺失值

        Args:
            data: 要处理的数据框
            strategies: 处理策略字典
            custom_values: 自定义填充值字典

        Returns:
            处理后的数据框
        """
        if strategies is None:
            strategies = self._default_strategies

        if custom_values is None:
            custom_values = {}

        result = data.copy()

        for column in result.columns:
            if column not in strategies:
                continue

            strategy = strategies[column]

            if not result[column].isna().any():
                continue

            if strategy == MissingValueStrategy.DROP:
                result = result.dropna(subset=[column])

            elif strategy == MissingValueStrategy.FILL_ZERO:
                result[column] = result[column].fillna(0)

            elif strategy == MissingValueStrategy.FILL_MEAN:
                if result[column].dtype in ["int64", "float64"]:
                    result[column] = result[column].fillna(result[column].mean())

            elif strategy == MissingValueStrategy.FILL_MEDIAN:
                if result[column].dtype in ["int64", "float64"]:
                    result[column] = result[column].fillna(result[column].median())

            elif strategy == MissingValueStrategy.FILL_MODE:
                mode_value = result[column].mode()
                if len(mode_value) > 0:
                    result[column] = result[column].fillna(mode_value.iloc[0])

            elif strategy == MissingValueStrategy.FILL_FORWARD:
                result[column] = result[column].ffill()

            elif strategy == MissingValueStrategy.FILL_BACKWARD:
                result[column] = result[column].bfill()

            elif strategy == MissingValueStrategy.INTERPOLATE:
                if result[column].dtype in ["int64", "float64"]:
                    result[column] = result[column].interpolate()

            elif strategy == MissingValueStrategy.CUSTOM:
                if column in custom_values:
                    result[column] = result[column].fillna(custom_values[column])

        return result

    def clean_data(
        self,
        data: pd.DataFrame,
        remove_outliers: bool = False,
        outlier_method: OutlierDetectionMethod = OutlierDetectionMethod.IQR,
        missing_strategies: Optional[Dict[str, MissingValueStrategy]] = None,
    ) -> pd.DataFrame:
        """
        综合数据清洗

        Args:
            data: 要清洗的数据框
            remove_outliers: 是否移除异常值
            outlier_method: 异常值检测方法
            missing_strategies: 缺失值处理策略

        Returns:
            清洗后的数据框
        """
        result = data.copy()

        # 1. 处理缺失值
        result = self.handle_missing_values(result, missing_strategies)

        # 2. 移除异常值（如果需要）
        if remove_outliers:
            outliers = self.detect_outliers(result, outlier_method)
            outlier_indices = set()
            for indices in outliers.values():
                outlier_indices.update(indices)

            if outlier_indices:
                result = result.drop(index=list(outlier_indices))

        # 3. 重置索引
        result = result.reset_index(drop=True)

        return result

    def add_validation_rule(self, field: str, rule: Dict[str, Any]):
        """
        添加验证规则

        Args:
            field: 字段名
            rule: 验证规则
        """
        self._validation_rules[field] = rule

    def get_data_quality_report(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成数据质量报告

        Args:
            data: 要分析的数据框

        Returns:
            数据质量报告
        """
        report = {
            "total_rows": len(data),
            "total_columns": len(data.columns),
            "missing_values": {},
            "data_types": {},
            "value_ranges": {},
            "outliers_count": {},
        }

        # 缺失值统计
        for column in data.columns:
            missing_count = data[column].isna().sum()
            missing_percentage = missing_count / len(data) * 100
            report["missing_values"][column] = {
                "count": int(missing_count),
                "percentage": round(missing_percentage, 2),
            }

        # 数据类型统计
        report["data_types"] = {col: str(dtype) for col, dtype in data.dtypes.items()}

        # 数值范围统计
        for column in data.select_dtypes(include=[np.number]).columns:
            column_data = data[column].dropna()
            if len(column_data) > 0:
                report["value_ranges"][column] = {
                    "min": float(column_data.min()),
                    "max": float(column_data.max()),
                    "mean": float(column_data.mean()),
                    "median": float(column_data.median()),
                    "std": float(column_data.std()),
                }

        # 异常值统计
        outliers = self.detect_outliers(data)
        for column, indices in outliers.items():
            report["outliers_count"][column] = len(indices)

        return report
