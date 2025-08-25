"""
Pandas DataFrame与JSON的转换工具
"""
from typing import Optional, Union, Literal
from pathlib import Path
import pandas as pd
from .convenience import json_save, json_load


def dataframe_to_json(
    df: pd.DataFrame,
    file_path: Union[str, Path],
    orient: Literal[
        "dict", "list", "series", "split", "tight", "records", "index"
    ] = "records",
    **kwargs,
) -> bool:
    """将DataFrame保存为JSON

    Args:
        df: DataFrame对象
        file_path: 文件路径
        orient: 输出格式
        **kwargs: 其他参数

    Returns:
        是否保存成功
    """
    try:
        data = df.to_dict(orient)
        return json_save(data, file_path, **kwargs)
    except Exception as e:
        print(f"DataFrame转JSON失败: {e}")
        return False


def json_to_dataframe(file_path: Union[str, Path], **kwargs) -> Optional[pd.DataFrame]:
    """从JSON文件加载DataFrame

    Args:
        file_path: 文件路径
        **kwargs: pandas参数

    Returns:
        DataFrame对象
    """
    try:
        data = json_load(file_path)
        if data is None:
            return None

        return pd.DataFrame(data, **kwargs)
    except Exception as e:
        print(f"JSON转DataFrame失败: {e}")
        return None
