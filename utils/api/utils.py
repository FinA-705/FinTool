"""
便捷函数和URL处理工具
"""
import urllib.parse
from typing import Any, Dict
from .helper import APIHelper
from .models import APIResponse


def quick_request(url: str, method: str = "GET", **kwargs) -> APIResponse:
    """快速请求"""
    api = APIHelper()
    return api.request(method, url, **kwargs)


def download_file(url: str, file_path: str, **kwargs) -> bool:
    """下载文件"""
    api = APIHelper()
    return api.download_file(url, file_path, **kwargs)


def build_query_string(params: Dict[str, Any]) -> str:
    """构建查询字符串"""
    return urllib.parse.urlencode(params)


def parse_url(url: str) -> Dict[str, Any]:
    """解析URL"""
    parsed = urllib.parse.urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": dict(urllib.parse.parse_qsl(parsed.query)),
        "fragment": parsed.fragment,
    }
