"""
统一日志工具

基于loguru实现统一的日志接口
支持多种输出格式和日志级别
"""

from typing import Optional, Union, Dict, Any
import sys
from pathlib import Path
from datetime import datetime
from loguru import logger as loguru_logger
import functools


class LogLevel:
    """日志级别常量"""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Logger:
    """统一日志器

    基于loguru的日志管理器，提供统一的日志接口
    支持文件输出、控制台输出、结构化日志等功能
    """

    def __init__(self, name: str = "FinancialAgent"):
        """初始化日志器

        Args:
            name: 日志器名称
        """
        self.name = name
        self._logger = loguru_logger.bind(module=name)
        self._configured = False

    def configure(
        self,
        log_level: str = LogLevel.INFO,
        log_file: Optional[Union[str, Path]] = None,
        rotation: str = "1 day",
        retention: str = "30 days",
        format_type: str = "detailed",
        enable_console: bool = True,
        enable_json: bool = False,
    ) -> "Logger":
        """配置日志器

        Args:
            log_level: 日志级别
            log_file: 日志文件路径
            rotation: 日志轮转规则
            retention: 日志保留时间
            format_type: 格式类型(simple/detailed/custom)
            enable_console: 是否启用控制台输出
            enable_json: 是否启用JSON格式

        Returns:
            配置后的日志器实例
        """
        if self._configured:
            return self

        # 移除默认handler
        self._logger.remove()

        # 获取日志格式
        log_format = self._get_format(format_type, enable_json)

        # 配置控制台输出
        if enable_console:
            self._logger.add(
                sys.stdout,
                level=log_level,
                format=log_format,
                colorize=True,
                backtrace=True,
                diagnose=True,
            )

        # 配置文件输出
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            self._logger.add(
                str(log_path),
                level=log_level,
                format=log_format,
                rotation=rotation,
                retention=retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
                encoding="utf-8",
            )

        self._configured = True
        return self

    def _get_format(self, format_type: str, enable_json: bool) -> str:
        """获取日志格式"""
        if enable_json:
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {module} | {message} | {extra}"

        if format_type == "simple":
            return "{time:HH:mm:ss} | {level} | {message}"
        elif format_type == "detailed":
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module: <15} | {function}:{line} | {message}"
        elif format_type == "custom":
            return "{time:YYYY-MM-DD HH:mm:ss} | {level} | [{module}] {function}() | {message}"
        else:
            return "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"

    def trace(self, message: str, **kwargs):
        """记录TRACE级别日志"""
        self._logger.trace(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self._logger.info(message, **kwargs)

    def success(self, message: str, **kwargs):
        """记录SUCCESS级别日志"""
        self._logger.success(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self._logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """记录异常信息"""
        self._logger.exception(message, **kwargs)

    def bind(self, **kwargs) -> "Logger":
        """绑定上下文信息"""
        bound_logger = Logger(self.name)
        bound_logger._logger = self._logger.bind(**kwargs)
        bound_logger._configured = self._configured
        return bound_logger

    def with_context(self, **context) -> "Logger":
        """添加上下文信息"""
        return self.bind(**context)

    def log_function_call(
        self, func_name: str, args: tuple = (), kwargs: Optional[Dict[str, Any]] = None
    ):
        """记录函数调用"""
        kwargs_str = f", kwargs={kwargs}" if kwargs else ""
        self.debug(f"调用函数 {func_name}(args={args}{kwargs_str})")

    def log_performance(self, operation: str, duration: float, **metrics):
        """记录性能指标"""
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
        self.info(f"性能指标 | {operation} | 耗时: {duration:.3f}s | {metrics_str}")

    def log_data_operation(self, operation: str, data_type: str, count: int, **details):
        """记录数据操作"""
        details_str = ", ".join(f"{k}={v}" for k, v in details.items())
        self.info(f"数据操作 | {operation} | {data_type}: {count}条 | {details_str}")

    def log_api_call(self, method: str, url: str, status_code: int, duration: float):
        """记录API调用"""
        self.info(
            f"API调用 | {method} {url} | 状态码: {status_code} | 耗时: {duration:.3f}s"
        )

    def log_error_with_context(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ):
        """记录带上下文的错误"""
        context_str = f" | 上下文: {context}" if context else ""
        self.error(f"异常发生: {type(error).__name__}: {str(error)}{context_str}")


# 全局日志器实例
_global_logger: Optional[Logger] = None


def get_logger(name: str = "FinancialAgent") -> Logger:
    """获取日志器实例

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    global _global_logger

    if _global_logger is None or _global_logger.name != name:
        _global_logger = Logger(name)

        # 默认配置
        if not _global_logger._configured:
            _global_logger.configure(
                log_level=LogLevel.INFO,
                log_file="logs/financial_agent.log",
                enable_console=True,
                format_type="detailed",
            )

    return _global_logger


def configure_global_logger(**config) -> Logger:
    """配置全局日志器

    Args:
        **config: 日志配置参数

    Returns:
        配置后的日志器
    """
    logger = get_logger()
    return logger.configure(**config)


def log_function_calls(logger_name: str = "FinancialAgent"):
    """函数调用日志装饰器

    Args:
        logger_name: 日志器名称
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            func_name = f"{func.__module__}.{func.__name__}"

            # 记录函数开始
            logger.debug(f"开始执行 {func_name}")

            try:
                result = func(*args, **kwargs)
                logger.debug(f"完成执行 {func_name}")
                return result
            except Exception as e:
                logger.error(f"执行失败 {func_name}: {str(e)}")
                raise

        return wrapper

    return decorator


def log_performance(logger_name: str = "FinancialAgent"):
    """性能监控装饰器

    Args:
        logger_name: 日志器名称
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            func_name = f"{func.__module__}.{func.__name__}"

            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(func_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"函数执行异常 {func_name} | 耗时: {duration:.3f}s | 错误: {str(e)}"
                )
                raise

        return wrapper

    return decorator


# 便捷函数
def trace(message: str, **kwargs):
    """记录TRACE日志"""
    get_logger().trace(message, **kwargs)


def debug(message: str, **kwargs):
    """记录DEBUG日志"""
    get_logger().debug(message, **kwargs)


def info(message: str, **kwargs):
    """记录INFO日志"""
    get_logger().info(message, **kwargs)


def success(message: str, **kwargs):
    """记录SUCCESS日志"""
    get_logger().success(message, **kwargs)


def warning(message: str, **kwargs):
    """记录WARNING日志"""
    get_logger().warning(message, **kwargs)


def error(message: str, **kwargs):
    """记录ERROR日志"""
    get_logger().error(message, **kwargs)


def critical(message: str, **kwargs):
    """记录CRITICAL日志"""
    get_logger().critical(message, **kwargs)


def exception(message: str, **kwargs):
    """记录异常日志"""
    get_logger().exception(message, **kwargs)


# 使用示例
if __name__ == "__main__":
    # 配置日志器
    logger = get_logger("TestModule")
    logger.configure(
        log_level=LogLevel.DEBUG, log_file="logs/test.log", format_type="detailed"
    )

    # 测试各种日志级别
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.success("操作成功")
    logger.warning("这是警告")
    logger.error("这是错误")

    # 测试上下文绑定
    context_logger = logger.bind(user_id="12345", session="abc")
    context_logger.info("用户操作")

    # 测试性能日志
    logger.log_performance("数据处理", 1.234, records=1000, cpu_usage=0.8)

    # 测试装饰器
    @log_function_calls()
    @log_performance()
    def test_function():
        import time

        time.sleep(0.1)
        return "测试结果"

    result = test_function()
    print(f"函数返回: {result}")
