"""
JSON处理工具包

提供便捷的JSON读写、处理、转换和配置管理功能。
"""

from .encoder import CustomJSONEncoder
from .helper import JSONHelper
from .convenience import (
    json_save,
    json_load,
    json_to_string,
    json_from_string,
    json_merge,
    json_validate,
    json_format,
)
from .dataframe import (
    dataframe_to_json,
    json_to_dataframe,
)
from .json_lines import (
    dict_to_json_lines,
    json_lines_to_dict,
)
from .config import ConfigManager

__all__ = [
    "CustomJSONEncoder",
    "JSONHelper",
    "json_save",
    "json_load",
    "json_to_string",
    "json_from_string",
    "json_merge",
    "json_validate",
    "json_format",
    "dataframe_to_json",
    "json_to_dataframe",
    "dict_to_json_lines",
    "json_lines_to_dict",
    "ConfigManager",
]
