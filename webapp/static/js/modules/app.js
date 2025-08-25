/**
 * 主应用控制器
 */

const App = {
  // 初始化应用
  init: () => {
    console.log("初始化应用...");

    // 绑定事件
    App.bindEvents();

    // 初始化默认标签页
    App.switchTab("dashboard");

    // 加载初始数据
    App.loadInitialData();

    // 启动定时刷新
    App.startAutoRefresh();

    Utils.showToast("应用初始化完成", "success");
  },

  // 绑定事件
  bindEvents: () => {
    // 导航栏点击事件
    $(".navbar-nav .nav-link").click(function (e) {
      e.preventDefault();
      const tab = $(this).data("tab");
      if (tab) {
        App.switchTab(tab);
      }
    });

    // 表单提交事件
    $("#strategy-form").submit(StrategiesManager.handleSubmit);
    $("#execute-strategy-form").submit(StrategiesManager.handleExecute);
    $("#backtest-form").submit(BacktestManager.handleSubmit);

    // 将函数暴露到全局作用域，供 HTML onclick 调用
    App.exposeGlobalFunctions();
  },

  // 将必要的函数暴露到全局作用域
  exposeGlobalFunctions: () => {
    // 快速操作函数
    window.quickAction = (action) => {
      switch (action) {
        case "fetch-data":
          Dashboard.quickActions.fetchData();
          break;
        case "run-strategy":
          Dashboard.quickActions.runStrategy();
          break;
        case "run-backtest":
          Dashboard.quickActions.runBacktest();
          break;
      }
    };

    // 股票相关函数
    window.refreshStockData = StocksManager.refresh;
    window.exportStockData = StocksManager.export;
    window.searchStocks = StocksManager.search;
    window.showStockDetail = StocksManager.showDetail;
    window.addToWatchlist = StocksManager.addToWatchlist;

    // 策略相关函数
    window.editStrategy = StrategiesManager.edit;
    window.executeStrategy = StrategiesManager.execute;
    window.deleteStrategy = StrategiesManager.delete;

    // 配置相关函数
    window.clearCache = ConfigManager.clearCache;
    window.resetConfig = ConfigManager.resetConfig;
    window.getCacheInfo = ConfigManager.getCacheInfo;
    window.exportData = ConfigManager.exportData;
  },

  // 切换标签页
  switchTab: (tabName) => {
    // 更新导航栏状态
    $(".navbar-nav .nav-link").removeClass("active");
    $(`.navbar-nav .nav-link[data-tab="${tabName}"]`).addClass("active");

    // 切换内容
    $(".tab-content").removeClass("active");
    $(`#${tabName}-tab`).addClass("active");

    STATE.currentTab = tabName;

    // 根据标签页加载对应数据
    switch (tabName) {
      case "dashboard":
        Dashboard.load();
        break;
      case "stocks":
        StocksManager.load();
        break;
      case "strategies":
        StrategiesManager.load();
        break;
      case "backtest":
        BacktestManager.load();
        break;
      case "config":
        ConfigManager.load();
        break;
    }
  },

  // 加载初始数据
  loadInitialData: async () => {
    try {
      // 加载系统信息
      const systemInfo = await SystemAPI.getInfo();
      STATE.systemInfo = systemInfo;

      // 更新系统状态
      App.updateSystemStatus(systemInfo);
    } catch (error) {
      console.error("加载初始数据失败:", error);
    }
  },

  // 更新系统状态
  updateSystemStatus: (info) => {
    if (info && info.system) {
      $("#system-status").text("系统运行正常");
      $("#system-uptime").text("运行中");
    }
  },

  // 启动自动刷新
  startAutoRefresh: () => {
    setInterval(() => {
      if (STATE.currentTab === "dashboard") {
        Dashboard.loadStats();
      }
    }, CONFIG.refreshInterval);
  },
};

// DOM 加载完成后初始化应用
$(document).ready(() => {
  App.init();
});

// 导出应用模块
window.App = App;
