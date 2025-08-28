"""
REST API客户端基类
"""

from typing import Any, Dict, Union
from .helper import APIHelper
from .models import APIResponse


class RESTClient:
    """REST API客户端基类"""

    def __init__(self, base_url: str, **kwargs):
        """初始化REST客户端

        Args:
            base_url: 基础URL
            **kwargs: API助手参数
        """
        self.api = APIHelper(base_url=base_url, **kwargs)

    def list_resources(self, resource_path: str, **kwargs) -> APIResponse:
        """列出资源"""
        return self.api.get(resource_path, **kwargs)

    def get_resource(
        self, resource_path: str, resource_id: Union[str, int], **kwargs
    ) -> APIResponse:
        """获取单个资源"""
        endpoint = f"{resource_path}/{resource_id}"
        return self.api.get(endpoint, **kwargs)

    def create_resource(
        self, resource_path: str, data: Dict[str, Any], **kwargs
    ) -> APIResponse:
        """创建资源"""
        return self.api.post(resource_path, json_data=data, **kwargs)

    def update_resource(
        self,
        resource_path: str,
        resource_id: Union[str, int],
        data: Dict[str, Any],
        **kwargs,
    ) -> APIResponse:
        """更新资源"""
        endpoint = f"{resource_path}/{resource_id}"
        return self.api.put(endpoint, json_data=data, **kwargs)

    def delete_resource(
        self, resource_path: str, resource_id: Union[str, int], **kwargs
    ) -> APIResponse:
        """删除资源"""
        endpoint = f"{resource_path}/{resource_id}"
        return self.api.delete(endpoint, **kwargs)
