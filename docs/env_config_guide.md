# 环境配置使用手册

## 概述

`utils/env_config.py` 模块提供了完整的环境配置管理功能，支持从 `.env` 文件和系统环境变量读取配置，特别支持各种 `baseurl` 自定义配置。

## 快速开始

### 1. 设置环境变量

复制 `.env.example` 为 `.env` 并设置您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 应用环境
ENVIRONMENT=development
DEBUG=true

# Tushare 配置
TUSHARE_TOKEN=your_tushare_token_here
TUSHARE_BASEURL=http://api.tushare.pro

# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASEURL=https://api.openai.com/v1
# 或者使用自定义API服务
AI_BASE_URL=https://api.65536.dev/v1

# 其他配置...
```

### 2. 在代码中使用

```python
from utils.env_config import env_config

# 获取基础配置
print(f"环境: {env_config.environment}")
print(f"调试模式: {env_config.debug}")

# 获取API配置
print(f"Tushare Base URL: {env_config.tushare_baseurl}")
print(f"OpenAI Base URL: {env_config.openai_baseurl}")

# 获取数据源配置
tushare_config = env_config.get_data_source_config('tushare')
openai_config = env_config.get_data_source_config('openai')
```

### 3. 在适配器中使用

```python
from adapters import TushareAdapter
from utils.env_config import env_config

# 方式1：自动从环境变量读取
adapter = TushareAdapter({})

# 方式2：使用环境配置辅助
config = env_config.get_data_source_config('tushare')
adapter = TushareAdapter(config)
```

## 支持的配置项

### 基础应用配置

| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `ENVIRONMENT` | `env_config.environment` | `development` | 应用环境 |
| `DEBUG` | `env_config.debug` | `False` | 调试模式 |
| `LOG_LEVEL` | `env_config.log_level` | `INFO` | 日志级别 |

### 数据源配置

#### Tushare
| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `TUSHARE_TOKEN` | `env_config.tushare_token` | `None` | API Token |
| `TUSHARE_BASEURL` | `env_config.tushare_baseurl` | `http://api.tushare.pro` | API地址 |

#### OpenAI
| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `OPENAI_API_KEY` | `env_config.openai_api_key` | `None` | API Key |
| `OPENAI_BASEURL` | `env_config.openai_baseurl` | `https://api.openai.com/v1` | API地址 |
| `AI_BASE_URL` | 同上 | 同上 | 兼容性别名 |
| `OPENAI_MODEL` | `env_config.openai_model` | `gpt-4` | 模型名称 |

#### Anthropic
| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `ANTHROPIC_API_KEY` | `env_config.anthropic_api_key` | `None` | API Key |
| `ANTHROPIC_BASEURL` | `env_config.anthropic_baseurl` | `https://api.anthropic.com` | API地址 |

### Web应用配置

| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `WEBAPP_HOST` | `env_config.webapp_host` | `0.0.0.0` | 服务器地址 |
| `WEBAPP_PORT` | `env_config.webapp_port` | `8000` | 服务器端口 |
| `WEBAPP_DEBUG` | `env_config.webapp_debug` | `False` | Web调试模式 |

### 性能配置

| 环境变量 | 属性访问 | 默认值 | 说明 |
|---------|---------|--------|------|
| `MAX_WORKERS` | `env_config.max_workers` | `4` | 最大工作线程 |
| `REQUEST_TIMEOUT` | `env_config.request_timeout` | `30` | 请求超时(秒) |
| `BATCH_SIZE` | `env_config.batch_size` | `100` | 批处理大小 |

## API 方法

### 基础获取方法

```python
# 获取字符串
value = env_config.get_str('KEY_NAME', 'default_value')

# 获取整数
value = env_config.get_int('KEY_NAME', 0)

# 获取浮点数
value = env_config.get_float('KEY_NAME', 0.0)

# 获取布尔值
value = env_config.get_bool('KEY_NAME', False)

# 获取列表（逗号分隔）
value = env_config.get_list('KEY_NAME', default=[])

# 获取必需配置（如果不存在则抛出异常）
value = env_config.require('REQUIRED_KEY')
```

### 高级方法

```python
# 获取数据源配置
config = env_config.get_data_source_config('tushare')
config = env_config.get_data_source_config('openai')
config = env_config.get_data_source_config('anthropic')

# 获取所有配置（隐藏敏感信息）
all_config = env_config.get_all_config()

# 验证必需配置
is_valid, missing = env_config.validate_required_configs()

# 重新加载配置
env_config.reload()
```

## 在适配器中的使用

### 1. Tushare 适配器

```python
from adapters import TushareAdapter

# 自动使用环境配置
adapter = TushareAdapter({})

# 或者显式传入配置
adapter = TushareAdapter({
    'token': 'your_token',
    'baseurl': 'http://custom.api.server.com'
})
```

### 2. 使用工厂模式

```python
from adapters import adapter_factory
from utils.env_config import env_config

# 获取环境配置
configs = {
    'tushare': env_config.get_data_source_config('tushare'),
    'openai': env_config.get_data_source_config('openai')
}

# 创建适配器
tushare_adapter = adapter_factory.create_adapter('tushare', configs['tushare'])
```

## 自定义BaseURL支持

系统支持多种方式设置自定义API地址：

1. **标准方式**：使用具体的环境变量
   ```bash
   TUSHARE_BASEURL=http://your.tushare.server.com
   OPENAI_BASEURL=https://your.openai.proxy.com/v1
   ```

2. **兼容性方式**：使用通用别名
   ```bash
   AI_BASE_URL=https://api.65536.dev/v1  # 会被用作OpenAI的baseurl
   ```

3. **代码中动态设置**：
   ```python
   config = {
       'token': 'your_token',
       'baseurl': 'http://custom.server.com'
   }
   adapter = TushareAdapter(config)
   ```

## 配置优先级

配置的读取优先级从高到低：

1. 代码中直接传入的配置
2. `.env` 文件中的配置
3. 系统环境变量
4. 默认值

## 安全注意事项

1. **敏感信息保护**：`get_all_config()` 方法会自动隐藏包含 `token`、`key`、`secret` 的敏感配置

2. **`.env` 文件安全**：
   - 不要将 `.env` 文件提交到版本控制系统
   - 使用 `.env.example` 作为模板
   - 在生产环境中使用更安全的配置管理方式

3. **配置验证**：使用 `validate_required_configs()` 验证必需配置是否完整

## 故障排除

### 常见问题

1. **配置未生效**：
   - 检查 `.env` 文件是否存在
   - 检查环境变量名是否正确
   - 尝试重新加载：`env_config.reload()`

2. **适配器创建失败**：
   - 检查必需的API密钥是否设置
   - 检查baseurl格式是否正确
   - 查看日志输出获取详细错误信息

3. **自定义baseurl不生效**：
   - 确认环境变量名正确
   - 检查是否有多个baseurl配置冲突
   - 验证URL格式是否有效

### 调试方法

```python
# 检查特定配置
print(f"Tushare Token: {env_config.tushare_token}")
print(f"OpenAI BaseURL: {env_config.openai_baseurl}")

# 查看所有配置
print(env_config.get_all_config())

# 验证配置
is_valid, missing = env_config.validate_required_configs()
if not is_valid:
    print(f"缺失配置: {missing}")
```
