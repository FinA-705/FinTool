"""
DataFrame处理工具

提供pandas DataFrame的常用操作和数据处理功能
包括数据清洗、转换、统计分析等
"""

from .data_loader import DataLoader
from .data_cleaner import DataCleaner
from .data_analyzer import DataAnalyzer

# 为了向后兼容，保留原有的DataFrameHelper类
class DataFrameHelper:
    """DataFrame处理助手
    
    整合数据加载、清洗和分析功能的统一接口
    """
    
    # 数据加载方法
    load_csv = staticmethod(DataLoader.load_csv)
    load_excel = staticmethod(DataLoader.load_excel)
    load_json = staticmethod(DataLoader.load_json)
    load_parquet = staticmethod(DataLoader.load_parquet)
    save_to_csv = staticmethod(DataLoader.save_to_csv)
    save_to_excel = staticmethod(DataLoader.save_to_excel)
    save_to_parquet = staticmethod(DataLoader.save_to_parquet)
    
    # 数据清洗方法
    remove_duplicates = staticmethod(DataCleaner.remove_duplicates)
    handle_missing_values = staticmethod(DataCleaner.handle_missing_values)
    remove_outliers = staticmethod(DataCleaner.remove_outliers)
    standardize_columns = staticmethod(DataCleaner.standardize_columns)
    convert_dtypes = staticmethod(DataCleaner.convert_dtypes)
    trim_whitespace = staticmethod(DataCleaner.trim_whitespace)
    validate_data_quality = staticmethod(DataCleaner.validate_data_quality)
    
    # 数据分析方法
    basic_stats = staticmethod(DataAnalyzer.basic_stats)
    correlation_matrix = staticmethod(DataAnalyzer.correlation_matrix)
    group_analysis = staticmethod(DataAnalyzer.group_analysis)
    value_counts_analysis = staticmethod(DataAnalyzer.value_counts_analysis)
    quantile_analysis = staticmethod(DataAnalyzer.quantile_analysis)
    rolling_analysis = staticmethod(DataAnalyzer.rolling_analysis)
    missing_pattern_analysis = staticmethod(DataAnalyzer.missing_pattern_analysis)
    outlier_analysis = staticmethod(DataAnalyzer.outlier_analysis)
    time_series_analysis = staticmethod(DataAnalyzer.time_series_analysis)


# 导出所有类和函数
__all__ = [
    "DataFrameHelper",
    "DataLoader", 
    "DataCleaner",
    "DataAnalyzer",
]
