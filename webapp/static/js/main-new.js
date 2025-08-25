/**
 * 财务智能体前端主文件 - 模块加载器
 * 负责加载所有功能模块
 */

// 模块加载顺序很重要：
// 1. 配置和工具函数
// 2. API 服务
// 3. 业务模块
// 4. 主应用控制器

(function () {
  "use strict";

  // 模块列表（按加载顺序）
  const modules = [
    "config.js", // 配置和常量
    "utils.js", // 工具函数
    "api.js", // API 服务
    "dashboard.js", // 仪表板模块
    "stocks.js", // 股票数据模块
    "strategies.js", // 策略管理模块
    "backtest.js", // 回测分析模块
    "config-manager.js", // 系统配置模块
    "app.js", // 主应用控制器
  ];

  // 动态加载模块
  function loadModule(modulePath) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `/static/js/modules/${modulePath}`;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  // 按顺序加载所有模块
  async function loadAllModules() {
    console.log("开始加载前端模块...");

    try {
      for (const module of modules) {
        console.log(`加载模块: ${module}`);
        await loadModule(module);
      }
      console.log("所有模块加载完成");
    } catch (error) {
      console.error("模块加载失败:", error);
      // 显示错误消息
      if (window.Utils) {
        Utils.showToast("模块加载失败，请刷新页面重试", "error");
      } else {
        alert("模块加载失败，请刷新页面重试");
      }
    }
  }

  // 页面加载完成后开始加载模块
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadAllModules);
  } else {
    loadAllModules();
  }
})();
