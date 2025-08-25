"""
策略公式解析器

支持用户自定义策略表达式的解析、验证和执行
集成安全的表达式求值器，防止代码注入
"""

import re
import ast
from typing import Any, Dict, List, Optional, Union, Set, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from utils.expression_evaluator import (
    SafeEvaluator,
    FormulaEvaluator,
    ExpressionValidator,
    ExpressionError,
    SecurityError,
)
from utils.logger import get_logger
from utils.validators import DataValidator, ValidationError

from .formula_types import FormulaType, OperatorType, FormulaComponent, ParsedFormula
from .formula_constants import FINANCIAL_FIELDS, FORMULA_FUNCTIONS, SCHLOSS_CONSTANTS
from .formula_functions import get_custom_functions

logger = get_logger(__name__)


class StrategyFormulaParser:
    """策略公式解析器"""

    def __init__(self):
        """初始化解析器"""
        self.evaluator = FormulaEvaluator()
        self.validator = ExpressionValidator()
        self.data_validator = DataValidator()

        # 设置字段和函数
        self.FINANCIAL_FIELDS = FINANCIAL_FIELDS
        self.FORMULA_FUNCTIONS = FORMULA_FUNCTIONS
        self.SCHLOSS_CONSTANTS = SCHLOSS_CONSTANTS

        # 扩展自定义函数
        self._setup_custom_functions()

    def _setup_custom_functions(self):
        """设置自定义函数"""
        custom_functions = get_custom_functions()

        # 更新求值器的自定义函数
        self.evaluator.evaluator.custom_functions.update(custom_functions)
        self.evaluator.evaluator.functions.update(custom_functions)

    def parse_formula(self, formula: str, formula_type: FormulaType) -> ParsedFormula:
        """解析策略公式

        Args:
            formula: 公式字符串
            formula_type: 公式类型

        Returns:
            解析结果
        """
        logger.info(f"解析公式: {formula} (类型: {formula_type.value})")

        try:
            # 预处理公式
            processed_formula = self._preprocess_formula(formula)

            # 安全性检查
            if not self.validator.validate(processed_formula):
                violations = self.validator.get_violations(processed_formula)
                return ParsedFormula(
                    original=formula,
                    components=[],
                    variables=set(),
                    functions=set(),
                    operators=set(),
                    formula_type=formula_type,
                    is_valid=False,
                    error_message=f"安全性检查失败: {violations}",
                )

            # 解析AST
            ast_tree = ast.parse(processed_formula, mode="eval")

            # 提取组件
            components = self._extract_components(ast_tree)
            variables = self._extract_variables(ast_tree)
            functions = self._extract_functions(ast_tree)
            operators = self._extract_operators(ast_tree)

            # 验证字段和函数
            validation_error = self._validate_formula_elements(variables, functions)
            if validation_error:
                return ParsedFormula(
                    original=formula,
                    components=components,
                    variables=variables,
                    functions=functions,
                    operators=operators,
                    formula_type=formula_type,
                    is_valid=False,
                    error_message=validation_error,
                )

            # 测试执行
            test_error = self._test_formula_execution(processed_formula)
            if test_error:
                return ParsedFormula(
                    original=formula,
                    components=components,
                    variables=variables,
                    functions=functions,
                    operators=operators,
                    formula_type=formula_type,
                    is_valid=False,
                    error_message=f"执行测试失败: {test_error}",
                )

            return ParsedFormula(
                original=formula,
                components=components,
                variables=variables,
                functions=functions,
                operators=operators,
                formula_type=formula_type,
                is_valid=True,
            )

        except Exception as e:
            logger.error(f"解析公式失败: {e}")
            return ParsedFormula(
                original=formula,
                components=[],
                variables=set(),
                functions=set(),
                operators=set(),
                formula_type=formula_type,
                is_valid=False,
                error_message=str(e),
            )

    def execute_formula(
        self,
        formula: str,
        data: pd.DataFrame,
        constants: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """执行公式

        Args:
            formula: 公式字符串
            data: 数据DataFrame
            constants: 自定义常量

        Returns:
            执行结果
        """
        try:
            # 预处理公式
            processed_formula = self._preprocess_formula(formula)

            # 准备变量
            variables = self._prepare_variables(data, constants)

            # 执行公式
            result = self.evaluator.evaluate(processed_formula, variables)

            logger.info(f"公式执行成功: {formula}")
            return result

        except Exception as e:
            logger.error(f"公式执行失败: {e}")
            raise ExpressionError(f"公式执行失败: {e}")

    def _preprocess_formula(self, formula: str) -> str:
        """预处理公式"""
        # 移除多余空格
        formula = re.sub(r"\s+", " ", formula.strip())

        # 处理中文字段名
        replacements = {
            "收盘价": "close",
            "开盘价": "open",
            "最高价": "high",
            "最低价": "low",
            "市盈率": "pe",
            "市净率": "pb",
            "净资产收益率": "roe",
            "总资产收益率": "roa",
            "流动比率": "current_ratio",
            "负债率": "debt_ratio",
            "市值": "market_cap",
            "成交量": "volume",
            "换手率": "turnover_rate",
        }

        for chinese, english in replacements.items():
            formula = formula.replace(chinese, english)

        # 处理中文逻辑操作符
        formula = formula.replace("并且", " and ")
        formula = formula.replace("或者", " or ")
        formula = formula.replace("不是", " not ")
        formula = formula.replace("大于", " > ")
        formula = formula.replace("小于", " < ")
        formula = formula.replace("等于", " == ")
        formula = formula.replace("大于等于", " >= ")
        formula = formula.replace("小于等于", " <= ")
        formula = formula.replace("不等于", " != ")

        return formula

    def _extract_components(self, ast_tree: ast.AST) -> List[FormulaComponent]:
        """提取公式组件"""
        components = []

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Compare):
                components.append(
                    FormulaComponent(
                        type="comparison",
                        value=(
                            ast.unparse(node) if hasattr(ast, "unparse") else str(node)
                        ),
                        position=(
                            getattr(node, "lineno", 0),
                            getattr(node, "col_offset", 0),
                        ),
                        dependencies=self._get_node_dependencies(node),
                    )
                )
            elif isinstance(node, ast.BoolOp):
                op_type = "and" if isinstance(node.op, ast.And) else "or"
                components.append(
                    FormulaComponent(
                        type="logical",
                        value=op_type,
                        position=(
                            getattr(node, "lineno", 0),
                            getattr(node, "col_offset", 0),
                        ),
                        dependencies=self._get_node_dependencies(node),
                    )
                )
            elif isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                components.append(
                    FormulaComponent(
                        type="function",
                        value=func_name,
                        position=(
                            getattr(node, "lineno", 0),
                            getattr(node, "col_offset", 0),
                        ),
                        dependencies=self._get_node_dependencies(node),
                    )
                )

        return components

    def _extract_variables(self, ast_tree: ast.AST) -> Set[str]:
        """提取变量名"""
        variables = set()

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                var_name = node.id
                # 排除函数名和常量
                if (
                    var_name not in self.FORMULA_FUNCTIONS
                    and var_name not in self.SCHLOSS_CONSTANTS
                    and not var_name.isupper()
                ):  # 常量通常是大写
                    variables.add(var_name)

        return variables

    def _extract_functions(self, ast_tree: ast.AST) -> Set[str]:
        """提取函数名"""
        functions = set()

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                if func_name:
                    functions.add(func_name)

        return functions

    def _extract_operators(self, ast_tree: ast.AST) -> Set[str]:
        """提取操作符"""
        operators = set()

        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Compare):
                for op in node.ops:
                    operators.add(type(op).__name__)
            elif isinstance(node, ast.BinOp):
                operators.add(type(node.op).__name__)
            elif isinstance(node, ast.BoolOp):
                operators.add(type(node.op).__name__)
            elif isinstance(node, ast.UnaryOp):
                operators.add(type(node.op).__name__)

        return operators

    def _get_function_name(self, call_node: ast.Call) -> Optional[str]:
        """获取函数名"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return None

    def _get_node_dependencies(self, node: ast.AST) -> List[str]:
        """获取节点依赖的变量"""
        dependencies = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id in self.FINANCIAL_FIELDS:
                    dependencies.append(child.id)
        return dependencies

    def _validate_formula_elements(
        self, variables: Set[str], functions: Set[str]
    ) -> Optional[str]:
        """验证公式元素"""
        # 检查未知变量
        unknown_vars = variables - self.FINANCIAL_FIELDS - set(self.SCHLOSS_CONSTANTS.keys())
        if unknown_vars:
            return f"未知变量: {unknown_vars}"

        # 检查未知函数
        unknown_funcs = functions - self.FORMULA_FUNCTIONS
        if unknown_funcs:
            return f"未知函数: {unknown_funcs}"

        return None

    def _test_formula_execution(self, formula: str) -> Optional[str]:
        """测试公式执行"""
        try:
            test_data = self._create_test_data()
            variables = self._prepare_variables(test_data)
            self.evaluator.evaluate(formula, variables)
            return None
        except Exception as e:
            return str(e)

    def _create_test_data(self) -> pd.DataFrame:
        """创建测试数据"""
        np.random.seed(42)
        n_stocks = 10

        data = pd.DataFrame(
            {
                "code": [f"00000{i}" for i in range(n_stocks)],
                "close": np.random.uniform(10, 100, n_stocks),
                "volume": np.random.randint(1000, 100000, n_stocks),
                "market_cap": np.random.uniform(1e8, 1e12, n_stocks),
                "pe": np.random.uniform(5, 50, n_stocks),
                "pb": np.random.uniform(0.5, 10, n_stocks),
                "roe": np.random.uniform(0, 0.3, n_stocks),
                "debt_ratio": np.random.uniform(0, 0.8, n_stocks),
                "current_ratio": np.random.uniform(0.5, 3, n_stocks),
            }
        )

        return data

    def _prepare_variables(
        self, data: pd.DataFrame, constants: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """准备变量字典"""
        variables = {}

        # 添加DataFrame列作为变量
        for col in data.columns:
            if col in self.FINANCIAL_FIELDS:
                variables[col] = data[col].values

        # 添加常量
        variables.update(self.SCHLOSS_CONSTANTS)

        # 添加自定义常量
        if constants:
            variables.update(constants)

        # 添加当前数据引用
        variables["_data"] = data

        return variables
