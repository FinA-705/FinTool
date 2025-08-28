"""
API请求工具

提供HTTP请求的封装和重试机制
支持常用的API调用模式和错误处理
"""

from .api.decorators import api_retry
from .api.helper import APIHelper
from .api.models import APIResponse, RequestMethod, RetryConfig
from .api.rest_client import RESTClient
from .api.utils import build_query_string, download_file, parse_url, quick_request

# 使用示例
if __name__ == "__main__":
    print("=== API工具测试 ===")

    # 创建API助手
    api = APIHelper(
        base_url="https://jsonplaceholder.typicode.com",
        timeout=10,
        default_headers={"User-Agent": "FinancialAgent/1.0"},
    )

    # 测试GET请求
    print("\n1. 测试GET请求:")
    response = api.get("/posts/1")
    print(f"状态码: {response.status_code}")
    print(f"成功: {response.success}")
    print(f"耗时: {response.elapsed_time:.2f}秒")
    if response.success:
        print(f"数据: {response.data}")

    # 测试POST请求
    print("\n2. 测试POST请求:")
    post_data = {"title": "测试标题", "body": "测试内容", "userId": 1}
    response = api.post("/posts", json_data=post_data)
    print(f"状态码: {response.status_code}")
    print(f"成功: {response.success}")
    if response.success:
        print(f"创建的数据: {response.data}")

    # 测试REST客户端
    print("\n3. 测试REST客户端:")
    client = RESTClient("https://jsonplaceholder.typicode.com")

    # 列出资源
    response = client.list_resources("/posts", params={"_limit": 3})
    print(f"列出资源 - 状态码: {response.status_code}")
    if response.success:
        print(f"获取到 {len(response.data)} 条记录")

    # 获取单个资源
    response = client.get_resource("/posts", 1)
    print(f"获取单个资源 - 状态码: {response.status_code}")

    # 测试批量请求
    print("\n4. 测试批量请求:")
    requests_data = [
        {"method": "GET", "endpoint": "/posts/1"},
        {"method": "GET", "endpoint": "/posts/2"},
        {"method": "GET", "endpoint": "/posts/3"},
    ]

    responses = api.batch_request(requests_data, max_concurrent=2)
    print(
        f"批量请求完成，成功: {sum(1 for r in responses if r.success)}/{len(responses)}"
    )

    # 测试URL解析
    print("\n5. 测试URL解析:")
    url_info = parse_url("https://api.example.com/v1/users?page=1&limit=10#section")
    print(f"URL解析结果: {url_info}")

    # 关闭会话
    api.close()
    client.api.close()

    print("\n测试完成！")
