"""
自定义JSON编码器
"""

import json
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import numpy as np
from enum import Enum


class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器

    支持更多Python数据类型的序列化
    """

    def default(self, o):
        """重写默认编码方法"""

        # 处理日期时间
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, date):
            return o.isoformat()

        # 处理数值类型
        elif isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()

        # 处理Pandas对象
        elif isinstance(o, pd.Series):
            return o.to_dict()
        elif isinstance(o, pd.DataFrame):
            return o.to_dict("records")
        elif isinstance(o, pd.Timestamp):
            return o.isoformat()

        # 处理枚举
        elif isinstance(o, Enum):
            return o.value

        # 处理集合类型
        elif isinstance(o, set):
            return list(o)

        # 处理复数
        elif isinstance(o, complex):
            return {"real": o.real, "imag": o.imag, "__complex__": True}

        # 处理NaN和无穷大
        elif isinstance(o, float):
            if np.isnan(o):
                return None
            elif np.isinf(o):
                return str(o)

        return super().default(o)
