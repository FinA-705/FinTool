"""
安全表达式求值器

提供安全的数学表达式和逻辑表达式求值
只允许安全的操作，防止代码注入
"""

import ast
import operator
import math
from typing import Any, Dict, Optional, Callable
import pandas as pd
import numpy as np

from .expression_types import ExpressionError, SecurityError


class SafeEvaluator:
    """安全的表达式求值器

    只允许安全的操作，防止代码注入
    """

    # 允许的操作符
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
    }

    # 允许的内置函数
    SAFE_FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "round": round,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "sorted": sorted,
        "reversed": reversed,
    }

    # 数学函数
    MATH_FUNCTIONS = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "sqrt": math.sqrt,
        "pow": pow,
        "ceil": math.ceil,
        "floor": math.floor,
        "fabs": math.fabs,
        "factorial": math.factorial,
        "degrees": math.degrees,
        "radians": math.radians,
    }

    # 允许的常量
    SAFE_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
        "inf": math.inf,
        "nan": math.nan,
        "True": True,
        "False": False,
        "None": None,
    }

    def __init__(
        self,
        custom_functions: Optional[Dict[str, Callable]] = None,
        custom_constants: Optional[Dict[str, Any]] = None,
        allow_assign: bool = False,
    ):
        """初始化求值器

        Args:
            custom_functions: 自定义函数
            custom_constants: 自定义常量
            allow_assign: 是否允许赋值操作
        """
        self.custom_functions = custom_functions or {}
        self.custom_constants = custom_constants or {}
        self.allow_assign = allow_assign

        # 合并所有可用的函数和常量
        self.functions = {
            **self.SAFE_FUNCTIONS,
            **self.MATH_FUNCTIONS,
            **self.custom_functions,
        }

        self.constants = {**self.SAFE_CONSTANTS, **self.custom_constants}

    def evaluate(
        self, expression: str, variables: Optional[Dict[str, Any]] = None
    ) -> Any:
        """求值表达式

        Args:
            expression: 表达式字符串
            variables: 变量字典

        Returns:
            求值结果
        """
        if not isinstance(expression, str):
            raise ExpressionError("表达式必须是字符串")

        variables = variables or {}

        try:
            # 解析表达式
            node = ast.parse(expression.strip(), mode="eval")

            # 安全检查
            self._check_security(node)

            # 求值
            return self._eval_node(node.body, variables)

        except SyntaxError as e:
            raise ExpressionError(f"语法错误: {e}")
        except Exception as e:
            raise ExpressionError(f"求值错误: {e}")

    def _check_security(self, node: ast.AST):
        """安全检查"""
        for child in ast.walk(node):
            # 检查是否包含不安全的操作
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                raise SecurityError("不允许导入模块")

            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    # 检查方法调用
                    if hasattr(child.func, "attr"):
                        attr_name = child.func.attr
                        if attr_name.startswith("_"):
                            raise SecurityError(f"不允许调用私有方法: {attr_name}")

            if isinstance(child, ast.Attribute):
                if child.attr.startswith("_"):
                    raise SecurityError(f"不允许访问私有属性: {child.attr}")

            if not self.allow_assign and isinstance(child, ast.Assign):
                raise SecurityError("不允许赋值操作")

    def _eval_node(self, node: ast.AST, variables: Dict[str, Any]) -> Any:
        """求值AST节点"""
        if isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Num):  # Python < 3.8兼容
            return node.n

        elif isinstance(node, ast.Str):  # Python < 3.8兼容
            return node.s

        elif isinstance(node, ast.Name):
            name = node.id

            # 查找变量值
            if name in variables:
                return variables[name]
            elif name in self.constants:
                return self.constants[name]
            elif name in self.functions:
                return self.functions[name]
            else:
                raise ExpressionError(f"未定义的变量或函数: {name}")

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, variables)
            right = self._eval_node(node.right, variables)

            if type(node.op) not in self.SAFE_OPERATORS:
                raise SecurityError(f"不允许的操作符: {type(node.op).__name__}")

            op_func = self.SAFE_OPERATORS[type(node.op)]

            # 处理数组操作
            try:
                return op_func(left, right)
            except ZeroDivisionError:
                if isinstance(left, (np.ndarray, pd.Series)) or isinstance(
                    right, (np.ndarray, pd.Series)
                ):
                    # 处理数组除零
                    return np.divide(
                        left, right, out=np.full_like(left, np.inf), where=right != 0
                    )
                else:
                    raise

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, variables)

            if type(node.op) not in self.SAFE_OPERATORS:
                raise SecurityError(f"不允许的一元操作符: {type(node.op).__name__}")

            op_func = self.SAFE_OPERATORS[type(node.op)]
            return op_func(operand)

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, variables)
            result = left
            final_result = None

            for i, (op, comparator) in enumerate(zip(node.ops, node.comparators)):
                right = self._eval_node(comparator, variables)

                if type(op) not in self.SAFE_OPERATORS:
                    raise SecurityError(f"不允许的比较操作符: {type(op).__name__}")

                op_func = self.SAFE_OPERATORS[type(op)]
                comparison_result = op_func(result, right)

                if i == 0:
                    final_result = comparison_result
                else:
                    # 链式比较：a < b < c => (a < b) and (b < c)
                    if final_result is not None:
                        if isinstance(
                            final_result, (np.ndarray, pd.Series)
                        ) or isinstance(comparison_result, (np.ndarray, pd.Series)):
                            final_result = final_result & comparison_result
                        else:
                            final_result = final_result and comparison_result

                result = right

            return final_result if final_result is not None else True

        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                results = []
                for value in node.values:
                    result = self._eval_node(value, variables)
                    results.append(result)

                # 处理数组和标量混合的情况
                array_results = [
                    r for r in results if isinstance(r, (np.ndarray, pd.Series))
                ]
                scalar_results = [
                    r for r in results if not isinstance(r, (np.ndarray, pd.Series))
                ]

                if array_results:
                    # 有数组结果，进行逐元素and操作
                    final_result = array_results[0].astype(bool)
                    for arr in array_results[1:]:
                        final_result = final_result & arr.astype(bool)

                    # 应用标量条件
                    for scalar in scalar_results:
                        if not scalar:
                            final_result = np.zeros_like(final_result, dtype=bool)
                            break

                    return final_result
                else:
                    # 全是标量，常规处理
                    return all(results)

            elif isinstance(node.op, ast.Or):
                results = []
                for value in node.values:
                    result = self._eval_node(value, variables)
                    results.append(result)

                # 处理数组和标量混合的情况
                array_results = [
                    r for r in results if isinstance(r, (np.ndarray, pd.Series))
                ]
                scalar_results = [
                    r for r in results if not isinstance(r, (np.ndarray, pd.Series))
                ]

                if array_results:
                    # 有数组结果，进行逐元素or操作
                    final_result = array_results[0].astype(bool)
                    for arr in array_results[1:]:
                        final_result = final_result | arr.astype(bool)

                    # 应用标量条件
                    for scalar in scalar_results:
                        if scalar:
                            final_result = np.ones_like(final_result, dtype=bool)
                            break

                    return final_result
                else:
                    # 全是标量，常规处理
                    return any(results)

        elif isinstance(node, ast.Call):
            func = self._eval_node(node.func, variables)

            if not callable(func):
                raise ExpressionError(f"'{func}' 不是可调用对象")

            args = [self._eval_node(arg, variables) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, variables)
                for kw in node.keywords
                if kw.arg
            }

            return func(*args, **kwargs)

        elif isinstance(node, ast.List):
            return [self._eval_node(item, variables) for item in node.elts]

        elif isinstance(node, ast.Tuple):
            return tuple(self._eval_node(item, variables) for item in node.elts)

        else:
            raise ExpressionError(f"不支持的AST节点类型: {type(node).__name__}")
