"""
JSON Lines格式处理工具
"""

import json
from typing import Dict, List, Union, Any
from pathlib import Path
from .encoder import CustomJSONEncoder


def dict_to_json_lines(
    data_list: List[Dict[str, Any]], file_path: Union[str, Path]
) -> bool:
    """将字典列表保存为JSON Lines格式

    Args:
        data_list: 字典列表
        file_path: 文件路径

    Returns:
        是否保存成功
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            for item in data_list:
                json_line = json.dumps(item, ensure_ascii=False, cls=CustomJSONEncoder)
                f.write(json_line + "\n")

        return True
    except Exception as e:
        print(f"保存JSON Lines失败: {e}")
        return False


def json_lines_to_dict(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """从JSON Lines文件加载数据

    Args:
        file_path: 文件路径

    Returns:
        字典列表
    """
    data_list = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    data_list.append(data)
    except Exception as e:
        print(f"加载JSON Lines失败: {e}")

    return data_list
