# 特选股模式使用说明

## 概述

特选股模式是一个新增的功能，允许系统在获取A股基础信息时只加载沪深300和中证500指数的成分股，而不是所有A股股票。这个功能对于以下场景特别有用：

- 专注于大盘蓝筹股投资策略
- 减少数据处理量，提高系统响应速度
- 降低API调用次数，节约使用成本
- 关注主流指数成分股的表现

## 功能特性

### 支持的指数
- **沪深300**: 包含沪深两市市值最大、流动性最好的300只股票
- **中证500**: 包含沪深市场中小盘股中市值排名前500的股票

### 工作原理
1. 当启用特选股模式时，系统会先获取沪深300和中证500的成分股列表
2. 自动去重，确保每只股票只出现一次
3. 批量获取这些成分股的基础信息
4. 返回过滤后的数据集

## 配置方法

### 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```dotenv
# 启用特选股模式
SELECTIVE_STOCKS_MODE=true

# 关闭特选股模式（默认）
SELECTIVE_STOCKS_MODE=false
```

### 配置验证

可以通过以下方式检查当前配置状态：

```python
from utils.env_config import env_config

print(f"特选股模式状态: {env_config.selective_stocks_mode}")
```

## 使用示例

### 基本用法

```python
import asyncio
from adapters.factory import AdapterFactory
from adapters.base import DataRequest, DataType, Market

async def get_selective_stocks():
    # 创建Tushare适配器
    adapter = AdapterFactory.create_adapter("tushare")

    # 创建数据请求
    request = DataRequest(
        data_type=DataType.BASIC_INFO,
        market=Market.A_STOCK
    )

    # 获取数据
    response = await adapter.get_data(request)

    if response.success:
        print(f"获取到 {len(response.data)} 只股票数据")
        return response.data
    else:
        print(f"获取失败: {response.message}")
        return None

# 运行示例
asyncio.run(get_selective_stocks())
```

### 直接获取指数成分股列表

```python
import asyncio
from adapters.factory import AdapterFactory

async def get_index_components():
    adapter = AdapterFactory.create_adapter("tushare")

    # 获取沪深300和中证500成分股代码
    stocks = await adapter.get_index_stocks()

    print(f"指数成分股数量: {len(stocks)}")
    print("部分股票代码:", stocks[:10])

    return stocks

# 运行示例
asyncio.run(get_index_components())
```

## 性能影响

### 启用特选股模式
- ✅ **数据量减少**: 从4000+只股票降至约800只股票
- ✅ **响应速度提升**: 数据获取和处理时间显著减少
- ✅ **API调用减少**: 降低Tushare API使用频率
- ✅ **内存占用降低**: 减少内存使用量

### 注意事项
- ⚠️ **覆盖范围**: 只包含指数成分股，可能错过一些小盘股机会
- ⚠️ **更新频率**: 成分股列表会定期调整，需要注意数据时效性
- ⚠️ **API依赖**: 依赖Tushare的index_weight接口

## 错误处理

系统内置了完善的错误处理机制：

1. **指数数据获取失败**: 自动尝试备用方法和不同的指数代码
2. **成分股列表为空**: 自动回退到普通模式，获取所有A股数据
3. **批量请求失败**: 记录警告日志，跳过失败的批次
4. **频率限制**: 自动控制请求间隔，避免触发API限制

## 测试工具

项目包含了一个专门的测试脚本：

```bash
python test_selective_stocks.py
```

此脚本会：
- 检查配置状态
- 验证Tushare连接
- 测试指数成分股获取
- 展示数据样本和统计信息

## 常见问题

### Q: 为什么选择沪深300和中证500？
A: 这两个指数覆盖了中国A股市场的主要投资标的，沪深300代表大盘蓝筹，中证500代表中盘成长，组合起来能够较好地代表市场整体情况。

### Q: 如何验证特选股模式是否生效？
A: 可以查看日志输出，启用特选股模式时会显示"启用特选股模式，获取沪深300和中证500成分股信息"的日志。

### Q: 特选股模式下还能获取指定股票的数据吗？
A: 可以。当DataRequest中指定了symbols参数时，系统会直接获取指定股票的数据，不受特选股模式影响。

### Q: 如何处理成分股调整？
A: 系统每次都会实时获取最新的成分股列表，自动反映指数的调整变化。

## 版本历史

- **v1.0.0**: 初始版本，支持沪深300和中证500成分股筛选
- 支持环境变量配置开关
- 包含完整的错误处理和日志记录
- 提供测试工具和文档

## 相关文件

- `utils/env_config.py`: 环境变量配置管理
- `adapters/tushare_adapter.py`: Tushare适配器实现
- `test_selective_stocks.py`: 测试工具
- `.env.example`: 环境变量配置模板
