"""
任务相关的枚举和数据类
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional
from datetime import datetime


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None

    @property
    def is_success(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def is_failure(self) -> bool:
        return self.status == TaskStatus.FAILED


@dataclass
class TaskInfo:
    """任务信息"""

    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    schedule: Optional[str] = None  # cron表达式或间隔时间
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    retry_count: int = 0
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
