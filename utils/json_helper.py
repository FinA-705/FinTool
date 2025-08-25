"""
JSON处理工具

提供便捷的JSON读写和处理功能
支持多种数据格式的序列化和反序列化
"""

from .json import *
from .json.helper import JSONHelper, _global_helper
from .json.encoder import CustomJSONEncoder
from .json.config import ConfigManager

# For backward compatibility, we can keep the old names if needed
JSONEncoder = CustomJSONEncoder


# 使用示例
if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    from datetime import datetime
    from decimal import Decimal

    print("=== JSON工具测试 ===")

    # 测试数据
    test_data = {
        "name": "测试数据",
        "timestamp": datetime.now(),
        "values": [1, 2, 3, 4, 5],
        "metrics": {
            "accuracy": 0.95,
            "precision": np.float64(0.88),
            "recall": Decimal("0.92"),
        },
        "dataframe": pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}),
    }

    # 测试保存和加载
    print("\n1. 测试JSON保存和加载:")
    success = json_save(test_data, "test_output/test_data.json")
    print(f"保存结果: {'成功' if success else '失败'}")

    loaded_data = json_load("test_output/test_data.json")
    print(f"加载结果: {'成功' if loaded_data else '失败'}")

    # 测试字符串转换
    print("\n2. 测试字符串转换:")
    json_str = json_to_string({"test": "value"})
    print(f"JSON字符串: {json_str}")

    parsed_data = json_from_string(json_str)
    print(f"解析结果: {parsed_data}")

    # 测试配置管理
    print("\n3. 测试配置管理:")
    config = ConfigManager("test_output/config.json")
    config.set("database.host", "localhost").set("database.port", 5432).set(
        "api.timeout", 30
    )

    config.save()
    print(f"数据库主机: {config.get('database.host')}")
    print(f"API超时: {config.get('api.timeout')}")

    print("\n测试完成！")
