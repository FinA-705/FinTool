/**
 * 仪表板功能模块
 */

const Dashboard = {
  // 加载仪表板
  load: async () => {
    try {
      await Dashboard.loadStats();
      await Dashboard.loadCharts();
    } catch (error) {
      console.error("加载仪表板失败:", error);
    }
  },

  // 加载统计数据
  loadStats: async () => {
    try {
      console.log("开始加载统计数据...");

      // 从API获取真实统计数据
      const response = await SystemAPI.getStats();
      console.log("API响应:", response);

      if (response.success && response.data) {
        const stats = response.data;

        console.log("更新前端显示:", stats);
        $("#strategy-count").text(stats.strategies || 0);
        $("#stock-count").text(stats.stocks || 0);
        $("#backtest-count").text(stats.backtests || 0);
        $("#system-uptime").text(stats.uptime || "未知");

        console.log("Dashboard stats loaded:", stats);
      } else {
        console.warn("API调用失败，使用默认值:", response);
        Dashboard.loadDefaultStats();
      }
    } catch (error) {
      console.error("Error loading dashboard stats:", error);
      // 出错时使用默认值
      Dashboard.loadDefaultStats();
    }
  },

  // 加载默认统计数据（备用）
  loadDefaultStats: () => {
    console.log("加载默认统计数据");
    const defaultStats = {
      strategies: 0,
      stocks: 0,
      backtests: 0,
      uptime: "未知",
    };

    $("#strategy-count").text(defaultStats.strategies);
    $("#stock-count").text(defaultStats.stocks);
    $("#backtest-count").text(defaultStats.backtests);
    $("#system-uptime").text(defaultStats.uptime);
  },

  // 加载图表
  loadCharts: async () => {
    // 策略分布饼图
    const strategyData = [
      {
        values: [40, 35, 25],
        labels: ["价值策略", "成长策略", "质量策略"],
        type: "pie",
        marker: {
          colors: CONFIG.chartColors,
        },
      },
    ];

    Plotly.newPlot(
      "strategy-chart",
      strategyData,
      {
        title: "策略分布",
        font: { family: "Arial, sans-serif" },
      },
      { responsive: true }
    );

    // 收益曲线图
    const dates = [];
    const returns = [];

    // 生成模拟数据
    const baseDate = new Date();
    baseDate.setMonth(baseDate.getMonth() - 12);

    for (let i = 0; i < 12; i++) {
      const date = new Date(baseDate);
      date.setMonth(date.getMonth() + i);
      dates.push(date.toISOString().split("T")[0]);
      returns.push(Math.random() * 0.2 - 0.1); // -10% 到 10%
    }

    const returnsData = [
      {
        x: dates,
        y: returns.map((r, i) =>
          returns.slice(0, i + 1).reduce((a, b) => a + b, 0)
        ),
        type: "scatter",
        mode: "lines+markers",
        name: "累计收益",
        line: { color: CONFIG.chartColors[0] },
      },
    ];

    Plotly.newPlot(
      "returns-chart",
      returnsData,
      {
        title: "过去一年收益曲线",
        xaxis: { title: "日期" },
        yaxis: { title: "累计收益率" },
        font: { family: "Arial, sans-serif" },
      },
      { responsive: true }
    );
  },

  // 快速操作
  quickActions: {
    fetchData: () => {
      if (window.StocksManager) {
        StocksManager.refresh();
      }
    },
    runBacktest: () => {
      if (window.BacktestManager) {
        BacktestManager.showCreateModal();
      }
    },
    exportReport: () => {
      if (window.Utils && Utils.showToast) {
        Utils.showToast("导出功能开发中...", "info");
      }
    },
  },
};

// 导出到全局作用域
window.Dashboard = Dashboard;
