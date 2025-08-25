# FinancialAgent - 智能选股系统

一个基于施洛斯价值投资策略的跨市场智能选股系统，支持A股、美股、港股的多数据源分析、AI评分、回测和自动调优。

## 项目特性

### 🌐 跨市场支持
- **A股市场**：沪深主板、创业板、科创板
- **美股市场**：纳斯达克、纽交所
- **港股市场**：主板、创业板

### 📊 多数据源集成
- **Tushare**：A股专业数据
- **Yahoo Finance**：全球市场数据
- **AKShare**：多市场金融数据
- **自定义适配器**：支持扩展更多数据源

### 🎯 施洛斯价值投资策略
- 低P/E、P/B比率筛选
- 债务比率控制
- 盈利稳定性分析
- 分红历史评估
- 支持自定义策略表达式

### 🤖 智能评分系统
- **基础评分**：财务指标量化评分
- **AI评分**：GPT-4等大模型深度分析
- **风险评估**：波动率、最大回撤、VaR计算
- **综合评分**：多维度权重评分

### 📈 回测与优化
- 历史数据回测引擎
- 多策略对比分析
- 绩效指标计算
- 参数自动调优（遗传算法、贝叶斯优化）

### 🔧 系统特性
- 模块化设计，易于扩展
- 异步数据获取，高性能
- 智能缓存机制
- 配置热加载
- RESTful API接口
- Web界面管理

## 项目结构

```
FinancialAgent/
├── adapters/           # 数据源适配器
│   ├── base.py        # 适配器基类
│   ├── tushare_adapter.py
│   ├── yfinance_adapter.py
│   └── akshare_adapter.py
├── cleaner/           # 数据清洗模块
│   └── cleaner.py
├── strategies/        # 投资策略模块
│   ├── schloss_strategy.py
│   └── formula_parser.py
├── scorer/           # 评分模块
│   ├── basic_scorer.py
│   ├── ai_scorer.py
│   └── risk_assessor.py
├── core/            # 核心模块
│   ├── config_manager.py
│   ├── cache_manager.py
│   ├── output_formatter.py
│   └── scheduler.py
├── backtest/        # 回测模块
│   ├── backtester.py
│   └── performance_metrics.py
├── utils/           # 工具库
│   ├── logger.py
│   ├── timer.py
│   ├── validators.py
│   └── ...
├── webapp/          # Web应用
│   ├── app.py
│   ├── routes/
│   ├── static/
│   └── templates/
├── tests/           # 测试用例
├── config/          # 配置文件
├── data/            # 数据存储
├── logs/            # 日志文件
└── cli.py           # 命令行入口
```

## 快速开始

### 环境安装

```bash
# 克隆项目
git clone <repository-url>
cd FinancialAgent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置设置

1. 复制配置模板：
```bash
cp config/config.example.yaml config/config.yaml
```

2. 编辑配置文件，设置API密钥：
```yaml
data_sources:
  tushare:
    token: "your_tushare_token"
  # ... 其他配置
```

### 运行示例

```bash
# 命令行模式
python cli.py --market A股 --strategy schloss --output json

# Web服务模式
python webapp/app.py

# 回测模式
python cli.py --backtest --start-date 2020-01-01 --end-date 2023-12-31
```

## API文档

### 命令行接口

```bash
# 基本选股
python cli.py --market A股 --strategy schloss

# 自定义策略
python cli.py --formula "PE < 15 AND PB < 2 AND ROE > 0.1"

# 输出格式
python cli.py --output json --pretty --save results.json

# 回测分析
python cli.py --backtest --period 1y --benchmark 000300.SH
```

### Web API

```http
# 获取选股结果
GET /api/stocks/screen?market=A股&strategy=schloss

# 获取股票评分
GET /api/stocks/{symbol}/score

# 配置管理
GET /api/config
POST /api/config/update
```

## 配置说明

### 策略配置

```yaml
strategies:
  schloss:
    pe_max: 15.0        # 最大市盈率
    pb_max: 2.0         # 最大市净率
    debt_ratio_max: 0.4 # 最大负债率
    roe_min: 0.1        # 最小净资产收益率
    dividend_years: 3   # 分红年数要求
```

### 评分权重

```yaml
scoring:
  weights:
    basic_score: 0.4    # 基础评分权重
    ai_score: 0.4       # AI评分权重
    risk_score: 0.2     # 风险评分权重
```

## 开发指南

### 添加新数据源

1. 继承 `adapters.base.BaseAdapter`
2. 实现必要的接口方法
3. 配置字段映射
4. 注册到配置文件

### 自定义策略

1. 继承 `strategies.base.BaseStrategy`
2. 实现选股逻辑
3. 或使用公式解析器创建表达式策略

### 扩展评分模块

1. 继承相应的评分基类
2. 实现评分算法
3. 注册到评分管道

## 测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_adapters.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 性能优化

- 使用异步请求提高数据获取效率
- 智能缓存减少重复计算
- 数据库索引优化查询性能
- 分布式计算支持大规模回测

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

- 项目主页：[项目链接]
- 问题反馈：[Issues链接]
- 技术交流：[讨论区链接]
