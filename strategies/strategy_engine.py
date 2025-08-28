"""
策略引擎

集成公式解析器和施洛斯策略，提供完整的策略执行环境
支持自定义策略、回测和实时选股
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import hashlib

from strategies.schloss_strategy import SchlossStrategy
from strategies.strategy_registry import StrategyRegistry, StrategyConfig
from strategies.strategy_executor import StrategyExecutor
from utils.logger import get_logger
from utils.cache_helper import CacheManager, MemoryCache
from utils.timer import Timer

logger = get_logger(__name__)


class StrategyExecutionMode(Enum):
    """策略执行模式"""

    FILTER_ONLY = "filter_only"  # 仅过滤
    SCORE_ONLY = "score_only"  # 仅评分
    FULL_PIPELINE = "full_pipeline"  # 完整流水线


@dataclass
class StrategyResult:
    """策略执行结果"""

    filtered_stocks: pd.DataFrame  # 过滤后的股票
    scores: Optional[pd.Series]  # 评分结果
    rankings: Optional[pd.Series]  # 排名结果
    signals: Optional[pd.DataFrame]  # 交易信号
    execution_time: float  # 执行时间
    summary: Dict[str, Any]  # 执行摘要


class EnhancedStrategyEngine:
    """增强策略引擎"""

    def __init__(self, cache_size: int = 1000):
        """初始化策略引擎"""
        self.registry = StrategyRegistry()
        self.executor = StrategyExecutor()
        self.schloss_strategy = SchlossStrategy()

        # 缓存系统
        cache_backend = MemoryCache(max_size=cache_size, default_ttl=3600)
        self.cache = CacheManager(cache_backend)

        # 执行统计
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "avg_execution_time": 0.0,
        }

    def register_strategy(self, strategy_config: StrategyConfig) -> bool:
        """注册策略"""
        return self.registry.register_strategy(strategy_config)

    def load_strategy_from_template(
        self, template_name: str, custom_params: Optional[Dict[str, Any]] = None
    ) -> Optional[StrategyConfig]:
        """从模板加载策略"""
        return self.registry.load_strategy_from_template(template_name, custom_params)

    def execute_strategy(
        self,
        strategy_name: str,
        data: pd.DataFrame,
        mode: StrategyExecutionMode = StrategyExecutionMode.FULL_PIPELINE,
        top_n: Optional[int] = None,
    ) -> StrategyResult:
        """执行策略"""
        timer = Timer()
        timer.start()

        try:
            # 获取策略配置
            strategy_config = self.registry.get_strategy(strategy_name)
            if not strategy_config:
                raise ValueError(f"策略未注册: {strategy_name}")

            if not strategy_config.enabled:
                raise ValueError(f"策略已禁用: {strategy_name}")

            # 数据验证
            if not self.executor.validate_input_data(data):
                raise ValueError("输入数据验证失败")

            # 生成缓存键
            cache_key = self._generate_cache_key(strategy_name, data, mode)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info(f"使用缓存结果: {strategy_name}")
                return cached_result

            logger.info(f"执行策略: {strategy_name} (模式: {mode.value})")

            # 准备变量
            variables = self.executor.prepare_variables(data, strategy_config.constants)

            # 执行过滤
            filtered_data = data.copy()
            if mode in [
                StrategyExecutionMode.FILTER_ONLY,
                StrategyExecutionMode.FULL_PIPELINE,
            ]:
                filtered_data = self.executor.execute_filters(
                    strategy_config.filters, data, variables
                )
                logger.info(f"过滤后股票数量: {len(filtered_data)}")

            # 执行评分
            scores = None
            rankings = None
            if mode in [
                StrategyExecutionMode.SCORE_ONLY,
                StrategyExecutionMode.FULL_PIPELINE,
            ]:
                if strategy_config.score_formula:
                    scores = self.executor.execute_scoring(
                        strategy_config.score_formula, filtered_data, variables
                    )

                if strategy_config.ranking_formula:
                    rankings = self.executor.execute_ranking(
                        strategy_config.ranking_formula, filtered_data, variables
                    )
                elif scores is not None:
                    rankings = scores.rank(ascending=False)

            # 执行信号计算
            signals = None
            if strategy_config.signal_formulas:
                signals = self.executor.execute_signals(
                    strategy_config.signal_formulas, filtered_data, variables
                )

            # 应用top_n限制
            if top_n and rankings is not None:
                top_indices = rankings.nsmallest(top_n).index
                filtered_data = filtered_data.loc[top_indices]
                if scores is not None:
                    scores = scores.loc[top_indices]
                rankings = rankings.loc[top_indices]
                if signals is not None:
                    signals = signals.loc[top_indices]

            execution_time = timer.stop()

            # 创建结果
            result = StrategyResult(
                filtered_stocks=filtered_data,
                scores=scores,
                rankings=rankings,
                signals=signals,
                execution_time=execution_time,
                summary=self._create_execution_summary(
                    strategy_name, filtered_data, scores, execution_time
                ),
            )

            # 缓存结果
            self.cache.set(cache_key, result, ttl=1800)  # 30分钟缓存

            # 更新统计
            self._update_execution_stats(execution_time, True)

            logger.info(f"策略执行完成: {strategy_name} (耗时: {execution_time:.2f}秒)")
            return result

        except Exception as e:
            execution_time = timer.stop()
            self._update_execution_stats(execution_time, False)
            logger.error(f"策略执行失败: {e}")
            raise

    def batch_execute_strategies(
        self,
        strategy_names: List[str],
        data: pd.DataFrame,
        mode: StrategyExecutionMode = StrategyExecutionMode.FULL_PIPELINE,
    ) -> Dict[str, StrategyResult]:
        """批量执行策略"""
        results = {}
        for strategy_name in strategy_names:
            try:
                result = self.execute_strategy(strategy_name, data, mode)
                results[strategy_name] = result
            except Exception as e:
                logger.error(f"策略 {strategy_name} 执行失败: {e}")
                continue
        return results

    def create_custom_strategy(
        self,
        name: str,
        description: str,
        filters: List[str],
        score_formula: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """创建自定义策略"""
        return self.registry.create_custom_strategy(
            name, description, filters, score_formula, **kwargs
        )

    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取策略信息"""
        return self.registry.get_strategy_info(strategy_name)

    def list_strategies(self) -> List[str]:
        """列出所有已注册的策略"""
        return self.registry.list_strategies()

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return self.execution_stats.copy()

    def _generate_cache_key(
        self, strategy_name: str, data: pd.DataFrame, mode: StrategyExecutionMode
    ) -> str:
        """生成缓存键"""
        data_hash = hashlib.md5(str(data.values.tobytes()).encode()).hexdigest()[:8]
        return f"strategy_{strategy_name}_{mode.value}_{data_hash}"

    def _create_execution_summary(
        self,
        strategy_name: str,
        filtered_data: pd.DataFrame,
        scores: Optional[pd.Series],
        execution_time: float,
    ) -> Dict[str, Any]:
        """创建执行摘要"""
        summary = {
            "strategy_name": strategy_name,
            "execution_time": execution_time,
            "total_stocks": len(filtered_data),
            "timestamp": datetime.now().isoformat(),
        }

        if scores is not None:
            summary.update(
                {
                    "avg_score": float(scores.mean()),
                    "max_score": float(scores.max()),
                    "min_score": float(scores.min()),
                    "score_std": float(scores.std()),
                }
            )
        return summary

    def _update_execution_stats(self, execution_time: float, success: bool):
        """更新执行统计"""
        self.execution_stats["total_executions"] += 1
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1

        self.execution_stats["total_execution_time"] += execution_time
        self.execution_stats["avg_execution_time"] = (
            self.execution_stats["total_execution_time"]
            / self.execution_stats["total_executions"]
        )


