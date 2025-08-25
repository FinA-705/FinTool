"""
DataFrame数据清洗工具

提供数据清洗、去重、缺失值处理等功能
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple, Literal
import warnings


class DataCleaner:
    """数据清洗器"""

    @staticmethod
    def remove_duplicates(
        df: pd.DataFrame,
        subset: Optional[List[str]] = None,
        keep: Literal["first", "last", False] = "first",
    ) -> pd.DataFrame:
        """删除重复行

        Args:
            df: DataFrame对象
            subset: 判断重复的列名列表
            keep: 保留策略

        Returns:
            清洗后的DataFrame
        """
        return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)

    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        method: str = "drop",
        fill_value: Any = None,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """处理缺失值

        Args:
            df: DataFrame对象
            method: 处理方法 (drop, fill, forward, backward)
            fill_value: 填充值
            columns: 指定列名

        Returns:
            处理后的DataFrame
        """
        target_df = df.copy()

        if columns:
            target_df = (
                target_df[columns] if set(columns).issubset(df.columns) else target_df
            )

        if method == "drop":
            return df.dropna()
        elif method == "fill":
            if fill_value is not None:
                if columns:
                    df[columns] = df[columns].fillna(fill_value)
                    return df
                else:
                    return df.fillna(fill_value)
            else:
                # 数值列用均值填充，字符串列用众数填充
                result = df.copy()
                for col in df.columns:
                    if df[col].dtype in ["int64", "float64"]:
                        result[col] = result[col].fillna(result[col].mean())
                    else:
                        mode_value = result[col].mode()
                        if len(mode_value) > 0:
                            result[col] = result[col].fillna(mode_value[0])
                return result
        elif method == "forward":
            return df.ffill()
        elif method == "backward":
            return df.bfill()
        else:
            return df

    @staticmethod
    def remove_outliers(
        df: pd.DataFrame,
        columns: List[str],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> pd.DataFrame:
        """删除异常值

        Args:
            df: DataFrame对象
            columns: 目标列名
            method: 检测方法 (iqr, zscore)
            threshold: 阈值

        Returns:
            清洗后的DataFrame
        """
        result = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            if method == "iqr":
                Q1 = result[col].quantile(0.25)
                Q3 = result[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR

                result = result[
                    (result[col] >= lower_bound) & (result[col] <= upper_bound)
                ]

            elif method == "zscore":
                z_scores = np.abs(
                    (result[col] - result[col].mean()) / result[col].std()
                )
                result = result[z_scores <= threshold]

        return result.reset_index(drop=True)

    @staticmethod
    def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名

        Args:
            df: DataFrame对象

        Returns:
            标准化后的DataFrame
        """
        result = df.copy()

        # 转为小写并替换空格和特殊字符
        new_columns = []
        for col in result.columns:
            new_col = str(col).lower()
            new_col = new_col.replace(" ", "_")
            new_col = new_col.replace("-", "_")
            new_col = new_col.replace(".", "_")
            new_col = new_col.replace("(", "")
            new_col = new_col.replace(")", "")
            new_columns.append(new_col)

        result.columns = new_columns
        return result

    @staticmethod
    def convert_dtypes(df: pd.DataFrame, dtype_mapping: Dict[str, str]) -> pd.DataFrame:
        """转换数据类型

        Args:
            df: DataFrame对象
            dtype_mapping: 数据类型映射字典

        Returns:
            转换后的DataFrame
        """
        result = df.copy()

        for col, dtype in dtype_mapping.items():
            if col in result.columns:
                try:
                    if dtype == "datetime":
                        result[col] = pd.to_datetime(result[col])
                    elif dtype == "category":
                        result[col] = result[col].astype("category")
                    elif dtype in ["int", "int64"]:
                        result[col] = result[col].astype("int64")
                    elif dtype in ["float", "float64"]:
                        result[col] = result[col].astype("float64")
                    elif dtype in ["str", "string", "object"]:
                        result[col] = result[col].astype("object")
                    else:
                        # 使用eval安全地转换其他类型
                        try:
                            result[col] = result[col].astype(eval(dtype))
                        except:
                            warnings.warn(f"未知数据类型: {dtype}")
                            pass
                except Exception as e:
                    warnings.warn(f"转换列 {col} 类型失败: {e}")

        return result

    @staticmethod
    def trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
        """去除字符串列的前后空格

        Args:
            df: DataFrame对象

        Returns:
            处理后的DataFrame
        """
        result = df.copy()

        string_columns = result.select_dtypes(include=["object"]).columns
        for col in string_columns:
            result[col] = result[col].astype(str).str.strip()

        return result

    @staticmethod
    def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """验证数据质量

        Args:
            df: DataFrame对象

        Returns:
            数据质量报告
        """
        report = {
            "总行数": len(df),
            "总列数": len(df.columns),
            "缺失值统计": {},
            "重复行数": df.duplicated().sum(),
            "数据类型": df.dtypes.to_dict(),
            "内存使用": df.memory_usage(deep=True).sum(),
        }

        # 缺失值统计
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_rate = missing_count / len(df) * 100
            report["缺失值统计"][col] = {
                "缺失数量": missing_count,
                "缺失率": f"{missing_rate:.2f}%",
            }

        return report
