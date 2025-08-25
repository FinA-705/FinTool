"""
配置管理器模块
支持 YAML/JSON 配置热加载、配置验证、环境变量覆盖等功能
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml
from dataclasses import dataclass
import threading
from enum import Enum


class ConfigFormat(Enum):
    """配置文件格式枚举"""

    YAML = "yaml"
    JSON = "json"
    YML = "yml"


@dataclass
class ConfigValidationRule:
    """配置验证规则"""

    key_path: str  # 配置键路径，如 "database.host"
    required: bool = True
    data_type: type = str
    default_value: Any = None
    validator_func: Optional[Callable[[Any], bool]] = None


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变更监听器"""

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

    def on_modified(self, event):
        """文件修改时触发"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path in self.config_manager.watched_files:
                self.config_manager._reload_config(file_path)


class CoreConfigManager:
    """
    核心配置管理器
    功能：
    1. 支持 YAML/JSON 配置文件加载
    2. 配置文件热更新监听
    3. 环境变量覆盖
    4. 配置验证
    5. 配置缓存
    """

    def __init__(self, config_dir: Union[str, Path] = "config"):
        self.config_dir = Path(config_dir)
        self.configs: Dict[str, Dict] = {}
        self.watched_files: Dict[Path, float] = {}  # 文件路径 -> 最后修改时间
        self.validation_rules: List[ConfigValidationRule] = []
        self.observer = None  # Observer 实例
        self.callbacks: Dict[str, List[Callable]] = {}  # 配置变更回调
        self.lock = threading.RLock()

    def add_validation_rule(self, rule: ConfigValidationRule):
        """添加配置验证规则"""
        self.validation_rules.append(rule)

    def register_change_callback(
        self, config_name: str, callback: Callable[[str, Dict], None]
    ):
        """注册配置变更回调函数"""
        if config_name not in self.callbacks:
            self.callbacks[config_name] = []
        self.callbacks[config_name].append(callback)

    def load_config(
        self,
        config_name: str,
        file_path: Optional[Union[str, Path]] = None,
        watch: bool = True,
    ) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_name: 配置名称
            file_path: 配置文件路径，如果为None则在config_dir中查找
            watch: 是否启用热更新监听

        Returns:
            配置字典
        """
        with self.lock:
            if file_path is None:
                # 自动查找配置文件
                file_path = self._find_config_file(config_name)
            else:
                file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {file_path}")

            # 加载配置文件
            config_data = self._load_file(file_path)

            # 应用环境变量覆盖
            config_data = self._apply_env_overrides(config_data, config_name)

            # 验证配置
            self._validate_config(config_data, config_name)

            # 缓存配置
            self.configs[config_name] = config_data

            # 添加文件监听
            if watch:
                self._watch_file(file_path)

            return config_data

    def get_config(
        self, config_name: str, key_path: Optional[str] = None, default=None
    ) -> Any:
        """
        获取配置值

        Args:
            config_name: 配置名称
            key_path: 配置键路径，如 "database.host"
            default: 默认值

        Returns:
            配置值
        """
        with self.lock:
            if config_name not in self.configs:
                return default

            config = self.configs[config_name]

            if key_path is None:
                return config

            # 按点分割路径获取嵌套值
            keys = key_path.split(".")
            value = config

            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default

    def set_config(self, config_name: str, key_path: str, value: Any):
        """
        设置配置值（内存中）

        Args:
            config_name: 配置名称
            key_path: 配置键路径
            value: 配置值
        """
        with self.lock:
            if config_name not in self.configs:
                self.configs[config_name] = {}

            config = self.configs[config_name]
            keys = key_path.split(".")

            # 创建嵌套字典结构
            current = config
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            current[keys[-1]] = value

            # 触发变更回调
            self._trigger_callbacks(config_name)

    def save_config(
        self, config_name: str, file_path: Optional[Union[str, Path]] = None
    ):
        """
        保存配置到文件

        Args:
            config_name: 配置名称
            file_path: 保存路径，如果为None则保存到原文件
        """
        with self.lock:
            if config_name not in self.configs:
                raise ValueError(f"配置不存在: {config_name}")

            if file_path is None:
                file_path = self._find_config_file(config_name)
            else:
                file_path = Path(file_path)

            config_data = self.configs[config_name]
            self._save_file(file_path, config_data)

    def reload_config(self, config_name: str):
        """手动重新加载配置"""
        if config_name in self.configs:
            file_path = self._find_config_file(config_name)
            self._reload_config(file_path)

    def start_watching(self):
        """启动配置文件监听"""
        if self.observer is None:
            self.observer = Observer()
            handler = ConfigChangeHandler(self)
            self.observer.schedule(handler, str(self.config_dir), recursive=True)
            self.observer.start()

    def stop_watching(self):
        """停止配置文件监听"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

    def _find_config_file(self, config_name: str) -> Path:
        """查找配置文件"""
        for ext in ["yaml", "yml", "json"]:
            file_path = self.config_dir / f"{config_name}.{ext}"
            if file_path.exists():
                return file_path
        raise FileNotFoundError(f"找不到配置文件: {config_name}")

    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """加载配置文件"""
        suffix = file_path.suffix.lower()

        with open(file_path, "r", encoding="utf-8") as f:
            if suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f) or {}
            elif suffix == ".json":
                return json.load(f) or {}
            else:
                raise ValueError(f"不支持的配置文件格式: {suffix}")

    def _save_file(self, file_path: Path, data: Dict[str, Any]):
        """保存配置文件"""
        suffix = file_path.suffix.lower()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            if suffix in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif suffix == ".json":
                json.dump(data, f, indent=2, ensure_ascii=False)

    def _apply_env_overrides(
        self, config: Dict[str, Any], config_name: str
    ) -> Dict[str, Any]:
        """应用环境变量覆盖"""
        prefix = f"{config_name.upper()}_"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix) :].lower()
                # 简单的类型转换
                if value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)

                # 设置到配置中
                keys = config_key.split("_")
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value

        return config

    def _validate_config(self, config: Dict[str, Any], config_name: str):
        """验证配置"""
        for rule in self.validation_rules:
            value = self.get_config(config_name, rule.key_path)

            if rule.required and value is None:
                raise ValueError(f"必需的配置项缺失: {rule.key_path}")

            if value is not None:
                if not isinstance(value, rule.data_type):
                    raise TypeError(
                        f"配置项类型错误: {rule.key_path}, 期望 {rule.data_type}, 得到 {type(value)}"
                    )

                if rule.validator_func and not rule.validator_func(value):
                    raise ValueError(f"配置项验证失败: {rule.key_path}")

    def _watch_file(self, file_path: Path):
        """添加文件监听"""
        self.watched_files[file_path] = file_path.stat().st_mtime

    def _reload_config(self, file_path: Path):
        """重新加载配置"""
        current_mtime = file_path.stat().st_mtime
        if (
            file_path in self.watched_files
            and self.watched_files[file_path] >= current_mtime
        ):
            return  # 文件未变更

        # 找到对应的配置名称
        config_name = file_path.stem

        try:
            with self.lock:
                # 重新加载配置
                config_data = self._load_file(file_path)
                config_data = self._apply_env_overrides(config_data, config_name)
                self._validate_config(config_data, config_name)

                self.configs[config_name] = config_data
                self.watched_files[file_path] = current_mtime

                # 触发变更回调
                self._trigger_callbacks(config_name)

        except Exception as e:
            print(f"配置文件重新加载失败: {file_path}, 错误: {e}")

    def _trigger_callbacks(self, config_name: str):
        """触发配置变更回调"""
        if config_name in self.callbacks:
            for callback in self.callbacks[config_name]:
                try:
                    callback(config_name, self.configs[config_name])
                except Exception as e:
                    print(f"配置变更回调执行失败: {e}")


# 全局配置管理器实例
config_manager = CoreConfigManager()
