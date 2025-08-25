"""
缓存管理器模块
支持 SQLite 数据库缓存和本地文件缓存，提供统一的缓存接口
"""

import json
import sqlite3
import pickle
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import threading
from contextlib import contextmanager


class CacheType(Enum):
    """缓存类型枚举"""

    SQLITE = "sqlite"
    FILE = "file"
    MEMORY = "memory"


@dataclass
class CacheConfig:
    """缓存配置"""

    cache_type: CacheType = CacheType.SQLITE
    cache_dir: str = "cache"
    max_memory_size: int = 1000  # 内存缓存最大条目数
    default_ttl: int = 3600  # 默认TTL（秒）
    sqlite_file: str = "cache.db"
    enable_compression: bool = False


@dataclass
class CacheItem:
    """缓存项"""

    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_access: float = 0


class MemoryCache:
    """内存缓存实现"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, CacheItem] = {}
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None

            item = self.cache[key]
            current_time = time.time()

            # 检查是否过期
            if current_time > item.created_at + item.ttl:
                del self.cache[key]
                return None

            # 更新访问统计
            item.access_count += 1
            item.last_access = current_time

            return item.value

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        with self.lock:
            current_time = time.time()

            # 如果缓存已满，删除最久未访问的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()

            self.cache[key] = CacheItem(
                key=key,
                value=value,
                created_at=current_time,
                ttl=ttl,
                access_count=1,
                last_access=current_time,
            )

    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def cleanup_expired(self):
        """清理过期缓存"""
        with self.lock:
            current_time = time.time()
            expired_keys = []

            for key, item in self.cache.items():
                if current_time > item.created_at + item.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

    def _evict_lru(self):
        """删除最久未访问的项"""
        if not self.cache:
            return

        lru_key = min(self.cache.keys(), key=lambda k: self.cache[k].last_access)
        del self.cache[lru_key]


class SQLiteCache:
    """SQLite 缓存实现"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_items (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    ttl INTEGER,
                    access_count INTEGER DEFAULT 0,
                    last_access REAL
                )
            """
            )

            # 创建索引
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_last_access
                ON cache_items(last_access)
            """
            )

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        try:
            yield conn
        finally:
            conn.close()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT value, created_at, ttl FROM cache_items
                    WHERE key = ?
                """,
                    (key,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                value_blob, created_at, ttl = row
                current_time = time.time()

                # 检查是否过期
                if current_time > created_at + ttl:
                    conn.execute("DELETE FROM cache_items WHERE key = ?", (key,))
                    conn.commit()
                    return None

                # 更新访问统计
                conn.execute(
                    """
                    UPDATE cache_items
                    SET access_count = access_count + 1, last_access = ?
                    WHERE key = ?
                """,
                    (current_time, key),
                )
                conn.commit()

                # 反序列化值
                try:
                    return pickle.loads(value_blob)
                except Exception:
                    return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        with self.lock:
            try:
                value_blob = pickle.dumps(value)
                current_time = time.time()

                with self._get_connection() as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cache_items
                        (key, value, created_at, ttl, access_count, last_access)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """,
                        (key, value_blob, current_time, ttl, current_time),
                    )
                    conn.commit()

            except Exception as e:
                print(f"缓存设置失败: {e}")

    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM cache_items WHERE key = ?", (key,))
                conn.commit()
                return cursor.rowcount > 0

    def clear(self):
        """清空缓存"""
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM cache_items")
                conn.commit()

    def cleanup_expired(self):
        """清理过期缓存"""
        with self.lock:
            current_time = time.time()
            with self._get_connection() as conn:
                conn.execute(
                    """
                    DELETE FROM cache_items
                    WHERE created_at + ttl < ?
                """,
                    (current_time,),
                )
                conn.commit()


