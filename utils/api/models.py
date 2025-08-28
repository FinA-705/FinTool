"""
API请求相关的枚举和数据类
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class RequestMethod(Enum):
    """HTTP请求方法枚举"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class APIResponse:
    """API响应数据类"""

    status_code: int
    data: Any
    headers: Dict[str, str]
    url: str
    elapsed_time: float
    success: bool
    error_message: Optional[str] = None


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: Optional[List[int]] = None,
        allowed_methods: Optional[List[str]] = None,
    ):
        """初始化重试配置

        Args:
            max_retries: 最大重试次数
            backoff_factor: 退避因子
            status_forcelist: 强制重试的状态码
            allowed_methods: 允许重试的方法
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.status_forcelist = status_forcelist or [500, 502, 503, 504]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE"]
