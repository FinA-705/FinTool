"""
数据验证工具

提供通用的数据验证功能
支持股票代码、日期范围、数值数据等验证
"""

from .validator.core import DataValidator, ValidationError
from .validator.helpers import (
    ensure_numeric_range,
    ensure_valid_date_range,
    ensure_valid_stock_code,
)
from .validator.models import ValidationRule
from .validator.presets import (
    validate_date_range,
    validate_numeric_data,
    validate_stock_code,
)

# 使用示例
if __name__ == "__main__":
    import numpy as np

    print("=== 数据验证工具测试 ===")

    # 测试股票代码验证
    print("\n1. 股票代码验证:")
    test_codes = ["000001.SZ", "600000.SH", "00700.HK", "AAPL", "INVALID"]
    for code in test_codes:
        valid = validate_stock_code(code)
        print(f"  {code}: {'有效' if valid else '无效'}")

    # 测试日期范围验证
    print("\n2. 日期范围验证:")
    date_ranges = [
        ("2023-01-01", "2023-12-31"),
        ("2023-06-01", "2023-01-01"),  # 无效
        ("invalid", "2023-12-31"),  # 无效
    ]
    for start, end in date_ranges:
        valid = validate_date_range(start, end)
        print(f"  {start} 到 {end}: {'有效' if valid else '无效'}")

    # 测试数值验证
    print("\n3. 数值验证:")
    test_values = [10, -5, 100.5, "abc", None, np.nan]
    for val in test_values:
        valid = validate_numeric_data(val, min_val=0, max_val=100)
        print(f"  {val}: {'有效' if valid else '无效'}")

    # 测试DataValidator
    print("\n4. 数据验证器:")
    validator = DataValidator()
    validator.required("name", "姓名不能为空").type_check(
        "age", int, "年龄必须是整数"
    ).range_check("score", 0, 100, "分数必须在0-100之间")

    test_data = [
        {"name": "张三", "age": 25, "score": 85},  # 有效
        {"name": "", "age": 25, "score": 85},  # 姓名为空
        {"name": "李四", "age": "25", "score": 85},  # 年龄类型错误
        {"name": "王五", "age": 30, "score": 150},  # 分数超范围
    ]

    for i, data in enumerate(test_data):
        try:
            valid = validator.validate(data, raise_on_error=False)
            if not valid:
                print(f"  数据{i+1} 验证失败:")
                for error in validator.get_errors():
                    print(f"    - {error.message}")
            else:
                print(f"  数据{i+1} 验证通过")
        except Exception as e:
            print(f"  数据{i+1} 验证异常: {e}")

    print("\n测试完成！")
