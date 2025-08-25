"""
命令行界面

提供完整的命令行操作接口，支持策略执行、回测、配置管理等功能
"""

import click
import json
import yaml
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from utils.logger import setup_logger
from core.config_manager import ConfigManager
from adapters.tushare_adapter import TushareAdapter
from cleaner.cleaner import DataCleaner
from strategies.strategy_engine import StrategyEngine, StrategyConfig
from backtest.backtester import BacktestEngine, BacktestConfig
from scorer.basic_scorer import BasicScorer
from utils.json_helper import JSONHelper

logger = setup_logger("cli")


class FinancialAgentCLI:
    """财务智能体命令行界面"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.data_adapter = None
        self.data_cleaner = DataCleaner()
        self.strategy_engine = StrategyEngine()
        self.basic_scorer = BasicScorer()
        self.json_helper = JSONHelper()

    def _initialize_adapter(self, source: str = "tushare"):
        """初始化数据适配器"""
        if source == "tushare":
            self.data_adapter = TushareAdapter()
        else:
            raise ValueError(f"不支持的数据源: {source}")

    def _format_output(
        self, data: Any, format_type: str = "json", pretty: bool = True
    ) -> str:
        """格式化输出"""
        if format_type == "json":
            if pretty:
                return json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                return json.dumps(data, ensure_ascii=False, default=str)
        elif format_type == "yaml":
            return yaml.dump(data, allow_unicode=True, default_flow_style=False)
        elif format_type == "table":
            if isinstance(data, pd.DataFrame):
                return data.to_string()
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                df = pd.DataFrame(data)
                return df.to_string()
            else:
                return str(data)
        else:
            return str(data)


@click.group()
@click.option("--config", "-c", default="config/default.yaml", help="配置文件路径")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.option("--log-level", default="INFO", help="日志级别")
@click.pass_context
def main(ctx, config, verbose, log_level):
    """财务智能体 - 智能选股系统"""
    ctx.ensure_object(dict)

    # 初始化CLI实例
    cli = FinancialAgentCLI()

    # 加载配置
    try:
        cli.config_manager.load_config(config)
        ctx.obj["cli"] = cli
        ctx.obj["config_file"] = config
        ctx.obj["verbose"] = verbose

        if verbose:
            logger.info(f"加载配置文件: {config}")
            logger.info(f"日志级别: {log_level}")

    except Exception as e:
        click.echo(f"初始化失败: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--source", "-s", default="tushare", help="数据源")
@click.option(
    "--market", "-m", default="all", help="市场(all/a_stock/us_stock/hk_stock)"
)
@click.option("--symbols", help="股票代码列表，逗号分隔")
@click.option("--limit", type=int, default=100, help="返回结果数量限制")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "yaml", "table"]),
    help="输出格式",
)
@click.option("--output", "-o", help="输出文件路径")
@click.pass_context
def fetch_data(ctx, source, market, symbols, limit, output_format, output):
    """获取股票数据"""
    cli = ctx.obj["cli"]

    try:
        # 初始化数据适配器
        cli._initialize_adapter(source)

        # 解析股票代码
        symbol_list = symbols.split(",") if symbols else None

        # 获取数据
        click.echo(f"正在从 {source} 获取 {market} 市场数据...")
        raw_data = cli.data_adapter.fetch_stock_data(
            symbols=symbol_list, market=market, limit=limit
        )

        # 数据清洗
        cleaned_data = cli.data_cleaner.clean_data(raw_data)

        # 转换为输出格式
        if isinstance(cleaned_data, pd.DataFrame):
            result = cleaned_data.head(limit).to_dict("records")
        else:
            result = cleaned_data

        # 格式化输出
        formatted_output = cli._format_output(result, output_format)

        # 输出到文件或控制台
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            click.echo(f"数据已保存到: {output}")
        else:
            click.echo(formatted_output)

        click.echo(f"✓ 成功获取 {len(result)} 条记录")

    except Exception as e:
        click.echo(f"获取数据失败: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--strategy", "-s", required=True, help="策略名称")
@click.option("--market", "-m", default="a_stock", help="目标市场")
@click.option("--top", "-t", type=int, default=20, help="返回前N只股票")
@click.option("--config-file", help="策略配置文件")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "yaml", "table"]),
    help="输出格式",
)
@click.option("--output", "-o", help="输出文件路径")
@click.option("--with-scores", is_flag=True, help="包含评分详情")
@click.pass_context
def screen(ctx, strategy, market, top, config_file, output_format, output, with_scores):
    """执行选股策略"""
    cli = ctx.obj["cli"]

    try:
        # 加载策略配置
        if config_file:
            with open(config_file, "r", encoding="utf-8") as f:
                strategy_config = yaml.safe_load(f)
        else:
            # 使用默认策略配置
            strategy_config = cli.config_manager.get_config("strategies", {}).get(
                strategy
            )

        if not strategy_config:
            click.echo(f"未找到策略配置: {strategy}", err=True)
            sys.exit(1)

        click.echo(f"执行策略: {strategy}")
        click.echo(f"目标市场: {market}")

        # 初始化数据适配器
        cli._initialize_adapter()

        # 获取市场数据
        market_data = cli.data_adapter.fetch_stock_data(market=market)
        cleaned_data = cli.data_cleaner.clean_data(market_data)

        # 创建策略配置对象
        config = StrategyConfig(
            name=strategy,
            description=strategy_config.get("description", ""),
            filters=strategy_config.get("filters", []),
            score_formula=strategy_config.get("score_formula"),
            ranking_formula=strategy_config.get("ranking_formula"),
            signal_formulas=strategy_config.get("signal_formulas"),
            risk_formulas=strategy_config.get("risk_formulas"),
            constants=strategy_config.get("constants", {}),
        )

        # 注册并执行策略
        cli.strategy_engine.register_strategy(config)
        results = cli.strategy_engine.execute_strategy(strategy, cleaned_data)

        # 获取前N只股票
        top_stocks = results.head(top).to_dict("records")

        # 添加评分详情（如果需要）
        if with_scores:
            for stock in top_stocks:
                code = stock.get("code")
                if code:
                    stock_data = cleaned_data[cleaned_data["code"] == code].iloc[0]
                    scores = cli.basic_scorer.calculate_comprehensive_score(
                        stock_data.to_dict()
                    )
                    stock["scores"] = scores

        # 格式化输出
        formatted_output = cli._format_output(top_stocks, output_format)

        # 输出结果
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            click.echo(f"选股结果已保存到: {output}")
        else:
            click.echo(formatted_output)

        click.echo(f"✓ 策略执行完成，筛选出 {len(top_stocks)} 只股票")

    except Exception as e:
        click.echo(f"策略执行失败: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--strategy", "-s", required=True, help="策略名称")
@click.option("--start-date", required=True, help="开始日期 (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="结束日期 (YYYY-MM-DD)")
@click.option("--initial-capital", type=float, default=1000000, help="初始资金")
@click.option("--commission", type=float, default=0.0008, help="手续费率")
@click.option("--rebalance", default="monthly", help="调仓频率")
@click.option("--benchmark", help="基准指数代码")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "yaml", "table"]),
    help="输出格式",
)
@click.option("--output", "-o", help="输出文件路径")
@click.option("--plot", is_flag=True, help="生成图表")
@click.pass_context
def backtest(
    ctx,
    strategy,
    start_date,
    end_date,
    initial_capital,
    commission,
    rebalance,
    benchmark,
    output_format,
    output,
    plot,
):
    """执行策略回测"""
    cli = ctx.obj["cli"]

    try:
        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        click.echo(f"回测策略: {strategy}")
        click.echo(f"回测期间: {start_date} 到 {end_date}")
        click.echo(f"初始资金: {initial_capital:,.0f}")

        # 创建回测配置
        backtest_config = BacktestConfig(
            start_date=start_dt,
            end_date=end_dt,
            initial_capital=initial_capital,
            commission_rate=commission,
            rebalance_frequency=rebalance,
        )

        # 初始化回测引擎
        backtest_engine = BacktestEngine(backtest_config)

        # 获取历史数据
        cli._initialize_adapter()
        historical_data = cli.data_adapter.fetch_historical_data(
            start_date=start_dt, end_date=end_dt
        )

        # 执行回测
        with click.progressbar(length=100, label="回测进行中") as bar:
            result = backtest_engine.run_backtest(historical_data, strategy)
            bar.update(100)

        # 格式化结果
        output_data = {
            "strategy": strategy,
            "period": f"{start_date} to {end_date}",
            "performance_metrics": result["performance_metrics"],
            "trades_summary": {
                "total_trades": len(result.get("trades", [])),
                "win_rate": result["performance_metrics"].get("win_rate", 0),
                "profit_factor": result["performance_metrics"].get("profit_factor", 0),
            },
        }

        # 输出结果
        formatted_output = cli._format_output(output_data, output_format)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(formatted_output)
            click.echo(f"回测结果已保存到: {output}")
        else:
            click.echo(formatted_output)

        # 显示关键指标
        metrics = result["performance_metrics"]
        click.echo(f"\n=== 回测结果摘要 ===")
        click.echo(f"总收益率: {metrics.get('total_return', 0):.2%}")
        click.echo(f"年化收益率: {metrics.get('annual_return', 0):.2%}")
        click.echo(f"最大回撤: {metrics.get('max_drawdown', 0):.2%}")
        click.echo(f"夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
        click.echo(f"✓ 回测完成")

    except Exception as e:
        click.echo(f"回测失败: {e}", err=True)
        sys.exit(1)


@main.group()
def config():
    """配置管理"""
    pass


@config.command()
@click.option(
    "--format",
    "output_format",
    default="yaml",
    type=click.Choice(["json", "yaml"]),
    help="输出格式",
)
@click.pass_context
def show(ctx, output_format):
    """显示当前配置"""
    cli = ctx.obj["cli"]

    try:
        current_config = cli.config_manager.get_all_config()
        formatted_output = cli._format_output(current_config, output_format)
        click.echo(formatted_output)

    except Exception as e:
        click.echo(f"显示配置失败: {e}", err=True)


@config.command()
@click.argument("key")
@click.argument("value")
@click.option(
    "--type",
    "value_type",
    default="auto",
    type=click.Choice(["auto", "str", "int", "float", "bool"]),
    help="值类型",
)
@click.pass_context
def set(ctx, key, value, value_type):
    """设置配置项"""
    cli = ctx.obj["cli"]

    try:
        # 类型转换
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "1", "yes", "on")
        elif value_type == "auto":
            # 自动推断类型
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                if value.lower() in ("true", "false"):
                    value = value.lower() == "true"
                # 否则保持字符串

        # 设置配置
        cli.config_manager.set_config(key, value)
        click.echo(f"✓ 配置已更新: {key} = {value}")

    except Exception as e:
        click.echo(f"设置配置失败: {e}", err=True)


@main.command()
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["json", "yaml", "table"]),
    help="输出格式",
)
@click.pass_context
def list_strategies(ctx, output_format):
    """列出可用策略"""
    cli = ctx.obj["cli"]

    try:
        strategies_config = cli.config_manager.get_config("strategies", {})
        registered_strategies = cli.strategy_engine.list_strategies()

        strategies_info = []
        for name, config in strategies_config.items():
            strategies_info.append(
                {
                    "name": name,
                    "description": config.get("description", ""),
                    "registered": name in registered_strategies,
                    "filters_count": len(config.get("filters", [])),
                    "has_score_formula": bool(config.get("score_formula")),
                }
            )

        formatted_output = cli._format_output(strategies_info, output_format)
        click.echo(formatted_output)

    except Exception as e:
        click.echo(f"列出策略失败: {e}", err=True)


@main.command()
@click.option("--port", "-p", type=int, default=8000, help="端口号")
@click.option("--host", "-h", default="127.0.0.1", help="主机地址")
@click.option("--debug", is_flag=True, help="调试模式")
@click.pass_context
def web(ctx, port, host, debug):
    """启动Web服务"""
    try:
        from webapp.app import create_app

        app = create_app()

        click.echo(f"启动Web服务...")
        click.echo(f"地址: http://{host}:{port}")
        click.echo(f"调试模式: {debug}")

        app.run(host=host, port=port, debug=debug)

    except ImportError:
        click.echo("Web模块未安装，请安装相关依赖", err=True)
    except Exception as e:
        click.echo(f"启动Web服务失败: {e}", err=True)


@main.command()
@click.pass_context
def version(ctx):
    """显示版本信息"""
    version_info = {
        "version": "1.0.0",
        "python_version": sys.version,
        "build_date": "2024-01-01",
    }

    click.echo(json.dumps(version_info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
