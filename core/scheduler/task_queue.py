"""
任务队列实现
"""
import threading
from typing import List, Optional
from .models import TaskInfo


class TaskQueue:
    """任务队列"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: List[TaskInfo] = []
        self._lock = threading.RLock()

    def put(self, task: TaskInfo) -> bool:
        """添加任务到队列"""
        with self._lock:
            if len(self._queue) >= self.max_size:
                return False
            inserted = False
            for i, existing_task in enumerate(self._queue):
                if task.priority.value > existing_task.priority.value:
                    self._queue.insert(i, task)
                    inserted = True
                    break
            if not inserted:
                self._queue.append(task)
            return True

    def get(self) -> Optional[TaskInfo]:
        """从队列获取任务"""
        with self._lock:
            if not self._queue:
                return None
            return self._queue.pop(0)

    def size(self) -> int:
        """队列大小"""
        with self._lock:
            return len(self._queue)

    def clear(self):
        """清空队列"""
        with self._lock:
            self._queue.clear()