# 使用示例
if __name__ == "__main__":
    import numpy as np

    print("=== 增强策略引擎测试 ===")

    # 创建策略引擎
    engine = EnhancedStrategyEngine()

    # 创建测试数据
    np.random.seed(42)
    test_data = pd.DataFrame(
        {
            "code": [f"00000{i}" for i in range(20)],
            "close": np.random.uniform(10, 100, 20),
            "volume": np.random.randint(1000, 100000, 20),
            "market_cap": np.random.uniform(1e8, 1e12, 20),
            "pe": np.random.uniform(5, 50, 20),
            "pb": np.random.uniform(0.5, 10, 20),
            "roe": np.random.uniform(0, 0.3, 20),
            "debt_ratio": np.random.uniform(0, 0.8, 20),
            "current_ratio": np.random.uniform(0.5, 3, 20),
        }
    )

    print(f"\n测试数据: {len(test_data)} 只股票")

    # 1. 从模板加载策略
    print("\n1. 从模板加载策略:")
    schloss_config = engine.load_strategy_from_template("schloss_basic")
    if schloss_config:
        success = engine.register_strategy(schloss_config)
        print(f"施洛斯策略注册: {'成功' if success else '失败'}")

    # 2. 创建自定义策略
    print("\n2. 创建自定义策略:")
    custom_success = engine.create_custom_strategy(
        name="简单价值策略",
        description="基于PE和PB的简单价值策略",
        filters=["pe > 0 and pe < 20", "pb > 0 and pb < 2", "market_cap > 1e9"],
        score_formula="1/pe + 1/pb + roe",
    )
    print(f"自定义策略创建: {'成功' if custom_success else '失败'}")

    # 3. 执行策略
    print("\n3. 执行策略:")
    strategies = engine.list_strategies()
    print(f"可用策略: {strategies}")

    for strategy_name in strategies:
        try:
            result = engine.execute_strategy(strategy_name, test_data, top_n=5)
            print(f"\n策略: {strategy_name}")
            print(f"过滤后股票数: {len(result.filtered_stocks)}")
            print(f"执行时间: {result.execution_time:.3f}秒")
            if result.scores is not None:
                print(f"平均评分: {result.scores.mean():.2f}")
            print(f"摘要: {result.summary}")

        except Exception as e:
            print(f"策略 {strategy_name} 执行失败: {e}")

    # 4. 批量执行
    print("\n4. 批量执行测试:")
    batch_results = engine.batch_execute_strategies(strategies, test_data)
    print(f"批量执行完成，成功: {len(batch_results)}/{len(strategies)}")

    # 5. 执行统计
    print("\n5. 执行统计:")
    stats = engine.get_execution_stats()
    print(f"总执行次数: {stats['total_executions']}")
    print(f"成功次数: {stats['successful_executions']}")
    print(f"平均执行时间: {stats['avg_execution_time']:.3f}秒")

    print("\n测试完成！")
