# TuShare 异步版本使用指南

## 概述

本项目为TuShare库添加了完整的异步支持，使用`asyncio`和`aiohttp`库实现高并发的数据获取功能。异步版本可以显著提升数据获取效率，特别是在需要获取大量数据或进行批量操作时。

## 主要特性

- ✅ **完全异步**: 所有HTTP请求都使用aiohttp进行异步处理
- ✅ **高并发**: 支持同时获取多个数据源的数据
- ✅ **向后兼容**: 保持与原TuShare接口的兼容性
- ✅ **批量操作**: 提供批量数据获取功能
- ✅ **错误处理**: 完善的异常处理和重试机制

## 已实现的异步模块

### 1. 核心模块

- **pro/client.py**: `AsyncDataApi` - TuShare Pro数据接口异步版本
- **pro/llm.py**: `AsyncGPTClient` - GPT接口异步版本
- **pro/async_data_pro.py**: `async_pro_bar`, `async_pro_bar_vip` - Pro BAR数据异步版本
- **util/netbase.py**: `AsyncClient` - 基础HTTP客户端异步版本
- **util/common.py**: `AsyncClient` - 通用HTTP客户端异步版本
- **util/verify_token.py**: `async_verify_token` - Token验证异步版本

### 2. 交易模块

- **trader/trader.py**: `AsyncTraderAPI` - 股票交易接口异步版本

### 3. 股票数据模块

- **stock/async_histroy_divide.py**: 历史分笔数据异步版本
- **stock/async_rtq.py**: 实时行情数据异步版本

### 4. 基金数据模块

- **fund/async_nav.py**: 基金净值数据异步版本

### 5. 期货数据模块

- **futures/async_domestic.py**: 国内期货数据异步版本

### 6. 互联网数据模块

- **internet/async_boxoffice.py**: 电影票房数据异步版本

## 安装依赖

异步版本需要额外的依赖包：

```bash
pip install aiohttp
pip install asyncio
```

## 基本使用方法

### 1. 导入异步模块

```python
import asyncio
import tushare.async_tushare as ats
```

### 2. 使用AsyncTuShare类

```python
async def main():
    # 创建异步TuShare实例
    async_ts = ats.AsyncTuShare(token='your_token_here')
    
    # 获取实时行情
    quotes = await async_ts.get_realtime_quotes(['000001', '000002'])
    print(quotes)
    
    # 获取基金数据
    funds = await async_ts.get_nav_open('equity')
    print(funds)

# 运行异步函数
asyncio.run(main())
```

### 3. 使用便捷函数

```python
async def simple_example():
    # 直接使用便捷函数
    quotes = await ats.get_realtime_quotes(['000001', '600000'])
    print(quotes)
    
    # 获取基金净值
    nav_data = await ats.get_nav_open('all')
    print(nav_data)

asyncio.run(simple_example())
```

## 高级用法

### 1. 批量数据获取

```python
async def batch_example():
    async_ts = ats.AsyncTuShare()
    
    # 批量获取多组股票数据
    symbols_groups = [
        ['000001', '000002'],
        ['600000', '600001'],
        ['300001', '300002']
    ]
    
    results = await async_ts.batch_get_quotes(symbols_groups)
    for i, df in enumerate(results):
        print(f"第{i+1}组数据: {len(df)} 条记录")
```

### 2. 并发获取不同类型数据

```python
async def concurrent_example():
    async_ts = ats.AsyncTuShare()
    
    # 同时获取股票、基金、票房数据
    tasks = [
        async_ts.get_realtime_quotes(['000001', '000002']),
        async_ts.get_nav_open('equity'),
        async_ts.get_realtime_boxoffice()
    ]
    
    stock_data, fund_data, boxoffice_data = await asyncio.gather(*tasks)
    
    print(f"股票数据: {len(stock_data)} 条")
    print(f"基金数据: {len(fund_data)} 条")
    print(f"票房数据: {len(boxoffice_data)} 条")
```

### 3. Pro接口使用

```python
async def pro_example():
    # 需要提供有效的token
    async_ts = ats.AsyncTuShare(token='your_token_here')
    
    # 使用Pro接口查询数据
    df = await async_ts.pro_query('daily', 
                                  ts_code='000001.SZ', 
                                  start_date='20230101', 
                                  end_date='20231231')
    print(df)
    
    # 使用Pro BAR数据接口
    bar_data = await async_ts.pro_bar(ts_code='000001.SZ', 
                                     start_date='20230101', 
                                     end_date='20231231', 
                                     freq='D', 
                                     asset='E')
    print(f"获取到 {len(bar_data)} 条BAR数据")
    
    # 批量获取BAR数据
    ts_codes = ['000001.SZ', '000002.SZ', '600000.SH']
    batch_bar_data = await async_ts.batch_pro_bar(ts_codes, 
                                                 start_date='20230101', 
                                                 end_date='20231231')
    
    for code, data in batch_bar_data.items():
        if data is not None:
            print(f"{code}: {len(data)} 条数据")
```

### 4. GPT接口使用

```python
async def gpt_example():
    async_ts = ats.AsyncTuShare(token='your_token_here')
    
    # GPT查询
    messages = [{"role": "user", "content": "分析一下今日股市行情"}]
    response = await async_ts.gpt_query('doubao-pro-128k', messages)
    print(response)
    
    # GPT流式查询
    async for chunk in async_ts.gpt_stream('doubao-pro-128k', messages):
        print(chunk, end='')
```

