#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
TuShare异步版本测试脚本
Created on 2024/01/01
@author: AI Assistant
"""

import asyncio
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import async_tushare as ats
    print("✅ 异步模块导入成功")
except ImportError as e:
    print(f"❌ 异步模块导入失败: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 基本功能测试 ===")
    
    # 创建异步TuShare实例
    async_ts = ats.AsyncTuShare()
    
    # 测试1: 获取实时行情（模拟）
    print("1. 测试实时行情获取...")
    try:
        # 这里可能会因为网络或API限制而失败，我们捕获异常
        quotes = await async_ts.get_realtime_quotes(['000001'])
        if quotes is not None:
            print(f"   ✅ 成功获取 {len(quotes)} 条行情数据")
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ 获取行情失败: {e}")
    
    # 测试2: 获取基金数据
    print("2. 测试基金数据获取...")
    try:
        nav_data = await async_ts.get_nav_open('equity')
        if nav_data is not None:
            print(f"   ✅ 成功获取 {len(nav_data)} 条基金数据")
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ 获取基金数据失败: {e}")
    
    # 测试3: 获取票房数据
    print("3. 测试票房数据获取...")
    try:
        boxoffice = await async_ts.get_realtime_boxoffice()
        if boxoffice is not None:
            print(f"   ✅ 成功获取 {len(boxoffice)} 条票房数据")
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ 获取票房数据失败: {e}")


async def test_performance():
    """测试性能"""
    print("\n=== 性能测试 ===")
    
    async_ts = ats.AsyncTuShare()
    
    # 测试批量获取性能
    print("测试批量获取多组数据的性能...")
    
    symbols_groups = [
        ['000001', '000002'],
        ['600000', '600001'],
        ['300001', '300002']
    ]
    
    start_time = time.time()
    try:
        # 并发获取多组数据
        tasks = []
        for symbols in symbols_groups:
            task = async_ts.get_realtime_quotes(symbols)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        print(f"   ✅ 并发获取完成: {success_count}/{len(tasks)} 成功")
        print(f"   ⏱️ 耗时: {elapsed:.2f} 秒")
        
    except Exception as e:
        print(f"   ❌ 批量获取失败: {e}")


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 错误处理测试 ===")
    
    async_ts = ats.AsyncTuShare()
    
    # 测试无效股票代码
    print("1. 测试无效股票代码处理...")
    try:
        result = await async_ts.get_realtime_quotes(['INVALID_CODE'])
        if result is not None:
            print("   ⚠️ 意外获取到数据")
        else:
            print("   ✅ 正确处理无效代码（返回None）")
    except Exception as e:
        print(f"   ✅ 正确抛出异常: {type(e).__name__}")
    
    # 测试超时处理
    print("2. 测试超时处理...")
    try:
        # 设置很短的超时时间
        result = await asyncio.wait_for(
            async_ts.get_realtime_quotes(['000001']), 
            timeout=0.001  # 1毫秒，肯定会超时
        )
    except asyncio.TimeoutError:
        print("   ✅ 正确处理超时异常")
    except Exception as e:
        print(f"   ⚠️ 其他异常: {type(e).__name__}")


async def test_convenience_functions():
    """测试便捷函数"""
    print("\n=== 便捷函数测试 ===")
    
    # 测试便捷函数
    print("1. 测试便捷函数...")
    try:
        quotes = await ats.get_realtime_quotes(['000001'])
        if quotes is not None:
            print("   ✅ 便捷函数工作正常")
        else:
            print("   ⚠️ 便捷函数返回空数据")
    except Exception as e:
        print(f"   ❌ 便捷函数失败: {e}")


def test_imports():
    """测试所有模块导入"""
    print("\n=== 模块导入测试 ===")
    
    modules_to_test = [
        ('tushare.pro.client', 'AsyncDataApi'),
        ('tushare.pro.llm', 'AsyncGPTClient'),
        ('tushare.util.netbase', 'AsyncClient'),
        ('tushare.util.common', 'AsyncClient'),
        ('tushare.trader.trader', 'AsyncTraderAPI'),
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name} 导入成功")
        except ImportError as e:
            print(f"   ❌ {module_name}.{class_name} 导入失败: {e}")
        except AttributeError as e:
            print(f"   ❌ {module_name}.{class_name} 属性错误: {e}")


async def main():
    """主测试函数"""
    print("🚀 TuShare异步版本测试开始")
    print("=" * 50)
    
    # 测试模块导入
    test_imports()
    
    # 测试基本功能
    await test_basic_functionality()
    
    # 测试便捷函数
    await test_convenience_functions()
    
    # 测试错误处理
    await test_error_handling()
    
    # 测试性能
    await test_performance()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    print("\n注意：由于网络环境和API限制，部分测试可能会失败。")
    print("这是正常现象，只要模块能正确导入和处理异常即可。")


if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ Python版本需要3.7+才能支持asyncio")
        sys.exit(1)
    
    # 运行测试
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试过程中发生未处理的异常: {e}")
        import traceback
        traceback.print_exc()