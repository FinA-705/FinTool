"""
表达式验证器

验证表达式的安全性和合法性
"""

import ast
import re
from typing import List, Set
from .expression_types import ValidationError, SecurityError


class ExpressionValidator:
    """表达式验证器"""

    # 危险的关键字和模式
    DANGEROUS_KEYWORDS = {
        "__import__",
        "eval",
        "exec",
        "compile",
        "open",
        "file",
        "input",
        "raw_input",
        "reload",
        "globals",
        "locals",
        "vars",
        "dir",
        "hasattr",
        "getattr",
        "setattr",
        "delattr",
        "isinstance",
        "issubclass",
        "callable",
        "type",
        "id",
        "help",
        "quit",
        "exit",
        "__builtins__",
        "__globals__",
        "__locals__",
        "__dict__",
        "__class__",
        "__bases__",
        "__name__",
        "__module__",
        "__file__",
    }

    # 危险的模式
    DANGEROUS_PATTERNS = [
        r"__.*__",  # 双下划线属性
        r"import\s+",  # import语句
        r"from\s+.*\s+import",  # from...import语句
        r"\bexec\s*\(",  # exec调用
        r"\beval\s*\(",  # eval调用
        r"\bopen\s*\(",  # open调用
        r"\..*__.*__",  # 访问特殊属性
    ]

    def __init__(self):
        """初始化验证器"""
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS
        ]

    def validate(self, expression: str) -> bool:
        """验证表达式是否安全

        Args:
            expression: 表达式字符串

        Returns:
            是否安全
        """
        try:
            # 基本检查
            self._check_dangerous_keywords(expression)
            self._check_dangerous_patterns(expression)

            # AST检查
            self._check_ast_security(expression)

            return True

        except (SecurityError, ValidationError):
            return False

    def get_violations(self, expression: str) -> List[str]:
        """获取表达式违规项

        Args:
            expression: 表达式字符串

        Returns:
            违规项列表
        """
        violations = []

        try:
            self._check_dangerous_keywords(expression)
        except SecurityError as e:
            violations.append(str(e))

        try:
            self._check_dangerous_patterns(expression)
        except SecurityError as e:
            violations.append(str(e))

        try:
            self._check_ast_security(expression)
        except SecurityError as e:
            violations.append(str(e))

        return violations

    def _check_dangerous_keywords(self, expression: str):
        """检查危险关键字"""
        expression_lower = expression.lower()

        for keyword in self.DANGEROUS_KEYWORDS:
            if keyword.lower() in expression_lower:
                raise SecurityError(f"检测到危险关键字: {keyword}")

    def _check_dangerous_patterns(self, expression: str):
        """检查危险模式"""
        for pattern in self.compiled_patterns:
            if pattern.search(expression):
                raise SecurityError(f"检测到危险模式: {pattern.pattern}")

    def _check_ast_security(self, expression: str):
        """检查AST安全性"""
        try:
            tree = ast.parse(expression, mode="eval")
            self._check_ast_nodes(tree)
        except SyntaxError as e:
            raise ValidationError(f"语法错误: {e}")

    def _check_ast_nodes(self, node: ast.AST):
        """递归检查AST节点"""
        # 禁止的节点类型
        forbidden_nodes = {
            ast.Import,
            ast.ImportFrom,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
            ast.Lambda,
            ast.Global,
            ast.Nonlocal,
            ast.Delete,
            ast.Assign,
            ast.AugAssign,
            ast.AnnAssign,
            ast.With,
            ast.AsyncWith,
            ast.Raise,
            ast.Try,
            ast.Assert,
            ast.Yield,
            ast.YieldFrom,
            ast.Await,
        }

        for child in ast.walk(node):
            if type(child) in forbidden_nodes:
                raise SecurityError(f"禁止的AST节点类型: {type(child).__name__}")

            # 检查属性访问
            if isinstance(child, ast.Attribute):
                if child.attr.startswith("_"):
                    raise SecurityError(f"禁止访问私有属性: {child.attr}")

            # 检查函数调用
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                    if func_name in self.DANGEROUS_KEYWORDS:
                        raise SecurityError(f"禁止调用危险函数: {func_name}")

                elif isinstance(child.func, ast.Attribute):
                    attr_name = child.func.attr
                    if attr_name.startswith("_"):
                        raise SecurityError(f"禁止调用私有方法: {attr_name}")

    def check_formula_syntax(self, formula: str) -> bool:
        """检查公式语法是否正确

        Args:
            formula: 公式字符串

        Returns:
            语法是否正确
        """
        try:
            ast.parse(formula, mode="eval")
            return True
        except SyntaxError:
            return False

    def extract_variables(self, expression: str) -> Set[str]:
        """提取表达式中的变量名

        Args:
            expression: 表达式字符串

        Returns:
            变量名集合
        """
        variables = set()

        try:
            tree = ast.parse(expression, mode="eval")

            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    variables.add(node.id)

        except SyntaxError:
            pass  # 语法错误时返回空集合

        return variables

    def extract_functions(self, expression: str) -> Set[str]:
        """提取表达式中的函数名

        Args:
            expression: 表达式字符串

        Returns:
            函数名集合
        """
        functions = set()

        try:
            tree = ast.parse(expression, mode="eval")

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        functions.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        functions.add(node.func.attr)

        except SyntaxError:
            pass  # 语法错误时返回空集合

        return functions
