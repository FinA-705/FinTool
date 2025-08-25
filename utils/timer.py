"""
性能计时工具

提供高精度计时和性能监控功能
支持上下文管理器和装饰器两种使用方式
"""

import time
import functools
from typing import Optional, Dict, Any, Callable, Union, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
from collections import defaultdict, deque
import threading


@dataclass
class TimingResult:
    """计时结果"""

    name: str
    duration: float
    start_time: float
    end_time: float
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata or {},
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}: {self.duration:.4f}s"


class Timer:
    """高精度计时器

    支持多种使用方式：
    1. 上下文管理器
    2. 手动开始/停止
    3. 装饰器
    4. 性能统计
    """

    def __init__(self, name: str = "Timer", auto_start: bool = False):
        """初始化计时器

        Args:
            name: 计时器名称
            auto_start: 是否自动开始计时
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.metadata: Dict[str, Any] = {}

        if auto_start:
            self.start()

    def start(self) -> "Timer":
        """开始计时"""
        self.start_time = time.perf_counter()
        self.end_time = None
        self.duration = None
        return self

    def stop(self) -> float:
        """停止计时

        Returns:
            计时时长(秒)
        """
        if self.start_time is None:
            raise RuntimeError("计时器尚未开始")

        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        return self.duration

    def elapsed(self) -> float:
        """获取已过去的时间

        Returns:
            已过去的时间(秒)
        """
        if self.start_time is None:
            return 0.0

        current_time = time.perf_counter()
        return current_time - self.start_time

    def reset(self) -> "Timer":
        """重置计时器"""
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.metadata.clear()
        return self

    def add_metadata(self, **metadata) -> "Timer":
        """添加元数据"""
        self.metadata.update(metadata)
        return self

    def get_result(self) -> TimingResult:
        """获取计时结果"""
        if self.duration is None:
            if self.start_time is not None:
                # 自动停止计时
                self.stop()
            else:
                raise RuntimeError("计时器尚未开始或完成")

        return TimingResult(
            name=self.name,
            duration=self.duration or 0.0,
            start_time=self.start_time or 0.0,
            end_time=self.end_time or 0.0,
            metadata=self.metadata.copy(),
        )

    def __enter__(self) -> "Timer":
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()

    def __str__(self) -> str:
        """字符串表示"""
        if self.duration is not None:
            return f"{self.name}: {self.duration:.4f}s"
        elif self.start_time is not None:
            return f"{self.name}: {self.elapsed():.4f}s (运行中)"
        else:
            return f"{self.name}: 未开始"


class PerformanceMonitor:
    """性能监控器

    收集和统计多次计时结果
    提供性能分析和报告功能
    """

    def __init__(self, max_history: int = 1000):
        """初始化性能监控器

        Args:
            max_history: 最大历史记录数量
        """
        self.max_history = max_history
        self._timings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._lock = threading.Lock()

    def add_timing(self, result: TimingResult):
        """添加计时结果"""
        with self._lock:
            self._timings[result.name].append(result)

    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """获取统计信息

        Args:
            name: 计时器名称

        Returns:
            统计信息字典
        """
        with self._lock:
            if name not in self._timings or not self._timings[name]:
                return None

            durations = [result.duration for result in self._timings[name]]

            return {
                "count": len(durations),
                "total": sum(durations),
                "average": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "latest": durations[-1],
            }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有统计信息"""
        with self._lock:
            result = {}
            for name in self._timings.keys():
                stats = self.get_stats(name)
                if stats is not None:
                    result[name] = stats
            return result

    def clear_history(self, name: Optional[str] = None):
        """清空历史记录

        Args:
            name: 计时器名称，如果为None则清空所有
        """
        with self._lock:
            if name is None:
                self._timings.clear()
            elif name in self._timings:
                self._timings[name].clear()

    def get_report(self) -> str:
        """生成性能报告"""
        all_stats = self.get_all_stats()

        if not all_stats:
            return "暂无性能数据"

        lines = ["性能统计报告", "=" * 50]

        for name, stats in all_stats.items():
            if stats:
                lines.extend(
                    [
                        f"\n{name}:",
                        f"  调用次数: {stats['count']}",
                        f"  总时间: {stats['total']:.4f}s",
                        f"  平均时间: {stats['average']:.4f}s",
                        f"  最短时间: {stats['min']:.4f}s",
                        f"  最长时间: {stats['max']:.4f}s",
                        f"  最近时间: {stats['latest']:.4f}s",
                    ]
                )

        return "\n".join(lines)


