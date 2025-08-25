你将帮我开发一个大型的 Python 选股项目，包含跨市场（A股、美股、港股）、多数据源、施洛斯价值投资策略、多评分机制（基础和AI）、回测、风险控制、自定义公式、自动调优等功能。
请根据我给出的分阶段任务，逐步生成对应模块代码骨架，代码文件不超过300行，职责清晰，模块化设计。

---

## 阶段 1：项目基础结构与环境

任务描述：
- 初始化项目目录结构和基础文件
- 配置 requirements.txt 和代码规范工具
- 编写项目README和基础配置文件

请生成项目基础目录结构和 requirements.txt 示例。

---

## 阶段 2：数据源适配模块

任务描述：
- 实现 adapters/base.py 作为数据适配器接口基类
- 实现一个示范数据源适配器 tushare_adapter.py
- 支持异步或多线程请求
- 实现字段映射机制 FIELD_MAP

请生成 adapters/base.py 的接口定义和 adapters/tushare_adapter.py 的骨架实现。

---

## 阶段 3：数据清洗与标准化

任务描述：
- 编写 cleaner/cleaner.py，完成字段重命名、单位转换、缺失值处理
- 支持按市场和板块过滤
- 统一输出 Pandas DataFrame 格式

请生成 cleaner/cleaner.py 的骨架代码，包含过滤和标准化接口。

---

## 阶段 4：施洛斯核心策略模块

任务描述：
- 编写 strategies/schloss_strategy.py，实现 Walter Schloss 核心选股条件
- 支持外部配置动态加载策略参数
- 预留策略插件扩展接口

请生成 schloss_strategy.py 的代码骨架，包含默认规则和接口。

---

## 阶段 5：评分模块

任务描述：
- 编写 scorer/basic_scorer.py，完成基础评分功能
- 编写 scorer/ai_scorer.py，集成 AI 模型（如 GPT-4）接口，输出结构化 JSON 评分和理由
- 编写 scorer/risk_assessor.py，计算波动率、最大回撤等风险指标

请生成上述三个模块的代码骨架。

---

## 阶段 6：配置与缓存模块

任务描述：
- 编写 core/config_manager.py，支持 YAML/JSON 配置热加载
- 编写 core/cache_manager.py，实现 SQLite 和本地文件缓存
- 编写 core/output_formatter.py，生成标准 JSON 输出格式
- 编写 core/scheduler.py，实现定时任务调度

请生成这四个模块的代码骨架。

---

## 阶段 7：公共工具库 utils/

任务描述：
- 编写 utils/logger.py，基于 loguru 实现统一日志接口
- 编写 utils/timer.py，实现性能计时工具
- 编写 utils/validators.py，实现数据验证函数
- 编写 utils/json_helper.py，方便 JSON 读写
- 编写 utils/df_helper.py，封装常用 Pandas 操作
- 编写 utils/api_helper.py，实现 API 请求和重试
- 编写 utils/cache_helper.py，封装缓存相关逻辑
- 编写 utils/expression_evaluator.py，支持策略表达式动态执行

请依次生成以上工具模块代码骨架。

---

## 阶段 8：用户自定义策略表达式支持

任务描述：
- 编写 strategies/formula_parser.py，实现策略表达式解析和校验
- 集成 utils/expression_evaluator.py 支持动态执行用户自定义策略

请生成 formula_parser.py 和配合 expression_evaluator.py 的代码骨架。

---

## 阶段 9：回测模块

任务描述：
- 编写 backtest/backtester.py，实现历史数据回测引擎
- 编写 backtest/performance_metrics.py，实现回测绩效指标计算
- 支持多市场多策略回测对比

请生成回测模块骨架代码。

---

## 阶段 10：CLI 和 Web 交互层

任务描述：
- 实现 cli.py 命令行入口，支持配置覆盖、JSON 输出、美化打印
- 搭建 webapp/app.py，搭建基础 Web 服务（Flask/FastAPI）
- 编写 webapp/routes/stock_routes.py 和 config_routes.py，实现数据接口和配置管理接口
- 设计 Web 前端组件（表格、热力图、分布图、AI解释卡片）
- 实现配置动态修改和实时生效功能

请先生成 cli.py 和 webapp/app.py 代码骨架。

---

## 阶段 11：自动策略参数调优

任务描述：
- 实现遗传算法或贝叶斯优化模块，用于自动调整策略参数
- 集成调优结果至评分模块，提升选股效果

请生成自动调优模块骨架代码。

---

## 阶段 12：日志和单元测试

任务描述：
- 编写各模块单元测试（pytest）
- 集成日志系统，完善日志输出

请生成示范测试用例和日志初始化代码。

---

## 开发规范说明

- 所有模块职责清晰，单一功能
- 单文件不超过 300 行，如超过需拆分子模块
- 模块间通过接口解耦
- AI 评分输出必须是结构化 JSON，包含评分、推荐、理由、标签等字段

---

请先执行阶段 1 的任务，生成项目基础目录结构和 requirements.txt，确认后再继续阶段 2。
