"""
表达式求值器基础类型和异常

定义表达式求值器使用的异常类和基础类型
"""


class ExpressionError(Exception):
    """表达式求值错误"""

    pass


class SecurityError(ExpressionError):
    """安全性错误"""

    pass


class ValidationError(ExpressionError):
    """验证错误"""

    pass


class SyntaxError(ExpressionError):
    """语法错误"""

    pass
