"""
核心数据验证器类
"""

import re
from typing import Any, List, Optional, Dict, Callable
from .models import ValidationRule, ValidationType, ValidationError


class DataValidator:
    """数据验证器"""

    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self.errors: List[ValidationError] = []

    def add_rule(self, field: str, rule: ValidationRule) -> "DataValidator":
        if field not in self.rules:
            self.rules[field] = []
        self.rules[field].append(rule)
        return self

    def required(self, field: str, message: str = "字段不能为空") -> "DataValidator":
        rule = ValidationRule(ValidationType.REQUIRED, message)
        return self.add_rule(field, rule)

    def type_check(
        self, field: str, expected_type: type, message: Optional[str] = None
    ) -> "DataValidator":
        if message is None:
            message = f"字段类型必须是 {expected_type.__name__}"
        rule = ValidationRule(
            ValidationType.TYPE, message, lambda v: isinstance(v, expected_type)
        )
        return self.add_rule(field, rule)

    def range_check(
        self,
        field: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        message: Optional[str] = None,
    ) -> "DataValidator":
        if message is None:
            parts = []
            if min_val is not None:
                parts.append(f">= {min_val}")
            if max_val is not None:
                parts.append(f"<= {max_val}")
            message = f"字段值必须 {' 且 '.join(parts)}"

        def validator(value):
            try:
                num_val = float(value)
                if min_val is not None and num_val < min_val:
                    return False
                if max_val is not None and num_val > max_val:
                    return False
                return True
            except (ValueError, TypeError):
                return False

        rule = ValidationRule(ValidationType.RANGE, message, validator)
        return self.add_rule(field, rule)

    def format_check(
        self, field: str, pattern: str, message: Optional[str] = None
    ) -> "DataValidator":
        if message is None:
            message = f"字段格式不符合要求: {pattern}"
        rule = ValidationRule(
            ValidationType.FORMAT, message, lambda v: bool(re.match(pattern, str(v)))
        )
        return self.add_rule(field, rule)

    def custom_check(
        self, field: str, validator_func: Callable, message: str
    ) -> "DataValidator":
        rule = ValidationRule(ValidationType.CUSTOM, message, validator_func)
        return self.add_rule(field, rule)

    def validate(self, data: Dict[str, Any], raise_on_error: bool = True) -> bool:
        self.errors.clear()
        for field, rules in self.rules.items():
            value = data.get(field)
            for rule in rules:
                try:
                    if not self._validate_rule(field, value, rule):
                        error = ValidationError(rule.message, field, value)
                        self.errors.append(error)
                        if raise_on_error:
                            raise error
                except Exception as e:
                    if isinstance(e, ValidationError):
                        raise
                    error = ValidationError(f"验证过程中出错: {str(e)}", field, value)
                    self.errors.append(error)
                    if raise_on_error:
                        raise error
        return not self.errors

    def _validate_rule(self, field: str, value: Any, rule: ValidationRule) -> bool:
        if rule.type == ValidationType.REQUIRED:
            return value is not None and value != ""
        if value is None or value == "":
            return True
        return rule.validator(value) if rule.validator else True

    def get_errors(self) -> List[ValidationError]:
        return self.errors.copy()

    def clear_rules(self) -> "DataValidator":
        self.rules.clear()
        return self
