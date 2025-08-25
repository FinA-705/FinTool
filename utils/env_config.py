"""
环境配置管理模块

负责读取和管理环境变量配置，包括从 .env 文件加载配置。
支持多种数据源的 API 配置，包括 baseurl 等自定义配置。
"""

import os
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging
from dotenv import load_dotenv


class EnvConfig:
    """
    环境配置管理类

    负责加载和管理环境变量，支持从 .env 文件读取配置。
    提供类型安全的配置访问方法。
    """

    def __init__(self, env_file: Optional[Union[str, Path]] = None):
        """
        初始化环境配置

        Args:
            env_file: .env 文件路径，如果为 None 则自动查找
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self._config_cache: Dict[str, Any] = {}

        # 加载环境变量
        self._load_env_file(env_file)
        self._cache_configs()

    def _load_env_file(self, env_file: Optional[Union[str, Path]] = None):
        """
        加载 .env 文件

        Args:
            env_file: .env 文件路径
        """
        if env_file is None:
            # 自动查找 .env 文件
            current_dir = Path.cwd()
            possible_paths = [
                current_dir / ".env",
                current_dir / "config" / ".env",
                current_dir.parent / ".env",
            ]

            for path in possible_paths:
                if path.exists():
                    env_file = path
                    break

        if env_file and Path(env_file).exists():
            load_dotenv(env_file, override=True)
            self.logger.info(f"已加载环境配置文件: {env_file}")
        else:
            self.logger.warning("未找到 .env 文件，将使用系统环境变量")

    def _cache_configs(self):
        """缓存常用配置"""
        # 应用配置
        self._config_cache["environment"] = self.get_str("ENVIRONMENT", "development")
        self._config_cache["debug"] = self.get_bool("DEBUG", False)
        self._config_cache["log_level"] = self.get_str("LOG_LEVEL", "INFO")

        # 数据源配置
        self._config_cache["tushare_token"] = self.get_str("TUSHARE_TOKEN")
        self._config_cache["tushare_baseurl"] = self.get_str(
            "TUSHARE_BASEURL", "http://api.tushare.pro"
        )

        # OpenAI 配置
        self._config_cache["openai_api_key"] = self.get_str("OPENAI_API_KEY")
        self._config_cache["openai_baseurl"] = self.get_str(
            "OPENAI_BASEURL"
        ) or self.get_str("AI_BASE_URL", "https://api.openai.com/v1")
        self._config_cache["openai_model"] = self.get_str("OPENAI_MODEL", "gpt-4")

        # Anthropic 配置
        self._config_cache["anthropic_api_key"] = self.get_str("ANTHROPIC_API_KEY")
        self._config_cache["anthropic_baseurl"] = self.get_str(
            "ANTHROPIC_BASEURL", "https://api.anthropic.com"
        )

        # 数据库配置
        self._config_cache["database_url"] = self.get_str(
            "DATABASE_URL", "sqlite:///data/financial_agent.db"
        )
        self._config_cache["redis_url"] = self.get_str(
            "REDIS_URL", "redis://localhost:6379/0"
        )

        # Web应用配置
        self._config_cache["webapp_host"] = self.get_str("WEBAPP_HOST", "0.0.0.0")
        self._config_cache["webapp_port"] = self.get_int("WEBAPP_PORT", 8000)
        self._config_cache["webapp_debug"] = self.get_bool("WEBAPP_DEBUG", False)

        # 安全配置
        self._config_cache["secret_key"] = self.get_str("SECRET_KEY")
        self._config_cache["jwt_secret"] = self.get_str("JWT_SECRET")

        # 缓存配置
        self._config_cache["cache_type"] = self.get_str("CACHE_TYPE", "sqlite")
        self._config_cache["cache_expire_hours"] = self.get_int(
            "CACHE_EXPIRE_HOURS", 24
        )

        # 性能配置
        self._config_cache["max_workers"] = self.get_int("MAX_WORKERS", 4)
        self._config_cache["request_timeout"] = self.get_int("REQUEST_TIMEOUT", 30)
        self._config_cache["batch_size"] = self.get_int("BATCH_SIZE", 100)

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取字符串类型的环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        value = os.getenv(key, default)
        return value if value != "" else default

    def get_int(self, key: str, default: int = 0) -> int:
        """
        获取整数类型的环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        value = os.getenv(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            self.logger.warning(
                f"环境变量 {key} 值 '{value}' 不是有效整数，使用默认值 {default}"
            )
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        获取浮点数类型的环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        value = os.getenv(key)
        if value is None:
            return default

        try:
            return float(value)
        except ValueError:
            self.logger.warning(
                f"环境变量 {key} 值 '{value}' 不是有效浮点数，使用默认值 {default}"
            )
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        获取布尔类型的环境变量

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值或默认值
        """
        value = os.getenv(key)
        if value is None:
            return default

        # 将字符串转换为布尔值
        return value.lower() in ("true", "1", "yes", "on", "enable", "enabled")

    def get_list(
        self, key: str, separator: str = ",", default: Optional[list] = None
    ) -> list:
        """
        获取列表类型的环境变量

        Args:
            key: 环境变量名
            separator: 分隔符
            default: 默认值

        Returns:
            环境变量值列表或默认值
        """
        value = os.getenv(key)
        if value is None:
            return default or []

        return [item.strip() for item in value.split(separator) if item.strip()]

    def require(self, key: str) -> str:
        """
        获取必需的环境变量，如果不存在则抛出异常

        Args:
            key: 环境变量名

        Returns:
            环境变量值

        Raises:
            ValueError: 如果环境变量不存在或为空
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"必需的环境变量 {key} 未设置或为空")
        return value

    # 便捷属性访问方法
    @property
    def environment(self) -> str:
        """应用环境"""
        return self._config_cache["environment"]

    @property
    def debug(self) -> bool:
        """调试模式"""
        return self._config_cache["debug"]

    @property
    def log_level(self) -> str:
        """日志级别"""
        return self._config_cache["log_level"]

    # Tushare 配置
    @property
    def tushare_token(self) -> Optional[str]:
        """Tushare API Token"""
        return self._config_cache["tushare_token"]

    @property
    def tushare_baseurl(self) -> str:
        """Tushare API 基础URL"""
        return self._config_cache["tushare_baseurl"]

    # OpenAI 配置
    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API Key"""
        return self._config_cache["openai_api_key"]

    @property
    def openai_baseurl(self) -> str:
        """OpenAI API 基础URL"""
        return self._config_cache["openai_baseurl"]

    @property
    def openai_model(self) -> str:
        """OpenAI 模型名称"""
        return self._config_cache["openai_model"]

    # Anthropic 配置
    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Anthropic API Key"""
        return self._config_cache["anthropic_api_key"]

    @property
    def anthropic_baseurl(self) -> str:
        """Anthropic API 基础URL"""
        return self._config_cache["anthropic_baseurl"]

    # 数据库配置
    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        return self._config_cache["database_url"]

    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        return self._config_cache["redis_url"]

    # Web应用配置
    @property
    def webapp_host(self) -> str:
        """Web应用主机地址"""
        return self._config_cache["webapp_host"]

    @property
    def webapp_port(self) -> int:
        """Web应用端口"""
        return self._config_cache["webapp_port"]

    @property
    def webapp_debug(self) -> bool:
        """Web应用调试模式"""
        return self._config_cache["webapp_debug"]

    # 安全配置
    @property
    def secret_key(self) -> Optional[str]:
        """应用密钥"""
        return self._config_cache["secret_key"]

    @property
    def jwt_secret(self) -> Optional[str]:
        """JWT密钥"""
        return self._config_cache["jwt_secret"]

    # 缓存配置
    @property
    def cache_type(self) -> str:
        """缓存类型"""
        return self._config_cache["cache_type"]

    @property
    def cache_expire_hours(self) -> int:
        """缓存过期时间（小时）"""
        return self._config_cache["cache_expire_hours"]

    # 性能配置
    @property
    def max_workers(self) -> int:
        """最大工作线程数"""
        return self._config_cache["max_workers"]

    @property
    def request_timeout(self) -> int:
        """请求超时时间（秒）"""
        return self._config_cache["request_timeout"]

    @property
    def batch_size(self) -> int:
        """批处理大小"""
        return self._config_cache["batch_size"]

    def get_data_source_config(self, source: str) -> Dict[str, Any]:
        """
        获取指定数据源的配置

        Args:
            source: 数据源名称 (tushare, openai, anthropic)

        Returns:
            数据源配置字典
        """
        if source.lower() == "tushare":
            return {
                "token": self.tushare_token,
                "baseurl": self.tushare_baseurl,
                "timeout": self.request_timeout,
                "retry_times": 3,
            }
        elif source.lower() == "openai":
            return {
                "api_key": self.openai_api_key,
                "baseurl": self.openai_baseurl,
                "model": self.openai_model,
                "timeout": self.request_timeout,
            }
        elif source.lower() == "anthropic":
            return {
                "api_key": self.anthropic_api_key,
                "baseurl": self.anthropic_baseurl,
                "timeout": self.request_timeout,
            }
        else:
            return {}

    def get_all_config(self) -> Dict[str, Any]:
        """
        获取所有配置（隐藏敏感信息）

        Returns:
            配置字典
        """
        config = self._config_cache.copy()

        # 隐藏敏感信息
        sensitive_keys = [
            "tushare_token",
            "openai_api_key",
            "anthropic_api_key",
            "secret_key",
            "jwt_secret",
        ]

        for key in sensitive_keys:
            if config.get(key):
                config[key] = "***hidden***"

        return config

    def validate_required_configs(self) -> tuple[bool, list]:
        """
        验证必需的配置项

        Returns:
            (是否所有必需配置都存在, 缺失的配置列表)
        """
        required_configs = []
        missing_configs = []

        # 根据环境检查必需配置
        if self.environment == "production":
            required_configs.extend(["secret_key", "jwt_secret"])

        # 检查数据源配置（至少需要一个）
        has_data_source = any([self.tushare_token, self.openai_api_key])

        if not has_data_source:
            missing_configs.append("至少需要一个数据源API密钥")

        # 检查具体配置
        for config in required_configs:
            if not self._config_cache.get(config):
                missing_configs.append(config)

        return len(missing_configs) == 0, missing_configs

    def reload(self, env_file: Optional[Union[str, Path]] = None):
        """
        重新加载环境配置

        Args:
            env_file: .env 文件路径
        """
        self._config_cache.clear()
        self._load_env_file(env_file)
        self._cache_configs()
        self.logger.info("环境配置已重新加载")

    def __repr__(self) -> str:
        return f"EnvConfig(environment={self.environment}, debug={self.debug})"


# 全局配置实例
env_config = EnvConfig()
