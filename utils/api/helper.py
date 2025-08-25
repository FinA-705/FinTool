"""
API请求助手核心类
"""
import requests
import time
from typing import Any, Dict, Optional, Union, Callable, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .models import RequestMethod, APIResponse, RetryConfig


class APIHelper:
    """API请求助手

    提供统一的API请求接口和高级功能
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry_config: Optional[RetryConfig] = None,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """初始化API助手

        Args:
            base_url: 基础URL
            timeout: 超时时间
            retry_config: 重试配置
            default_headers: 默认请求头
        """
        self.base_url = base_url.rstrip("/") if base_url else None
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.default_headers = default_headers or {}
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建会话对象"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.retry_config.max_retries,
            backoff_factor=self.retry_config.backoff_factor,
            status_forcelist=self.retry_config.status_forcelist,
            allowed_methods=self.retry_config.allowed_methods,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.default_headers)
        return session

    def _build_url(self, endpoint: str) -> str:
        """构建完整URL"""
        if endpoint.startswith(("http://", "https://")):
            return endpoint
        if self.base_url:
            return f"{self.base_url}/{endpoint.lstrip('/')}"
        return endpoint

    def _prepare_request(
        self,
        method: RequestMethod,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """准备请求参数"""
        url = self._build_url(endpoint)
        request_kwargs = {
            "method": method.value,
            "url": url,
            "timeout": kwargs.get("timeout", self.timeout),
            "params": params,
            "headers": headers,
        }
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = data
        for key in ["auth", "cookies", "files", "verify", "cert", "proxies"]:
            if key in kwargs:
                request_kwargs[key] = kwargs[key]
        return request_kwargs

    def request(
        self, method: Union[RequestMethod, str], endpoint: str, **kwargs
    ) -> APIResponse:
        """发送HTTP请求"""
        if isinstance(method, str):
            method = RequestMethod(method.upper())
        start_time = time.time()
        try:
            request_kwargs = self._prepare_request(method, endpoint, **kwargs)
            response = self.session.request(**request_kwargs)
            elapsed_time = time.time() - start_time
            try:
                data = response.json()
            except ValueError:
                data = response.text
            return APIResponse(
                status_code=response.status_code,
                data=data,
                headers=dict(response.headers),
                url=response.url,
                elapsed_time=elapsed_time,
                success=response.ok,
                error_message=None if response.ok else f"HTTP {response.status_code}",
            )
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            return APIResponse(
                status_code=0,
                data=None,
                headers={},
                url=self._build_url(endpoint),
                elapsed_time=elapsed_time,
                success=False,
                error_message=str(e),
            )

    def get(self, endpoint: str, **kwargs) -> APIResponse:
        """GET请求"""
        return self.request(RequestMethod.GET, endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> APIResponse:
        """POST请求"""
        return self.request(RequestMethod.POST, endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> APIResponse:
        """PUT请求"""
        return self.request(RequestMethod.PUT, endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> APIResponse:
        """DELETE请求"""
        return self.request(RequestMethod.DELETE, endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> APIResponse:
        """PATCH请求"""
        return self.request(RequestMethod.PATCH, endpoint, **kwargs)

    def download_file(
        self,
        url: str,
        file_path: str,
        chunk_size: int = 8192,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """下载文件"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            return True
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False

    def upload_file(
        self,
        endpoint: str,
        file_path: str,
        field_name: str = "file",
        additional_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> APIResponse:
        """上传文件"""
        try:
            with open(file_path, "rb") as f:
                files = {field_name: f}
                data = additional_data or {}
                return self.post(endpoint, files=files, data=data, **kwargs)
        except Exception as e:
            return APIResponse(
                status_code=0,
                data=None,
                headers={},
                url=self._build_url(endpoint),
                elapsed_time=0,
                success=False,
                error_message=f"上传文件失败: {e}",
            )

    def batch_request(
        self,
        requests_data: List[Dict[str, Any]],
        max_concurrent: int = 5,
        delay_between_requests: float = 0,
    ) -> List[APIResponse]:
        """批量请求"""
        import threading
        import queue

        responses: List[Optional[APIResponse]] = [None] * len(requests_data)
        request_queue = queue.Queue()
        for i, req_data in enumerate(requests_data):
            request_queue.put((i, req_data))

        def worker():
            while True:
                try:
                    index, req_data = request_queue.get(timeout=1)
                    method = req_data.pop("method", "GET")
                    endpoint = req_data.pop("endpoint")
                    response = self.request(method, endpoint, **req_data)
                    responses[index] = response
                    if delay_between_requests > 0:
                        time.sleep(delay_between_requests)
                    request_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"批量请求失败: {e}")
                    request_queue.task_done()

        threads = []
        for _ in range(min(max_concurrent, len(requests_data))):
            t = threading.Thread(target=worker)
            t.start()
            threads.append(t)
        request_queue.join()
        for t in threads:
            t.join()
        return [r for r in responses if r is not None]

    def set_auth(self, auth_type: str, **kwargs):
        """设置认证"""
        if auth_type == "basic":
            username = kwargs.get("username")
            password = kwargs.get("password")
            if username and password:
                self.session.auth = (username, password)
        elif auth_type == "bearer":
            token = kwargs.get("token")
            if token:
                self.session.headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "custom":
            header_name = kwargs.get("header_name", "Authorization")
            header_value = kwargs.get("header_value")
            if header_value:
                self.session.headers[header_name] = header_value

    def set_proxy(self, proxy_url: str):
        """设置代理"""
        self.session.proxies = {"http": proxy_url, "https": proxy_url}

    def close(self):
        """关闭会话"""
        self.session.close()
