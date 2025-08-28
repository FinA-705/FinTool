#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
TuShare异步版本 data_pro 模块测试脚本
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
    from pro.async_data_pro import (
        async_pro_api, async_pro_bar, async_pro_bar_vip,
        async_batch_pro_bar, async_multi_asset_data
    )
    import async_tushare as ats
    print("✅ 异步 data_pro 模块导入成功")
except ImportError as e:
    print(f"❌ 异步 data_pro 模块导入失败: {e}")
    sys.exit(1)


async def test_pro_api():
    """测试Pro API初始化"""
    print("\n=== Pro API 初始化测试 ===")
    
    try:
        # 测试不带token的初始化（可能会失败，这是正常的）
        api = async_pro_api()
        if api:
            print("✅ Pro API 初始化成功")
        else:
            print("⚠️ Pro API 初始化失败（可能没有设置token）")
    except Exception as e:
        print(f"⚠️ Pro API 初始化异常: {e}")


async def test_pro_bar():
    """测试Pro BAR数据获取"""
    print("\n=== Pro BAR 数据测试 ===")
    
    # 测试基本BAR数据获取
    print("1. 测试基本BAR数据获取...")
    try:
        data = await async_pro_bar(
            ts_code='000001.SZ',
            start_date='20231201',
            end_date='20231231',
            asset='E'
        )
        if data is not None and len(data) > 0:
            print(f"   ✅ 成功获取 {len(data)} 条BAR数据")
            print(f"   数据列: {list(data.columns)}")
            print(data.head(2))
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ 获取BAR数据失败: {e}")
    
    # 测试带复权的BAR数据
    print("\n2. 测试复权BAR数据获取...")
    try:
        adj_data = await async_pro_bar(
            ts_code='000001.SZ',
            start_date='20231201',
            end_date='20231231',
            adj='qfq',  # 前复权
            ma=[5, 10],  # 均线
            asset='E'
        )
        if adj_data is not None and len(adj_data) > 0:
            print(f"   ✅ 成功获取 {len(adj_data)} 条复权数据")
            # 检查是否包含均线列
            ma_cols = [col for col in adj_data.columns if 'ma' in col.lower()]
            if ma_cols:
                print(f"   均线列: {ma_cols}")
        else:
            print("   ⚠️ 复权数据为空")
    except Exception as e:
        print(f"   ❌ 获取复权数据失败: {e}")


async def test_pro_bar_vip():
    """测试VIP版本的BAR数据"""
    print("\n=== VIP BAR 数据测试 ===")
    
    try:
        vip_data = await async_pro_bar_vip(
            ts_code='000001.SZ',
            start_date='20231201',
            end_date='20231231',
            asset='E'
        )
        if vip_data is not None and len(vip_data) > 0:
            print(f"   ✅ 成功获取 {len(vip_data)} 条VIP数据")
        else:
            print("   ⚠️ VIP数据为空")
    except Exception as e:
        print(f"   ❌ 获取VIP数据失败: {e}")


