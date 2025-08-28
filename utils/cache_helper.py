"""
缓存工具

提供多种缓存策略和存储后端
支持内存缓存、文件缓存和自定义缓存
"""

import time
from pathlib import Path

from .cache.base import CacheBackend
from .cache.decorators import cached, memoize
from .cache.entry import CacheEntry, CachePolicy
from .cache.file_cache import FileCache
from .cache.manager import CacheManager, get_default_cache, set_default_cache
from .cache.memory_cache import MemoryCache


# 使用示例
if __name__ == "__main__":
    print("=== 缓存工具测试 ===")

    # 测试内存缓存
    print("\n1. 测试内存缓存:")
    memory_cache = MemoryCache(max_size=3, default_ttl=2)
    cache_manager = CacheManager(memory_cache)

    # 设置缓存
    cache_manager.set("key1", "value1")
    cache_manager.set("key2", "value2")
    cache_manager.set("key3", "value3")

    print(f"获取key1: {cache_manager.get('key1')}")
    print(f"获取key2: {cache_manager.get('key2')}")

    # 超出最大大小，触发LRU驱逐
    cache_manager.set("key4", "value4")
    print(f"设置key4后，key3: {cache_manager.get('key3')}")  # 应该还存在
    print(f"所有键: {cache_manager.keys()}")

    # 测试TTL
    print("\n2. 测试TTL:")
    cache_manager.set("temp_key", "temp_value", ttl=1)
    print(f"立即获取: {cache_manager.get('temp_key')}")

    time.sleep(1.1)
    print(f"1秒后获取: {cache_manager.get('temp_key')}")  # 应该为None

    # 测试文件缓存
    print("\n3. 测试文件缓存:")
    file_cache = FileCache("test_cache", serializer="json", default_ttl=10)
    file_cache_manager = CacheManager(file_cache)

    file_cache_manager.set("file_key", {"data": "测试数据", "number": 123})
    retrieved = file_cache_manager.get("file_key")
    print(f"文件缓存数据: {retrieved}")

    # 测试缓存装饰器
    print("\n4. 测试缓存装饰器:")

    @memoize(maxsize=10, ttl=5)
    def expensive_function(x, y):
        print(f"执行复杂计算: {x} + {y}")
        time.sleep(0.1)  # 模拟耗时操作
        return x + y

    # 第一次调用
    start_time = time.time()
    result1 = expensive_function(1, 2)
    time1 = time.time() - start_time
    print(f"第一次调用结果: {result1}, 耗时: {time1:.3f}秒")

    # 第二次调用（应该从缓存获取）
    start_time = time.time()
    result2 = expensive_function(1, 2)
    time2 = time.time() - start_time
    print(f"第二次调用结果: {result2}, 耗时: {time2:.3f}秒")

    print(f"缓存信息: {getattr(expensive_function, 'cache_info', lambda: {})()}")

    # 清理测试文件
    file_cache.clear()
    Path("test_cache").rmdir()

    print("\n测试完成！")
