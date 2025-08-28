# FinancialAgent / 智能选股系统（使用指南）

一个基于施洛斯价值投资策略的跨市场智能选股系统，集数据抓取、指标清洗、策略筛选、评分、回测与Web管理于一体。

## 1. 环境与依赖

- Python: 3.13+（见 `pyproject.toml`）
- 系统依赖：可用的 SQLite（内置）、网络可访问 Tushare/Yahoo

安装步骤（推荐虚拟环境）：

```bash
git clone <your-repo-url>
cd FinTool/project

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -U pip
pip install .             # 使用 pyproject 安装依赖
# 或者：pip install -r requirements.txt.bak
```

使用 uv 管理环境（可选，更快更简洁）：

```bash
# 安装 uv（Linux/macOS）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并激活
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖（基于 pyproject.toml）
uv pip install -e .
# 或：uv pip install -r requirements.txt.bak
```

## 2. 必要配置

1) 复制示例配置：

```bash
cp config/config.example.yaml config/config.yaml
```

2) 在 `config/config.yaml` 填写数据源信息（至少 Tushare）：

```yaml
data_sources:
  tushare:
    token: "你的_tushare_token"
```

3) 策略参数位于 `config/strategies.yaml`，默认已提供“schloss”策略。注意单位：

- 市值（market_cap）配置单位为“万元”；Web 前端展示为“亿元”。
- ROE 与资产负债率在配置里使用百分数（如 8 表示 8%）。

## 3. 运行方式

### A) 启动 Web 界面

```bash
python -m uvicorn webapp.app:app --host 127.0.0.1 --port 8002
```

VS Code 用户可直接用任务：Run Web Server (uvicorn) on 8002。

启动后浏览器访问：

- http://127.0.0.1:8002/  首页与列表

首次运行提示：

- 打开“股票列表”页面，点击右上角“刷新股票列表”以触发全量数据获取；
- 切回命令行观察抓取与入库日志，该过程可能需要数分钟（视网络与数据量）；
- 完成后页面会逐步显示数据，如网络不稳定可稍后重试刷新。

常用健康检查：

- GET /api/stocks/health
- GET /api/stocks/market/summary
- GET /api/stocks/metrics/bad-codes  查看疑似异常股票列表

### B) 命令行（可选）

仓库包含 `cli.py`，可用于批处理、回测等（如需请根据项目实际参数扩展）。

## 4. 常用 API（片段）

基础数据与检索：

- GET `/api/stocks/data` 获取股票基础数据（支持缓存）
- GET `/api/stocks/search?q=关键词` 代码/名称检索
- GET `/api/stocks/info/{stock_code}` 个股信息

市场与策略：

- GET `/api/stocks/market/summary` 市场概览
- POST `/api/stocks/screen` 选股（按策略名及参数筛选）

财务指标运维：

- GET `/api/stocks/metrics/bad-codes` 当前疑似异常股票列表
- POST `/api/stocks/metrics/refetch` 重抓指标（传入 `codes` 或 `?all=true`）

返回结构均为统一封装的 `SuccessResponse`，详见 `webapp/models.py`。

## 5. 使用要点与单位说明

- 市值单位：
  - 数据库与后端策略使用“万元”存储；
  - Web 列表展示自动格式化为“亿元/万亿元”。
- ROE/负债率单位：配置与展示以“百分数”表达（如 8 表示 8%）。
- 选择性抓取模式与缓存：系统会优先用数据库缓存，失效时异步抓取并入库。

## 6. 异常监控与重试

- 在财务指标抓取阶段，如 `daily_basic`/`fina_indicator`/`daily` 调用失败（例如“Server disconnected”），对应股票会被“立即”加入缓存异常列表，前端和接口可立刻看到。
- 接口：
  - GET `/api/stocks/metrics/bad-codes` 查看异常列表
  - POST `/api/stocks/metrics/refetch` 触发重抓
    - 请求体：`{"codes": ["000001.SZ", "600000.SH"]}` 或使用 `?all=true`
- 若重抓成功且指标不再异常，系统会自动把该代码从异常列表移除。

## 7. 配置文件速览

- `config/config.yaml`：应用与数据源配置（如 Tushare token）。
- `config/strategies.yaml`：策略阈值（如市值下限、PE/PB范围、ROE/负债率阈值）。
- 提示：放宽非关键约束（行业、交易天数等）能提升候选数量；关键指标建议保留。

## 8. 日志与数据

- 日志目录：`logs/`（含 rolling 文件与压缩包）
- 缓存/数据库：`core/database.py` 使用 SQLite；指标与基础数据会落盘，便于离线浏览与增量更新。

## 9. 常见问题（FAQ）

1) 启动后看不到数据？
   - 确认 `config/config.yaml` 内 Tushare token 有效；
   - 首次启动需要等待数据抓取与入库；
   - 查看 `GET /api/stocks/health` 与服务端日志。

2) 市值单位为什么与页面不同？
   - 后端存“万元”，前端显示“亿元/万亿元”，属预期。

3) 选股结果为 0？
   - 检查 `config/strategies.yaml` 的阈值与单位是否过严；
   - 适当放宽非关键约束，仅保留 PE/PB/ROE/负债率/市值等核心条件。

## 10. 参与开发

- 路由：`webapp/routes`（含市场、数据、策略与维护接口）
- 服务：`webapp/services/stock_data_service.py`（抓取缓存、异常标记）
- 策略：`strategies/schloss_strategy.py` 与 `strategies/config_manager.py`
- 前端：`webapp/templates/` 与 `webapp/static/js/modules/`

欢迎提交 Issue / PR。若需要“图形化策略配置”，可在 Web 端添加配置弹窗与对应 API（见 issue 模板说明或联系我们）。
