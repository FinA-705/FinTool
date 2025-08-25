"""
核心调度器实现
"""
import asyncio
import time
import threading
import uuid
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime

from .models import TaskInfo, TaskResult, TaskStatus, TaskPriority
from .cron_parser import CronParser
from .task_queue import TaskQueue
from .storage import TaskStorage


class CoreScheduler:
    """核心定时任务调度器"""

    def __init__(
        self, max_workers: int = 4, storage_path: Optional[Union[str, Path]] = None
    ):
        self.max_workers = max_workers
        self.storage = (
            TaskStorage(Path(storage_path)) if storage_path else None
        )
        self.tasks: Dict[str, TaskInfo] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_queue = TaskQueue()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, Future] = {}
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        self.check_interval = 1.0
        self.max_task_history = 1000
        self.logger = logging.getLogger(__name__)
        if self.storage:
            self._load_tasks()

    def add_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        schedule: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = TaskInfo(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs or {},
            schedule=schedule,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata or {},
        )
        if schedule:
            task.next_run = CronParser.parse_cron(schedule)
        with self.lock:
            self.tasks[task_id] = task
        if not schedule and self.running:
            self.task_queue.put(task)
        if self.storage:
            self.storage.save(self.tasks)
        self.logger.info(f"添加任务: {name} (ID: {task_id})")
        return task_id

    def remove_task(self, task_id: str) -> bool:
        with self.lock:
            if task_id in self.tasks:
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]
                del self.tasks[task_id]
                if self.storage:
                    self.storage.save(self.tasks)
                self.logger.info(f"移除任务: {task_id}")
                return True
        return False

    def enable_task(self, task_id: str, enabled: bool = True) -> bool:
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].enabled = enabled
                if self.storage:
                    self.storage.save(self.tasks)
                return True
        return False

    def run_task_now(self, task_id: str) -> Optional[str]:
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if not task.enabled:
                    return None
                execution_id = f"{task_id}_{int(time.time())}"
                self.task_queue.put(task)
                return execution_id
        return None

    def start(self):
        if self.running:
            return
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()
        self.logger.info("任务调度器已启动")

    def stop(self):
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        for future in self.running_tasks.values():
            future.cancel()
        self.running_tasks.clear()
        self.executor.shutdown(wait=True)
        self.logger.info("任务调度器已停止")

    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        return self.task_results.get(task_id)

    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        with self.lock:
            return self.tasks.copy()

    def get_task_history(self, limit: int = 100) -> List[TaskResult]:
        results = list(self.task_results.values())
        results.sort(key=lambda x: x.start_time or datetime.min, reverse=True)
        return results[:limit]

    def _scheduler_loop(self):
        while self.running:
            try:
                self._check_scheduled_tasks()
                self._execute_queued_tasks()
                self._cleanup_completed_tasks()
                self._cleanup_history()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"调度器循环出错: {e}")
                time.sleep(1.0)

    def _check_scheduled_tasks(self):
        current_time = datetime.now()
        with self.lock:
            for task in self.tasks.values():
                if (
                    task.enabled
                    and task.schedule
                    and task.next_run
                    and current_time >= task.next_run
                ):
                    self.task_queue.put(task)
                    task.next_run = CronParser.parse_cron(task.schedule, current_time)
                    task.last_run = current_time

    def _execute_queued_tasks(self):
        available_workers = self.max_workers - len(self.running_tasks)
        for _ in range(available_workers):
            task = self.task_queue.get()
            if task is None:
                break
            if not task.enabled:
                continue
            future = self.executor.submit(self._execute_task, task)
            self.running_tasks[task.task_id] = future

    def _execute_task(self, task: TaskInfo) -> TaskResult:
        result = TaskResult(
            task_id=task.task_id, status=TaskStatus.RUNNING, start_time=datetime.now()
        )
        try:
            self.logger.info(f"开始执行任务: {task.name} (ID: {task.task_id})")
            if asyncio.iscoroutinefunction(task.func):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if task.timeout:
                        task_result = loop.run_until_complete(
                            asyncio.wait_for(
                                task.func(*task.args, **task.kwargs),
                                timeout=task.timeout,
                            )
                        )
                    else:
                        task_result = loop.run_until_complete(
                            task.func(*task.args, **task.kwargs)
                        )
                finally:
                    loop.close()
            else:
                task_result = task.func(*task.args, **task.kwargs)
            result.result = task_result
            result.status = TaskStatus.COMPLETED
            self.logger.info(f"任务执行成功: {task.name} (ID: {task.task_id})")
        except Exception as e:
            result.error = str(e)
            result.status = TaskStatus.FAILED
            self.logger.error(
                f"任务执行失败: {task.name} (ID: {task.task_id}), 错误: {e}"
            )
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                self.logger.info(f"任务重试: {task.name}, 第{task.retry_count}次重试")
                time.sleep(task.retry_delay)
                self.task_queue.put(task)
        finally:
            result.end_time = datetime.now()
            if result.start_time and result.end_time:
                result.duration = (result.end_time - result.start_time).total_seconds()
            self.task_results[task.task_id] = result
        return result

    def _cleanup_completed_tasks(self):
        completed_tasks = [
            task_id
            for task_id, future in self.running_tasks.items()
            if future.done()
        ]
        for task_id in completed_tasks:
            del self.running_tasks[task_id]

    def _cleanup_history(self):
        if len(self.task_results) > self.max_task_history:
            sorted_results = sorted(
                self.task_results.items(),
                key=lambda x: x[1].start_time or datetime.min,
                reverse=True,
            )
            self.task_results = dict(sorted_results[: self.max_task_history])

    def _load_tasks(self):
        if self.storage:
            self.logger.info("从文件加载任务元数据")
            # This part would need a mechanism to re-associate functions with tasks
            # For now, it just logs the loaded data.
            self.storage.load()