async def test_batch_pro_bar():
    """测试批量BAR数据获取"""
    print("\n=== 批量 BAR 数据测试 ===")
    
    ts_codes = ['000001.SZ', '000002.SZ', '600000.SH']
    
    print(f"批量获取 {len(ts_codes)} 只股票的数据...")
    start_time = time.time()
    
    try:
        batch_data = await async_batch_pro_bar(
            ts_codes,
            start_date='20231201',
            end_date='20231231',
            asset='E'
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        success_count = sum(1 for v in batch_data.values() if v is not None)
        print(f"   ✅ 批量获取完成: {success_count}/{len(ts_codes)} 成功")
        print(f"   ⏱️ 耗时: {elapsed:.2f} 秒")
        
        for code, data in batch_data.items():
            if data is not None:
                print(f"   {code}: {len(data)} 条数据")
            else:
                print(f"   {code}: 获取失败")
                
    except Exception as e:
        print(f"   ❌ 批量获取失败: {e}")


async def test_multi_asset_data():
    """测试多资产数据获取"""
    print("\n=== 多资产数据测试 ===")
    
    requests = [
        {
            'ts_code': '000001.SZ',
            'asset': 'E',  # 股票
            'start_date': '20231201',
            'end_date': '20231231'
        },
        {
            'ts_code': '000016.SH',
            'asset': 'I',  # 指数
            'start_date': '20231201',
            'end_date': '20231231'
        }
    ]
    
    print(f"获取 {len(requests)} 种不同资产类型的数据...")
    
    try:
        multi_results = await async_multi_asset_data(requests)
        
        success_count = sum(1 for r in multi_results if not isinstance(r, Exception) and r is not None)
        print(f"   ✅ 多资产获取完成: {success_count}/{len(requests)} 成功")
        
        for i, result in enumerate(multi_results):
            request = requests[i]
            if not isinstance(result, Exception) and result is not None:
                print(f"   {request['ts_code']} ({request['asset']}): {len(result)} 条数据")
            else:
                print(f"   {request['ts_code']} ({request['asset']}): 获取失败")
                
    except Exception as e:
        print(f"   ❌ 多资产获取失败: {e}")


async def test_performance_comparison():
    """测试性能对比"""
    print("\n=== 性能对比测试 ===")
    
    ts_codes = ['000001.SZ', '000002.SZ', '600000.SH', '600001.SH', '300001.SZ']
    
    print(f"性能测试：并发获取 {len(ts_codes)} 只股票的数据...")
    
    # 并发获取
    start_time = time.time()
    try:
        tasks = []
        for ts_code in ts_codes:
            task = async_pro_bar(
                ts_code=ts_code,
                start_date='20231201',
                end_date='20231231',
                asset='E'
            )
            tasks.append(task)
        
        concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
        concurrent_time = time.time() - start_time
        
        concurrent_success = sum(1 for r in concurrent_results if not isinstance(r, Exception) and r is not None)
        print(f"   ✅ 并发获取: {concurrent_success}/{len(ts_codes)} 成功，耗时 {concurrent_time:.2f} 秒")
        
    except Exception as e:
        print(f"   ❌ 并发获取失败: {e}")


async def test_integrated_tushare_class():
    """测试集成的TuShare类"""
    print("\n=== 集成 AsyncTuShare 类测试 ===")
    
    # 创建AsyncTuShare实例（不带token，可能部分功能无法使用）
    async_ts = ats.AsyncTuShare()
    
    print("1. 测试AsyncTuShare.pro_bar方法...")
    try:
        data = await async_ts.pro_bar(
            ts_code='000001.SZ',
            start_date='20231201',
            end_date='20231231'
        )
        if data is not None and len(data) > 0:
            print(f"   ✅ 成功通过AsyncTuShare获取 {len(data)} 条数据")
        else:
            print("   ⚠️ 返回数据为空")
    except Exception as e:
        print(f"   ❌ AsyncTuShare.pro_bar失败: {e}")
    
    print("\n2. 测试AsyncTuShare批量获取方法...")
    try:
        batch_data = await async_ts.batch_pro_bar(
            ['000001.SZ', '000002.SZ'],
            start_date='20231201',
            end_date='20231231'
        )
        success_count = sum(1 for v in batch_data.values() if v is not None)
        print(f"   ✅ AsyncTuShare批量获取: {success_count}/{len(batch_data)} 成功")
    except Exception as e:
        print(f"   ❌ AsyncTuShare批量获取失败: {e}")


async def test_convenience_functions():
    """测试便捷函数"""
    print("\n=== 便捷函数测试 ===")
    
    print("1. 测试便捷函数 pro_bar...")
    try:
        data = await ats.pro_bar(
            ts_code='000001.SZ',
            start_date='20231201',
            end_date='20231231'
        )
        if data is not None and len(data) > 0:
            print(f"   ✅ 便捷函数获取 {len(data)} 条数据")
        else:
            print("   ⚠️ 便捷函数返回空数据")
    except Exception as e:
        print(f"   ❌ 便捷函数失败: {e}")
    
    print("\n2. 测试便捷函数 batch_pro_bar...")
    try:
        batch_data = await ats.batch_pro_bar(['000001.SZ', '000002.SZ'])
        success_count = sum(1 for v in batch_data.values() if v is not None)
        print(f"   ✅ 便捷批量函数: {success_count}/{len(batch_data)} 成功")
    except Exception as e:
        print(f"   ❌ 便捷批量函数失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 TuShare异步 data_pro 模块测试开始")
    print("=" * 60)
    
    # 测试Pro API初始化
    await test_pro_api()
    
    # 测试基本BAR数据获取
    await test_pro_bar()
    
    # 测试VIP版本
    await test_pro_bar_vip()
    
    # 测试批量获取
    await test_batch_pro_bar()
    
    # 测试多资产数据
    await test_multi_asset_data()
    
    # 测试性能
    await test_performance_comparison()
    
    # 测试集成的TuShare类
    await test_integrated_tushare_class()
    
    # 测试便捷函数
    await test_convenience_functions()
    
    print("\n" + "=" * 60)
    print("🎉 data_pro 异步模块测试完成！")
    print("\n注意：")
    print("- 由于网络环境和API限制，部分测试可能会失败")
    print("- Pro接口需要有效的token才能正常使用")
    print("- 测试数据仅用于功能验证，请以实际API返回为准")


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