class FileCache:
    """文件缓存实现"""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希避免文件名冲突
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            try:
                with open(file_path, "rb") as f:
                    cache_data = pickle.load(f)

                current_time = time.time()

                # 检查是否过期
                if current_time > cache_data["created_at"] + cache_data["ttl"]:
                    file_path.unlink()
                    return None

                return cache_data["value"]

            except Exception:
                # 文件损坏，删除
                if file_path.exists():
                    file_path.unlink()
                return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存值"""
        with self.lock:
            file_path = self._get_file_path(key)

            cache_data = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "ttl": ttl,
            }

            try:
                with open(file_path, "wb") as f:
                    pickle.dump(cache_data, f)
            except Exception as e:
                print(f"文件缓存设置失败: {e}")

    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self.lock:
            file_path = self._get_file_path(key)

            if file_path.exists():
                file_path.unlink()
                return True
            return False

    def clear(self):
        """清空缓存"""
        with self.lock:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink()

    def cleanup_expired(self):
        """清理过期缓存"""
        with self.lock:
            current_time = time.time()

            for file_path in self.cache_dir.glob("*.cache"):
                try:
                    with open(file_path, "rb") as f:
                        cache_data = pickle.load(f)

                    # 检查是否过期
                    if current_time > cache_data["created_at"] + cache_data["ttl"]:
                        file_path.unlink()

                except Exception:
                    # 文件损坏，删除
                    file_path.unlink()


class CoreCacheManager:
    """
    核心缓存管理器
    功能：
    1. 支持多种缓存后端（内存、SQLite、文件）
    2. TTL 支持
    3. 缓存命名空间
    4. 缓存统计
    5. 过期清理
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.caches: Dict[str, Union[MemoryCache, SQLiteCache, FileCache]] = {}
        self.lock = threading.RLock()
        self._init_default_cache()

    def _init_default_cache(self):
        """初始化默认缓存"""
        self.get_cache("default")

    def get_cache(
        self, namespace: str = "default"
    ) -> Union[MemoryCache, SQLiteCache, FileCache]:
        """获取指定命名空间的缓存实例"""
        with self.lock:
            if namespace in self.caches:
                return self.caches[namespace]

            cache_dir = Path(self.config.cache_dir) / namespace

            if self.config.cache_type == CacheType.MEMORY:
                cache = MemoryCache(self.config.max_memory_size)
            elif self.config.cache_type == CacheType.SQLITE:
                db_path = cache_dir / self.config.sqlite_file
                cache = SQLiteCache(db_path)
            elif self.config.cache_type == CacheType.FILE:
                cache = FileCache(cache_dir)
            else:
                raise ValueError(f"不支持的缓存类型: {self.config.cache_type}")

            self.caches[namespace] = cache
            return cache

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """获取缓存值"""
        cache = self.get_cache(namespace)
        return cache.get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default",
    ):
        """设置缓存值"""
        if ttl is None:
            ttl = self.config.default_ttl

        cache = self.get_cache(namespace)
        cache.set(key, value, ttl)

    def delete(self, key: str, namespace: str = "default") -> bool:
        """删除缓存项"""
        cache = self.get_cache(namespace)
        return cache.delete(key)

    def clear(self, namespace: str = "default"):
        """清空指定命名空间的缓存"""
        cache = self.get_cache(namespace)
        cache.clear()

    def clear_all(self):
        """清空所有缓存"""
        with self.lock:
            for cache in self.caches.values():
                cache.clear()

    def cleanup_expired(self, namespace: Optional[str] = None):
        """清理过期缓存"""
        if namespace:
            cache = self.get_cache(namespace)
            if hasattr(cache, "cleanup_expired"):
                cache.cleanup_expired()
        else:
            # 清理所有命名空间
            for cache in self.caches.values():
                if hasattr(cache, "cleanup_expired"):
                    cache.cleanup_expired()

    def get_stats(self, namespace: str = "default") -> Dict[str, Any]:
        """获取缓存统计信息"""
        cache = self.get_cache(namespace)

        if isinstance(cache, MemoryCache):
            return {
                "type": "memory",
                "size": len(cache.cache),
                "max_size": cache.max_size,
            }
        elif isinstance(cache, SQLiteCache):
            try:
                with cache._get_connection() as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM cache_items")
                    count = cursor.fetchone()[0]
                    return {
                        "type": "sqlite",
                        "size": count,
                        "db_path": str(cache.db_path),
                    }
            except Exception:
                return {"type": "sqlite", "size": 0}
        elif isinstance(cache, FileCache):
            cache_files = list(cache.cache_dir.glob("*.cache"))
            return {
                "type": "file",
                "size": len(cache_files),
                "cache_dir": str(cache.cache_dir),
            }
        else:
            return {"type": "unknown", "size": 0}


# 全局缓存管理器实例
cache_manager = CoreCacheManager()
