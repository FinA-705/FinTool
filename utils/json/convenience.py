"""
便捷函数，用于简化JSON操作
"""

from typing import Any, Dict, Optional, Union
from pathlib import Path
from .helper import _global_helper, JSONHelper


def json_save(data: Any, file_path: Union[str, Path], **kwargs) -> bool:
    """保存数据到JSON文件

    Args:
        data: 要保存的数据
        file_path: 文件路径
        **kwargs: 其他参数

    Returns:
        是否保存成功
    """
    return _global_helper.save(data, file_path, **kwargs)


def json_load(file_path: Union[str, Path], default: Any = None, **kwargs) -> Any:
    """从JSON文件加载数据

    Args:
        file_path: 文件路径
        default: 默认值
        **kwargs: 其他参数

    Returns:
        加载的数据
    """
    return _global_helper.load(file_path, default, **kwargs)


def json_to_string(data: Any, **kwargs) -> str:
    """将数据转换为JSON字符串"""
    helper = JSONHelper(**kwargs)
    return helper.to_string(data)


def json_from_string(json_str: str, default: Any = None) -> Any:
    """从JSON字符串解析数据"""
    return _global_helper.from_string(json_str, default)


def json_merge(
    *files: Union[str, Path], output: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """合并JSON文件"""
    return _global_helper.merge(*files, output_file=output)


def json_validate(file_path: Union[str, Path]) -> bool:
    """验证JSON文件"""
    return _global_helper.validate(file_path)


def json_format(
    file_path: Union[str, Path], output: Optional[Union[str, Path]] = None
) -> bool:
    """格式化JSON文件"""
    return _global_helper.format_file(file_path, output)
