"""
基于JSON的配置管理
"""
from typing import Any, Dict, Union
from pathlib import Path
from .helper import JSONHelper


class ConfigManager:
    """配置管理器

    基于JSON的配置文件管理
    """

    def __init__(self, config_file: Union[str, Path]):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.helper = JSONHelper()
        self._config = {}
        self.load()

    def load(self) -> bool:
        """加载配置"""
        self._config = self.helper.load(self.config_file, {})
        return isinstance(self._config, dict)

    def save(self) -> bool:
        """保存配置"""
        return self.helper.save(self._config, self.config_file)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> "ConfigManager":
        """设置配置值"""
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        return self

    def update(self, updates: Dict[str, Any]) -> "ConfigManager":
        """批量更新配置"""
        self._config.update(updates)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return self._config.copy()
