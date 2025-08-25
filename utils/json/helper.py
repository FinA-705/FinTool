"""
JSON处理助手核心类
"""
import json
import gzip
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from .encoder import CustomJSONEncoder


class JSONHelper:
    """JSON处理助手

    提供统一的JSON读写接口和高级功能
    """

    def __init__(
        self,
        indent: int = 2,
        ensure_ascii: bool = False,
        sort_keys: bool = False,
        use_custom_encoder: bool = True,
    ):
        """初始化JSON助手

        Args:
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码
            sort_keys: 是否排序键名
            use_custom_encoder: 是否使用自定义编码器
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
        self.encoder_cls = CustomJSONEncoder if use_custom_encoder else None

    def save(
        self,
        data: Any,
        file_path: Union[str, Path],
        compress: bool = False,
        backup: bool = False,
    ) -> bool:
        """保存数据到JSON文件

        Args:
            data: 要保存的数据
            file_path: 文件路径
            compress: 是否压缩
            backup: 是否备份原文件

        Returns:
            是否保存成功
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f".backup.{file_path.suffix}")
                file_path.rename(backup_path)

            json_str = json.dumps(
                data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                sort_keys=self.sort_keys,
                cls=self.encoder_cls,
            )

            if compress:
                with gzip.open(f"{file_path}.gz", "wt", encoding="utf-8") as f:
                    f.write(json_str)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_str)
            return True
        except Exception as e:
            print(f"保存JSON文件失败: {e}")
            return False

    def load(
        self, file_path: Union[str, Path], default: Any = None, decompress: bool = False
    ) -> Any:
        """从JSON文件加载数据

        Args:
            file_path: 文件路径
            default: 加载失败时的默认值
            decompress: 是否解压缩

        Returns:
            加载的数据
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return default

            if decompress or file_path.suffix == ".gz":
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    content = f.read()
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            return json.loads(content)
        except Exception as e:
            print(f"加载JSON文件失败: {e}")
            return default

    def to_string(self, data: Any) -> str:
        """将数据转换为JSON字符串"""
        return json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=self.sort_keys,
            cls=self.encoder_cls,
        )

    def from_string(self, json_str: str, default: Any = None) -> Any:
        """从JSON字符串解析数据"""
        try:
            return json.loads(json_str)
        except Exception as e:
            print(f"解析JSON字符串失败: {e}")
            return default

    def merge(
        self,
        *json_files: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """合并多个JSON文件"""
        merged_data = {}
        for file_path in json_files:
            data = self.load(file_path, {})
            if isinstance(data, dict):
                merged_data.update(data)
            else:
                key = Path(file_path).stem
                merged_data[key] = data
        if output_file:
            self.save(merged_data, output_file)
        return merged_data

    def validate(self, file_path: Union[str, Path]) -> bool:
        """验证JSON文件格式"""
        try:
            data = self.load(file_path)
            return data is not None
        except Exception:
            return False

    def format_file(
        self,
        file_path: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
    ) -> bool:
        """格式化JSON文件"""
        try:
            data = self.load(file_path)
            if data is None:
                return False
            output_path = output_file or file_path
            return self.save(data, output_path)
        except Exception as e:
            print(f"格式化JSON文件失败: {e}")
            return False

    def filter_data(
        self,
        data: Dict[str, Any],
        include_keys: Optional[List[str]] = None,
        exclude_keys: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """过滤数据字段"""
        if not isinstance(data, dict):
            return data
        if include_keys:
            filtered_data = {k: v for k, v in data.items() if k in include_keys}
        else:
            filtered_data = data.copy()
        if exclude_keys:
            for key in exclude_keys:
                filtered_data.pop(key, None)
        return filtered_data

    def deep_merge(
        self, dict1: Dict[str, Any], dict2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并字典"""
        result = dict1.copy()
        for key, value in dict2.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self.deep_merge(result[key], value)
            else:
                result[key] = value
        return result

# 全局JSON助手实例
_global_helper = JSONHelper()
