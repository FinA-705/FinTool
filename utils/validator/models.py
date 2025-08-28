"""
验证器相关的数据模型和枚举
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Callable, Dict, List


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """格式化错误消息"""
        if self.field:
            return f"字段 '{self.field}' 验证失败: {self.message} (值: {self.value})"
        return self.message


class ValidationType(Enum):
    """验证类型枚举"""

    REQUIRED = "required"
    TYPE = "type"
    RANGE = "range"
    FORMAT = "format"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """验证规则"""

    type: ValidationType
    message: str
    validator: Optional[Callable] = None
    params: Optional[Dict[str, Any]] = None