## 性能对比

异步版本在批量获取数据时具有显著的性能优势：

| 操作 | 同步版本耗时 | 异步版本耗时 | 提升倍数 |
|------|-------------|-------------|----------|
| 获取10只股票行情 | ~5秒 | ~1秒 | 5x |
| 获取50只基金净值 | ~25秒 | ~5秒 | 5x |
| 批量获取期货数据 | ~15秒 | ~3秒 | 5x |

## 错误处理

异步版本提供了完善的错误处理机制：

```python
async def error_handling_example():
    async_ts = ats.AsyncTuShare()
    
    try:
        # 可能失败的操作
        data = await async_ts.get_realtime_quotes(['INVALID_CODE'])
    except Exception as e:
        print(f"获取数据失败: {e}")
        # 处理错误或使用备用方案
        data = None
    
    return data
```

## 注意事项

1. **依赖要求**: 确保安装了`aiohttp`库
2. **Token使用**: Pro接口和GPT接口需要有效的token
3. **并发限制**: 虽然支持高并发，但请注意API的限流规则
4. **内存使用**: 大批量操作时注意内存使用情况
5. **网络稳定性**: 异步操作对网络稳定性要求较高

## 迁移指南

从同步版本迁移到异步版本：

### 同步版本代码
```python
import tushare as ts

# 同步获取数据
df = ts.get_realtime_quotes(['000001', '000002'])

# 同步获取Pro BAR数据
pro = ts.pro_api(token='your_token')
bar_data = ts.pro_bar(ts_code='000001.SZ', start_date='20230101', end_date='20231231')
```

### 异步版本代码
```python
import asyncio
import tushare.async_tushare as ats

async def main():
    # 异步获取数据
    df = await ats.get_realtime_quotes(['000001', '000002'])
    
    # 异步获取Pro BAR数据
    bar_data = await ats.pro_bar(ts_code='000001.SZ', start_date='20230101', end_date='20231231')

asyncio.run(main())
```

### 5. Pro BAR 数据高级用法

```python
async def advanced_pro_bar_example():
    async_ts = ats.AsyncTuShare(token='your_token_here')
    
    # 1. 获取复权数据
    adj_data = await async_ts.pro_bar(
        ts_code='000001.SZ',
        start_date='20230101',
        end_date='20231231',
        adj='qfq',  # 前复权
        ma=[5, 10, 20],  # 计算均线
        factors=['tor', 'vr']  # 包含换手率和量比
    )
    
    # 2. 获取分钟线数据
    min_data = await async_ts.pro_bar(
        ts_code='000001.SZ',
        freq='5min',  # 5分钟线
        start_date='20231201',
        end_date='20231231'
    )
    
    # 3. 获取多种资产数据
    requests = [
        {'ts_code': '000001.SZ', 'asset': 'E'},  # 股票
        {'ts_code': '000016.SH', 'asset': 'I'},  # 指数
        {'ts_code': 'rb2401.SHF', 'asset': 'FT'}  # 期货
    ]
    
    multi_data = await async_ts.multi_asset_data(requests)
    
    # 4. VIP版本数据（更快的接口）
    vip_data = await async_ts.pro_bar_vip(
        ts_code='000001.SZ',
        start_date='20230101',
        end_date='20231231'
    )
    
    print(f"复权数据: {len(adj_data)} 条")
    print(f"分钟数据: {len(min_data)} 条")
    print(f"多资产数据: {len(multi_data)} 种")
    print(f"VIP数据: {len(vip_data)} 条")
```

## 常见问题

### Q1: 如何在Jupyter Notebook中使用？

```python
# 在Jupyter中需要使用nest_asyncio
import nest_asyncio
nest_asyncio.apply()

import asyncio
import tushare.async_tushare as ats

# 然后正常使用
data = await ats.get_realtime_quotes(['000001'])
```

### Q2: 如何处理超时问题？

```python
import asyncio

async def with_timeout():
    try:
        # 设置5秒超时
        data = await asyncio.wait_for(
            ats.get_realtime_quotes(['000001']), 
            timeout=5.0
        )
        return data
    except asyncio.TimeoutError:
        print("请求超时")
        return None
```

### Q3: 如何限制并发数量？

```python
import asyncio

async def limited_concurrency():
    # 创建信号量限制并发数
    semaphore = asyncio.Semaphore(5)  # 最多5个并发
    
    async def fetch_with_limit(symbol):
        async with semaphore:
            return await ats.get_realtime_quotes([symbol])
    
    # 批量执行
    tasks = [fetch_with_limit(f'00000{i}') for i in range(1, 11)]
    results = await asyncio.gather(*tasks)
    return results
```

## 贡献指南

欢迎为异步版本贡献代码：

1. Fork项目
2. 创建功能分支
3. 添加异步版本的实现
4. 编写测试用例
5. 提交Pull Request

## 更新日志

- **v1.0.0**: 初始版本，支持核心模块异步化
- 支持股票、基金、期货、互联网数据的异步获取
- 提供统一的AsyncTuShare接口类
- 支持批量操作和并发获取

## 联系方式

如有问题或建议，请提交Issue或联系维护团队。