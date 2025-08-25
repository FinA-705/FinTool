/**
 * 回测分析模块
 */

const BacktestManager = {
  // 加载回测数据
  load: async () => {
    try {
      // 加载策略选择
      if (STATE.strategiesData.length === 0) {
        await StrategiesManager.load();
      }

      // 设置默认日期
      const endDate = new Date();
      const startDate = new Date();
      startDate.setFullYear(endDate.getFullYear() - 1);

      $("#backtest-start-date").val(startDate.toISOString().split("T")[0]);
      $("#backtest-end-date").val(endDate.toISOString().split("T")[0]);

      // 加载回测历史
      BacktestManager.loadHistory();
    } catch (error) {
      console.error("加载回测数据失败:", error);
    }
  },

  // 处理回测提交
  handleSubmit: (e) => {
    e.preventDefault();

    const formData = {
      strategy_name: $("#backtest-strategy").val(),
      start_date: $("#backtest-start-date").val(),
      end_date: $("#backtest-end-date").val(),
      initial_capital: parseFloat($("#backtest-capital").val()),
      commission_rate: parseFloat($("#backtest-commission").val()) / 100,
      rebalance_frequency: $("#backtest-rebalance").val(),
    };

    if (!formData.strategy_name) {
      Utils.showToast("请选择策略", "warning");
      return;
    }

    if (new Date(formData.start_date) >= new Date(formData.end_date)) {
      Utils.showToast("开始日期必须早于结束日期", "warning");
      return;
    }

    BacktestManager.run(formData);
  },

  // 运行回测
  run: async (config) => {
    try {
      // 显示进度
      $("#backtest-empty").hide();
      $("#backtest-results").hide();
      $("#backtest-progress").show();

      Utils.showToast("正在执行回测...", "info");

      const response = await BacktestAPI.run(config);

      if (response.success && response.data) {
        // 显示结果
        BacktestManager.showResults(response.data);

        Utils.showToast("回测完成", "success");
      } else {
        throw new Error(response.message || "回测执行失败");
      }
    } catch (error) {
      console.error("回测执行失败:", error);
      Utils.showToast("回测执行失败: " + error.message, "error");

      $("#backtest-progress").hide();
      $("#backtest-empty").show();
    }
  },

  // 显示回测结果
  showResults: (result) => {
    $("#backtest-progress").hide();

    const metrics = result.performance_metrics;
    const profit = result.final_value - result.initial_capital;

    const html = `
      <div class="row mb-4">
        <div class="col-md-12">
          <h6>回测概览</h6>
          <div class="row">
            <div class="col-md-3">
              <div class="metric-card bg-primary text-white">
                <div class="metric-value">${Utils.formatPercent(
                  metrics.total_return
                )}</div>
                <div class="metric-label">总收益率</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="metric-card bg-success text-white">
                <div class="metric-value">${Utils.formatCurrency(profit)}</div>
                <div class="metric-label">绝对收益</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="metric-card bg-warning text-white">
                <div class="metric-value">${Utils.formatPercent(
                  metrics.max_drawdown
                )}</div>
                <div class="metric-label">最大回撤</div>
              </div>
            </div>
            <div class="col-md-3">
              <div class="metric-card bg-info text-white">
                <div class="metric-value">${Utils.formatNumber(
                  metrics.sharpe_ratio,
                  2
                )}</div>
                <div class="metric-label">夏普比率</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-6">
          <h6>详细指标</h6>
          <table class="table table-sm">
            <tr><td>策略名称</td><td>${result.strategy_name}</td></tr>
            <tr><td>回测期间</td><td>${result.period}</td></tr>
            <tr><td>初始资金</td><td>${Utils.formatCurrency(
              result.initial_capital
            )}</td></tr>
            <tr><td>最终价值</td><td>${Utils.formatCurrency(
              result.final_value
            )}</td></tr>
            <tr><td>年化收益</td><td>${Utils.formatPercent(
              metrics.annual_return
            )}</td></tr>
            <tr><td>波动率</td><td>${Utils.formatPercent(
              metrics.volatility
            )}</td></tr>
            <tr><td>胜率</td><td>${Utils.formatPercent(
              metrics.win_rate
            )}</td></tr>
            <tr><td>盈亏比</td><td>${Utils.formatNumber(
              metrics.profit_factor,
              2
            )}</td></tr>
            <tr><td>交易次数</td><td>${result.trades_count}</td></tr>
            <tr><td>执行时间</td><td>${Utils.formatNumber(
              result.execution_time,
              1
            )}秒</td></tr>
          </table>
        </div>
        <div class="col-md-6">
          <h6>收益曲线</h6>
          <div id="backtest-chart" style="height: 300px;"></div>
        </div>
      </div>
    `;

    $("#backtest-results").html(html).show();

    // 绘制收益曲线图
    BacktestManager.drawChart(result);
  },

  // 绘制回测图表
  drawChart: (result) => {
    // 生成模拟数据点
    const dates = [];
    const values = [];
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);

    for (let i = 0; i <= 365; i += 7) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      dates.push(date.toISOString().split("T")[0]);

      const progress = i / 365;
      const randomWalk = (Math.random() - 0.5) * 0.02;
      const trendValue =
        result.initial_capital *
        (1 + result.performance_metrics.total_return * progress + randomWalk);
      values.push(trendValue);
    }

    const chartData = [
      {
        x: dates,
        y: values,
        type: "scatter",
        mode: "lines",
        name: "投资组合价值",
        line: { color: CONFIG.chartColors[0] },
      },
    ];

    Plotly.newPlot(
      "backtest-chart",
      chartData,
      {
        title: "回测收益曲线",
        xaxis: { title: "日期" },
        yaxis: { title: "投资组合价值" },
        font: { family: "Arial, sans-serif" },
      },
      { responsive: true }
    );
  },

  // 加载回测历史
  loadHistory: () => {
    const historyHtml = `
      <div class="text-center text-muted">
        <i class="fas fa-history fa-2x mb-3"></i>
        <p>暂无回测历史记录</p>
      </div>
    `;
    $("#backtest-history").html(historyHtml);
  },

  // 快速回测
  runQuick: () => {
    const quickConfig = {
      strategy_name: "价值策略",
      start_date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
      end_date: new Date().toISOString().split("T")[0],
      initial_capital: 1000000,
      commission_rate: 0.0008,
      rebalance_frequency: "monthly",
    };

    BacktestManager.run(quickConfig);
  },
};

// 导出回测管理模块
window.BacktestManager = BacktestManager;