# 全局性能监控器
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor


@contextmanager
def timeit(name: str = "Operation", monitor: bool = True, **metadata):
    """计时上下文管理器

    Args:
        name: 操作名称
        monitor: 是否添加到性能监控器
        **metadata: 额外的元数据

    Yields:
        Timer实例
    """
    timer = Timer(name)
    timer.add_metadata(**metadata)

    try:
        timer.start()
        yield timer
    finally:
        timer.stop()

        if monitor:
            _global_monitor.add_timing(timer.get_result())


def time_function(name: Optional[str] = None, monitor: bool = True):
    """函数计时装饰器

    Args:
        name: 自定义名称，如果为None则使用函数名
        monitor: 是否添加到性能监控器
    """

    def decorator(func: Callable) -> Callable:
        func_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with timeit(func_name, monitor=monitor):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def benchmark(
    func: Callable, *args, iterations: int = 1, warmup: int = 0, **kwargs
) -> Dict[str, Any]:
    """函数基准测试

    Args:
        func: 要测试的函数
        *args: 函数位置参数
        iterations: 迭代次数
        warmup: 预热次数
        **kwargs: 函数关键字参数

    Returns:
        基准测试结果
    """
    # 预热
    for _ in range(warmup):
        func(*args, **kwargs)

    # 基准测试
    durations = []
    last_result = None

    for i in range(iterations):
        with Timer(f"benchmark_{i}") as timer:
            last_result = func(*args, **kwargs)
        durations.append(timer.duration)

    # 统计结果
    total_time = sum(durations)
    avg_time = total_time / iterations
    min_time = min(durations)
    max_time = max(durations)

    return {
        "function": f"{func.__module__}.{func.__name__}",
        "iterations": iterations,
        "total_time": total_time,
        "average_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "durations": durations,
        "result": last_result if iterations == 1 else None,
    }


def compare_functions(
    *funcs, args: tuple = (), kwargs: Optional[Dict] = None, iterations: int = 100
) -> Dict[str, Any]:
    """比较多个函数的性能

    Args:
        *funcs: 要比较的函数列表
        args: 函数参数
        kwargs: 函数关键字参数
        iterations: 每个函数的迭代次数

    Returns:
        性能比较结果
    """
    kwargs = kwargs or {}
    results = {}

    for func in funcs:
        func_name = f"{func.__module__}.{func.__name__}"
        bench_result = benchmark(func, *args, iterations=iterations, **kwargs)
        results[func_name] = bench_result

    # 排序结果
    sorted_results = sorted(results.items(), key=lambda x: x[1]["average_time"])

    return {
        "comparison": sorted_results,
        "fastest": sorted_results[0][0] if sorted_results else None,
        "slowest": sorted_results[-1][0] if sorted_results else None,
        "details": results,
    }


# 便捷函数
def measure_time(func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """测量函数执行时间

    Args:
        func: 要测量的函数
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        (函数返回值, 执行时间)
    """
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()

    return result, end_time - start_time


def sleep_with_timer(seconds: float) -> TimingResult:
    """带计时的睡眠函数

    Args:
        seconds: 睡眠秒数

    Returns:
        计时结果
    """
    with Timer("sleep") as timer:
        time.sleep(seconds)

    return timer.get_result()


# 使用示例
if __name__ == "__main__":
    # 基本使用
    print("=== 基本计时器使用 ===")
    timer = Timer("测试操作")
    timer.start()
    time.sleep(0.1)
    duration = timer.stop()
    print(f"操作耗时: {duration:.4f}s")

    # 上下文管理器
    print("\n=== 上下文管理器 ===")
    with Timer("上下文操作") as t:
        time.sleep(0.05)
    print(t)

    # 装饰器
    print("\n=== 装饰器使用 ===")

    @time_function("数据处理")
    def process_data():
        time.sleep(0.02)
        return "处理完成"

    result = process_data()
    print(f"结果: {result}")

    # 性能监控
    print("\n=== 性能监控 ===")
    monitor = get_monitor()

    for i in range(5):
        with timeit(f"循环操作_{i}"):
            time.sleep(0.01)

    print(monitor.get_report())

    # 基准测试
    print("\n=== 基准测试 ===")

    def test_function():
        return sum(range(1000))

    bench_result = benchmark(test_function, iterations=10)
    print(f"平均耗时: {bench_result['average_time']:.6f}s")

    print("\n测试完成！")
