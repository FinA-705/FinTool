/**
 * API 请求处理模块
 */

const ApiService = {
  // API请求封装
  request: async (url, options = {}) => {
    const config = {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(API_BASE + url, config);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error("API请求失败:", error);
      // 避免依赖循环，直接使用console而不是Utils.showToast
      if (window.Utils && Utils.showToast) {
        Utils.showToast(`请求失败: ${error.message}`, "error");
      }
      throw error;
    }
  },

  // GET 请求
  get: (url, params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    return ApiService.request(fullUrl);
  },

  // POST 请求
  post: (url, data = {}) => {
    return ApiService.request(url, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // PUT 请求
  put: (url, data = {}) => {
    return ApiService.request(url, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // DELETE 请求
  delete: (url) => {
    return ApiService.request(url, {
      method: "DELETE",
    });
  },
};

// 股票相关API
const StockAPI = {
  // 获取股票数据
  getStockData: (params = {}) => {
    return ApiService.get("/stocks/data", params);
  },

  // 获取单只股票详细信息
  getStockInfo: (stockCode) => {
    return ApiService.get(`/stocks/info/${stockCode}`);
  },

  // 手动缓存财务指标
  cacheMetrics: (params = {}) => {
    return ApiService.post("/stocks/cache-metrics", {}, params);
  },

  // 执行选股策略
  screenStocks: (strategyData) => {
    return ApiService.post("/stocks/screen", strategyData);
  },

  // 获取支持的市场
  getMarkets: () => {
    return ApiService.get("/stocks/markets");
  },

  // 获取行业分类
  getIndustries: (params = {}) => {
    return ApiService.get("/stocks/industries", params);
  },

  // 搜索股票
  searchStocks: (params = {}) => {
    return ApiService.get("/stocks/search", params);
  },

  // 获取热门股票
  getTrendingStocks: (params = {}) => {
    return ApiService.get("/stocks/trending", params);
  },

  // Tushare健康检查
  checkTushareHealth: () => {
    return ApiService.get("/stocks/health/tushare");
  },
};

// 系统相关API
const SystemAPI = {
  // 获取系统统计信息
  getStats: () => {
    return ApiService.get("/stats");
  },

  // 获取系统健康状态
  getHealth: () => {
    return ApiService.get("/health");
  },
};

// 策略相关API
const StrategyAPI = {
  // 获取所有策略
  list: () => {
    return ApiService.get("/strategies");
  },

  // 获取特定策略
  get: (strategyId) => {
    return ApiService.get(`/strategies/${strategyId}`);
  },

  // 创建新策略
  create: (strategyData) => {
    return ApiService.post("/strategies", strategyData);
  },

  // 更新策略
  update: (strategyId, strategyData) => {
    return ApiService.put(`/strategies/${strategyId}`, strategyData);
  },

  // 删除策略
  delete: (strategyId) => {
    return ApiService.delete(`/strategies/${strategyId}`);
  },

  // 执行策略
  execute: (strategyName, topN = 20, params = {}) => {
    const queryParams = { top_n: topN, ...params };
    return ApiService.post(`/strategies/${strategyName}/execute`, {}, queryParams);
  },
};

// 回测相关API
const BacktestAPI = {
  // 运行回测
  run: (backtestData) => {
    return ApiService.post("/backtest/run", backtestData);
  },

  // 异步运行回测
  runAsync: (backtestData) => {
    return ApiService.post("/backtest/run_async", backtestData);
  },

  // 获取回测任务状态
  getTask: (taskId) => {
    return ApiService.get(`/backtest/task/${taskId}`);
  },

  // 获取所有回测任务
  getTasks: (params = {}) => {
    return ApiService.get("/backtest/tasks", params);
  },

  // 删除回测任务
  deleteTask: (taskId) => {
    return ApiService.delete(`/backtest/task/${taskId}`);
  },

  // 比较回测结果
  compare: (compareData) => {
    return ApiService.post("/backtest/compare", compareData);
  },

  // 获取策略回测报告
  getReports: (strategyName, params = {}) => {
    return ApiService.get(`/backtest/reports/${strategyName}`, params);
  },

  // 获取回测结果（兼容旧版本）
  getResults: (backtestId) => {
    return ApiService.get(`/backtest/results/${backtestId}`);
  },

  // 获取回测历史（兼容旧版本）
  getHistory: (params = {}) => {
    return ApiService.get("/backtest/history", params);
  },
};

// 配置相关API
const ConfigAPI = {
  // 获取配置
  get: (section = "") => {
    const url = section ? `/config/${section}` : "/config";
    return ApiService.get(url);
  },

  // 更新配置
  update: (configData) => {
    return ApiService.post("/config", configData);
  },

  // 获取策略配置
  getStrategies: () => {
    return ApiService.get("/config/strategies");
  },

  // 获取数据源配置
  getDataSources: () => {
    return ApiService.get("/config/data_sources");
  },

  // 重新加载配置
  reload: () => {
    return ApiService.post("/config/reload");
  },

  // 重置配置
  reset: () => {
    return ApiService.post("/config/reset");
  },

  // 导出数据
  exportData: () => {
    return ApiService.get("/data/export");
  },
};

// 导出 API 服务
window.ApiService = ApiService;
window.StockAPI = StockAPI;
window.SystemAPI = SystemAPI;
window.StrategyAPI = StrategyAPI;
window.BacktestAPI = BacktestAPI;
window.ConfigAPI = ConfigAPI;
