#!/usr/bin/env python3
"""
测试特选股模式功能

此脚本用于测试和演示特选股模式的工作原理。
在启用特选股模式时，系统将只加载沪深300和中证500成分股。
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from adapters.factory import AdapterFactory
from adapters.base import DataRequest, DataType, Market
from utils.env_config import env_config


async def test_selective_stocks_mode():
    """测试特选股模式"""

    print("=" * 60)
    print("特选股模式测试")
    print("=" * 60)

    # 显示当前配置
    print(f"当前特选股模式状态: {env_config.selective_stocks_mode}")
    print(f"Tushare Token存在: {'是' if env_config.tushare_token else '否'}")
    print()

    if not env_config.tushare_token:
        print("❌ 错误: 未找到Tushare Token")
        print("请在 .env 文件中设置 TUSHARE_TOKEN")
        return

    try:
        # 创建适配器工厂和Tushare适配器
        factory = AdapterFactory()
        config = {"token": env_config.tushare_token}
        adapter = factory.create_adapter("tushare", config)
        print("✅ Tushare适配器创建成功")

        # 健康检查
        print("🔍 执行健康检查...")
        health_result = await adapter.health_check()
        print(f"Token有效: {'✅' if health_result['token_valid'] else '❌'}")
        print(f"基础接口访问: {'✅' if health_result['stock_basic_access'] else '❌'}")
        print()

        if not health_result["token_valid"]:
            print("❌ Token验证失败，无法继续测试")
            return

        # 测试基础信息获取
        print("📊 获取股票基础信息...")
        request = DataRequest(
            data_type=DataType.BASIC_INFO,
            market=Market.A_STOCK,
            limit=10,  # 限制返回10条数据用于测试
        )

        response = await adapter.get_data(request)

        if response.success:
            print(f"✅ 数据获取成功")
            print(f"返回股票数量: {len(response.data)}")
            print(
                f"特选股模式: {'启用' if env_config.selective_stocks_mode else '未启用'}"
            )

            if not response.data.empty:
                print("\n📋 股票样本数据:")
                print("-" * 80)
                sample_data = response.data.head(5)
                for idx, row in sample_data.iterrows():
                    print(
                        f"{row.get('ts_code', 'N/A'):12} {row.get('name', 'N/A'):15} {row.get('industry', 'N/A'):10}"
                    )
                print("-" * 80)

                # 统计行业分布
                if "industry" in response.data.columns:
                    industry_counts = response.data["industry"].value_counts().head(5)
                    print("\n🏢 主要行业分布:")
                    for industry, count in industry_counts.items():
                        print(f"  {industry}: {count}只")
        else:
            print(f"❌ 数据获取失败: {response.message}")

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback

        traceback.print_exc()


async def test_index_stocks():
    """测试指数成分股获取功能"""

    print("\n" + "=" * 60)
    print("指数成分股获取测试")
    print("=" * 60)

    if not env_config.tushare_token:
        print("❌ 错误: 未找到Tushare Token")
        return

    try:
        factory = AdapterFactory()
        config = {"token": env_config.tushare_token}
        adapter = factory.create_adapter("tushare", config)

        print("🔍 获取沪深300和中证500成分股...")
        index_stocks = await adapter.get_index_stocks()

        if index_stocks:
            print(f"✅ 成功获取 {len(index_stocks)} 只指数成分股")
            print("\n📋 部分股票代码:")
            print("-" * 40)
            for i, stock in enumerate(index_stocks[:10]):
                print(f"  {stock}")
            if len(index_stocks) > 10:
                print(f"  ... 还有 {len(index_stocks) - 10} 只股票")
            print("-" * 40)
        else:
            print("❌ 未能获取指数成分股")

    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")


def show_config_help():
    """显示配置帮助信息"""

    print("\n" + "=" * 60)
    print("配置说明")
    print("=" * 60)
    print("要启用特选股模式，请在 .env 文件中设置:")
    print("  SELECTIVE_STOCKS_MODE=true")
    print()
    print("特选股模式将只加载以下指数的成分股:")
    print("  • 沪深300 (000300.SH 或 399300.SZ)")
    print("  • 中证500 (000905.SH)")
    print()
    print("普通模式将加载所有A股股票")
    print("=" * 60)


async def main():
    """主函数"""

    print("🚀 金融代理特选股模式测试工具")

    # 显示配置帮助
    show_config_help()

    # 执行测试
    await test_selective_stocks_mode()
    await test_index_stocks()

    print("\n✅ 测试完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())
