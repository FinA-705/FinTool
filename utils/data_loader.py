"""
DataFrame数据加载工具

提供各种数据源的DataFrame加载功能
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
import json
import warnings


class DataLoader:
    """数据加载器"""

    @staticmethod
    def load_csv(
        file_path: Union[str, Path], encoding: str = "utf-8", **kwargs
    ) -> Optional[pd.DataFrame]:
        """加载CSV文件

        Args:
            file_path: 文件路径
            encoding: 编码格式
            **kwargs: pandas参数

        Returns:
            DataFrame对象
        """
        try:
            # 尝试不同编码
            encodings = [encoding, "utf-8", "gbk", "gb2312", "latin1"]

            for enc in encodings:
                try:
                    return pd.read_csv(file_path, encoding=enc, **kwargs)
                except UnicodeDecodeError:
                    continue

            print(f"无法使用任何编码读取文件: {file_path}")
            return None

        except Exception as e:
            print(f"加载CSV文件失败: {e}")
            return None

    @staticmethod
    def load_excel(
        file_path: Union[str, Path], sheet_name: Union[str, int] = 0, **kwargs
    ) -> Optional[pd.DataFrame]:
        """加载Excel文件

        Args:
            file_path: 文件路径
            sheet_name: 工作表名称或索引
            **kwargs: pandas参数

        Returns:
            DataFrame对象
        """
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
        except Exception as e:
            print(f"加载Excel文件失败: {e}")
            return None

    @staticmethod
    def load_json(
        file_path: Union[str, Path], encoding: str = "utf-8", **kwargs
    ) -> Optional[pd.DataFrame]:
        """加载JSON文件

        Args:
            file_path: 文件路径
            encoding: 编码格式
            **kwargs: pandas参数

        Returns:
            DataFrame对象
        """
        try:
            return pd.read_json(file_path, encoding=encoding, **kwargs)
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            return None

    @staticmethod
    def load_parquet(file_path: Union[str, Path], **kwargs) -> Optional[pd.DataFrame]:
        """加载Parquet文件

        Args:
            file_path: 文件路径
            **kwargs: pandas参数

        Returns:
            DataFrame对象
        """
        try:
            return pd.read_parquet(file_path, **kwargs)
        except Exception as e:
            print(f"加载Parquet文件失败: {e}")
            return None

    @staticmethod
    def save_to_csv(
        df: pd.DataFrame, file_path: Union[str, Path], encoding: str = "utf-8", **kwargs
    ) -> bool:
        """保存为CSV文件

        Args:
            df: DataFrame对象
            file_path: 文件路径
            encoding: 编码格式
            **kwargs: pandas参数

        Returns:
            是否成功
        """
        try:
            df.to_csv(file_path, encoding=encoding, index=False, **kwargs)
            return True
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
            return False

    @staticmethod
    def save_to_excel(
        df: pd.DataFrame,
        file_path: Union[str, Path],
        sheet_name: str = "Sheet1",
        **kwargs,
    ) -> bool:
        """保存为Excel文件

        Args:
            df: DataFrame对象
            file_path: 文件路径
            sheet_name: 工作表名称
            **kwargs: pandas参数

        Returns:
            是否成功
        """
        try:
            df.to_excel(file_path, sheet_name=sheet_name, index=False, **kwargs)
            return True
        except Exception as e:
            print(f"保存Excel文件失败: {e}")
            return False

    @staticmethod
    def save_to_parquet(
        df: pd.DataFrame, file_path: Union[str, Path], **kwargs
    ) -> bool:
        """保存为Parquet文件

        Args:
            df: DataFrame对象
            file_path: 文件路径
            **kwargs: pandas参数

        Returns:
            是否成功
        """
        try:
            df.to_parquet(file_path, index=False, **kwargs)
            return True
        except Exception as e:
            print(f"保存Parquet文件失败: {e}")
            return False
