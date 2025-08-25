"""
API请求相关的装饰器
"""
import time
from .models import APIResponse


def rate_limit(calls_per_second: float):
    """限流装饰器"""
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret

        return wrapper

    return decorator


def api_retry(max_retries: int = 3, delay: float = 1.0):
    """API重试装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, APIResponse) and result.success:
                        return result
                    elif not isinstance(result, APIResponse):
                        return result
                except Exception as e:
                    last_exception = e
                if attempt < max_retries:
                    time.sleep(delay * (2**attempt))  # 指数退避
            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator
