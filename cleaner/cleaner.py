"""
数据清洗与标准化模块

负责统一数据格式、字段映射、单位转换、缺失值处理和市场过滤
"""

from typing import Dict, List, Optional, Any, Union
import pandas as pd
import logging
from dataclasses import dataclass

from .field_mapper import FieldMapper, DataSource, StandardFields
from .unit_converter import UnitConverter, Unit
from .data_validator import DataValidator, MissingValueStrategy, OutlierDetectionMethod
from .market_filter import MarketFilter, Market


@dataclass
class CleaningConfig:
    """数据清洗配置"""

    # 字段映射配置
    source: DataSource
    custom_field_mapping: Optional[Dict[str, str]] = None

    # 单位转换配置
    target_units: Optional[Dict[str, Unit]] = None

    # 数据验证配置
    remove_outliers: bool = False
    outlier_method: OutlierDetectionMethod = OutlierDetectionMethod.IQR
    outlier_threshold: float = 3.0

    # 缺失值处理配置
    missing_strategies: Optional[Dict[str, MissingValueStrategy]] = None
    custom_fill_values: Optional[Dict[str, Any]] = None

    # 过滤配置
    filters: Optional[Dict[str, Any]] = None

    # 输出配置
    sort_by: Optional[str] = None
    sort_ascending: bool = True
    reset_index: bool = True


class DataCleaner:
    """数据清洗器主类"""

    def __init__(self):
        self.field_mapper = FieldMapper()
        self.unit_converter = UnitConverter()
        self.data_validator = DataValidator()
        self.market_filter = MarketFilter()
        self.logger = logging.getLogger(__name__)

    def clean_data(self, data: pd.DataFrame, config: CleaningConfig) -> pd.DataFrame:
        """
        执行完整的数据清洗流程

        Args:
            data: 原始数据框
            config: 清洗配置

        Returns:
            清洗后的数据框
        """
        if data.empty:
            self.logger.warning("输入数据为空")
            return data.copy()

        result = data.copy()

        try:
            # 1. 字段映射和重命名
            result = self._map_fields(result, config)

            # 2. 单位转换
            result = self._convert_units(result, config)

            # 3. 数据验证和清洗
            result = self._validate_and_clean(result, config)

            # 4. 市场和板块过滤
            result = self._apply_filters(result, config)

            # 5. 最终格式化
            result = self._format_output(result, config)

            self.logger.info(f"数据清洗完成: {len(data)} -> {len(result)} 行")

        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            raise

        return result

    def _map_fields(self, data: pd.DataFrame, config: CleaningConfig) -> pd.DataFrame:
        """字段映射步骤"""
        result = self.field_mapper.map_fields(data, config.source)

        # 应用自定义字段映射
        if config.custom_field_mapping:
            for original, standard in config.custom_field_mapping.items():
                self.field_mapper.add_custom_mapping(config.source, original, standard)
            result = self.field_mapper.map_fields(data, config.source)

        self.logger.debug(
            f"字段映射完成: {list(data.columns)} -> {list(result.columns)}"
        )
        return result

    def _convert_units(
        self, data: pd.DataFrame, config: CleaningConfig
    ) -> pd.DataFrame:
        """单位转换步骤"""
        source_name = config.source.value
        result = self.unit_converter.standardize_units(
            data, source_name, config.target_units
        )

        self.logger.debug("单位转换完成")
        return result

    def _validate_and_clean(
        self, data: pd.DataFrame, config: CleaningConfig
    ) -> pd.DataFrame:
        """数据验证和清洗步骤"""
        # 验证数据质量
        type_errors = self.data_validator.validate_data_types(data)
        range_errors = self.data_validator.validate_value_ranges(data)

        if type_errors:
            self.logger.warning(f"数据类型错误: {type_errors}")
        if range_errors:
            self.logger.warning(f"数值范围错误: {range_errors}")

        # 执行数据清洗
        result = self.data_validator.clean_data(
            data,
            remove_outliers=config.remove_outliers,
            outlier_method=config.outlier_method,
            missing_strategies=config.missing_strategies,
        )

        self.logger.debug(f"数据验证和清洗完成: {len(data)} -> {len(result)} 行")
        return result

    def _apply_filters(
        self, data: pd.DataFrame, config: CleaningConfig
    ) -> pd.DataFrame:
        """应用过滤条件"""
        if not config.filters:
            return data

        result = self.market_filter.apply_multiple_filters(data, config.filters)

        self.logger.debug(f"过滤完成: {len(data)} -> {len(result)} 行")
        return result

    def _format_output(
        self, data: pd.DataFrame, config: CleaningConfig
    ) -> pd.DataFrame:
        """格式化输出"""
        result = data.copy()

        # 排序
        if config.sort_by and config.sort_by in result.columns:
            result = result.sort_values(
                by=config.sort_by, ascending=config.sort_ascending
            )

        # 重置索引
        if config.reset_index:
            result = result.reset_index(drop=True)

        return result

    def quick_clean(
        self,
        data: pd.DataFrame,
        source: DataSource,
        markets: Optional[Union[Market, List[Market]]] = None,
    ) -> pd.DataFrame:
        """
        快速清洗（使用默认配置）

        Args:
            data: 原始数据框
            source: 数据源类型
            markets: 市场过滤条件

        Returns:
            清洗后的数据框
        """
        filters = {"markets": markets} if markets else None

        config = CleaningConfig(
            source=source, filters=filters, sort_by=StandardFields.SYMBOL
        )

        return self.clean_data(data, config)

    def get_cleaning_report(
        self, original_data: pd.DataFrame, cleaned_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        生成清洗报告

        Args:
            original_data: 原始数据
            cleaned_data: 清洗后数据

        Returns:
            清洗报告
        """
        report = {
            "original_rows": len(original_data),
            "cleaned_rows": len(cleaned_data),
            "rows_removed": len(original_data) - len(cleaned_data),
            "removal_rate": (len(original_data) - len(cleaned_data))
            / len(original_data)
            * 100,
            "original_columns": list(original_data.columns),
            "cleaned_columns": list(cleaned_data.columns),
            "data_quality": {},
        }

        if not cleaned_data.empty:
            report["data_quality"] = self.data_validator.get_data_quality_report(
                cleaned_data
            )

        return report

    def batch_clean(
        self, data_dict: Dict[str, pd.DataFrame], configs: Dict[str, CleaningConfig]
    ) -> Dict[str, pd.DataFrame]:
        """
        批量清洗多个数据集

        Args:
            data_dict: 数据集字典 {名称: 数据框}
            configs: 配置字典 {名称: 配置}

        Returns:
            清洗后的数据集字典
        """
        results = {}

        for name, data in data_dict.items():
            if name in configs:
                try:
                    results[name] = self.clean_data(data, configs[name])
                    self.logger.info(f"数据集 '{name}' 清洗完成")
                except Exception as e:
                    self.logger.error(f"数据集 '{name}' 清洗失败: {e}")
                    results[name] = pd.DataFrame()
            else:
                self.logger.warning(f"数据集 '{name}' 缺少配置，跳过清洗")
                results[name] = data.copy()

        return results

    def add_custom_field_mapping(
        self, source: DataSource, original_field: str, standard_field: str
    ):
        """添加自定义字段映射"""
        self.field_mapper.add_custom_mapping(source, original_field, standard_field)

    def add_custom_unit_mapping(self, source: str, field: str, unit: Unit):
        """添加自定义单位映射"""
        self.unit_converter.add_unit_mapping(source, field, unit)

    def add_custom_validation_rule(self, field: str, rule: Dict[str, Any]):
        """添加自定义验证规则"""
        self.data_validator.add_validation_rule(field, rule)

    def add_custom_industry_group(self, group_name: str, industries: List[str]):
        """添加自定义行业分组"""
        self.market_filter.add_industry_group(group_name, industries)

    def get_supported_sources(self) -> List[DataSource]:
        """获取支持的数据源列表"""
        return list(DataSource)

    def get_standard_fields(self) -> List[str]:
        """获取标准字段列表"""
        return self.field_mapper.get_standard_fields()

    def get_available_filters(self) -> Dict[str, Any]:
        """获取可用的过滤选项"""
        return {
            "markets": [market.value for market in Market],
            "industry_groups": self.market_filter.get_available_groups()[
                "industry_groups"
            ],
            "sector_groups": self.market_filter.get_available_groups()["sector_groups"],
            "missing_strategies": [strategy.value for strategy in MissingValueStrategy],
            "outlier_methods": [method.value for method in OutlierDetectionMethod],
        }
