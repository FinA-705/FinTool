"""
任务持久化存储
"""
import json
from pathlib import Path
from typing import Dict, Any
import logging
from .models import TaskInfo, TaskPriority
from datetime import datetime


class TaskStorage:
    """任务持久化存储"""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.logger = logging.getLogger(__name__)

    def save(self, tasks: Dict[str, TaskInfo]):
        """保存任务到文件"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            serializable_tasks = {}
            for task_id, task in tasks.items():
                if task.schedule:
                    serializable_tasks[task_id] = {
                        "task_id": task.task_id,
                        "name": task.name,
                        "schedule": task.schedule,
                        "priority": task.priority.value,
                        "max_retries": task.max_retries,
                        "retry_delay": task.retry_delay,
                        "timeout": task.timeout,
                        "enabled": task.enabled,
                        "metadata": task.metadata,
                        "created_at": task.created_at.isoformat(),
                        "next_run": (
                            task.next_run.isoformat() if task.next_run else None
                        ),
                        "last_run": (
                            task.last_run.isoformat() if task.last_run else None
                        ),
                    }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(serializable_tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")

    def load(self) -> Dict[str, Dict[str, Any]]:
        """从文件加载任务元数据"""
        if not self.storage_path.exists():
            return {}
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                serializable_tasks = json.load(f)
            self.logger.info(f"从文件加载了 {len(serializable_tasks)} 个任务元数据")
            return serializable_tasks
        except Exception as e:
            self.logger.error(f"加载任务失败: {e}")
            return {}
