/**
 * 全局配置和常量
 */

// API 基础URL
const API_BASE = window.location.origin + "/api/v1";

// 配置对象
const CONFIG = {
  apiBase: API_BASE,
  refreshInterval: 30000, // 30秒刷新间隔
  chartColors: [
    "#007bff",
    "#28a745",
    "#ffc107",
    "#dc3545",
    "#6c757d",
    "#17a2b8",
  ],
  maxRetries: 3,
  retryDelay: 1000,
};

// 全局状态
const STATE = {
  currentTab: "dashboard",
  stocksTable: null,
  strategiesData: [],
  currentStrategy: null,
  backtestTasks: new Map(),
  systemInfo: {},
};

// 导出配置
window.CONFIG = CONFIG;
window.STATE = STATE;
window.API_BASE = API_BASE;
