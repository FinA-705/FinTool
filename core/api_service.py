"""
API服务模块，用于集成和管理核心服务
"""

from core.config_manager import CoreConfigManager
from core.cache_manager import CoreCacheManager
from utils.logger import get_logger


class APIService:
    """
    API服务类，用于封装和管理核心服务
    """

    def __init__(self):
        self.config_manager = CoreConfigManager()
        self.cache_manager = CoreCacheManager(self.config_manager.get_config("cache"))
        self.logger = get_logger("APIService")
        self._data_cache = {}

    def initialize(self):
        """初始化所有服务"""
        self.config_manager.load_config("application", "config/config.yaml")
        self.logger.info("API服务已初始化")

    def shutdown(self):
        """关闭所有服务"""
        self.logger.info("API服务已关闭")

    def get_cached_data(self, key: str):
        """获取缓存数据"""
        return self._data_cache.get(key)

    def set_cached_data(self, key: str, value, ttl: int = 300):
        """设置缓存数据"""
        # 简单的内存缓存，可以根据需要替换为更复杂的实现
        self._data_cache[key] = value
