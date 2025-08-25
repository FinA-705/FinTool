/**
 * 策略管理模块
 */

const StrategiesManager = {
  // 加载策略
  load: async () => {
    try {
      const response = await StrategyAPI.list();

      if (response.success && response.data) {
        STATE.strategiesData = response.data;
        StrategiesManager.renderList(response.data);
        StrategiesManager.updateSelects(response.data);

        console.log(`加载了 ${response.data.length} 个策略`);
      } else {
        console.log("策略获取响应:", response.message);
      }
    } catch (error) {
      console.error("加载策略失败:", error);
    }
  },

  // 渲染策略列表
  renderList: (strategies) => {
    const container = $("#strategies-list");

    if (!strategies || strategies.length === 0) {
      container.html('<div class="text-center text-muted">暂无策略</div>');
      return;
    }

    const html = strategies
      .map(
        (strategy) => `
        <div class="card strategy-card mb-3" data-strategy="${strategy.name}">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <div>
                <h6 class="card-title">${strategy.name}</h6>
                <p class="card-text text-muted">${strategy.description}</p>
                <div class="d-flex gap-2">
                  <span class="badge ${
                    strategy.status === "active" ? "bg-success" : "bg-secondary"
                  }">
                    ${strategy.status === "active" ? "活跃" : "非活跃"}
                  </span>
                  <span class="badge bg-info">最后运行: ${
                    strategy.last_run
                  }</span>
                </div>
              </div>
              <div class="btn-group">
                <button class="btn btn-sm btn-primary" onclick="StrategiesManager.edit('${
                  strategy.name
                }')">
                  <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-success" onclick="StrategiesManager.execute('${
                  strategy.name
                }')">
                  <i class="fas fa-play"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="StrategiesManager.delete('${
                  strategy.name
                }')">
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      `
      )
      .join("");

    container.html(html);
  },

  // 更新策略选择器
  updateSelects: (strategies) => {
    const selects = ["#execute-strategy-select", "#backtest-strategy"];

    selects.forEach((selector) => {
      const $select = $(selector);
      $select.find("option:not(:first)").remove();

      strategies.forEach((strategy) => {
        $select.append(
          `<option value="${strategy.name}">${strategy.name}</option>`
        );
      });
    });
  },

  // 处理策略提交
  handleSubmit: (e) => {
    e.preventDefault();

    const formData = {
      name: $("#strategy-name").val(),
      description: $("#strategy-description").val(),
      filters: $("#strategy-filters")
        .val()
        .split("\n")
        .filter((f) => f.trim()),
      score_formula: $("#strategy-score").val(),
    };

    // 模拟保存策略
    Utils.showToast(`策略 "${formData.name}" 保存成功`, "success");

    // 重置表单
    $("#strategy-form")[0].reset();

    // 重新加载策略列表
    StrategiesManager.load();
  },

  // 处理策略执行
  handleExecute: (e) => {
    e.preventDefault();

    const strategy = $("#execute-strategy-select").val();
    const topN = parseInt($("#execute-top-n").val());
    const includeScores = $("#include-scores").is(":checked");

    if (!strategy) {
      Utils.showToast("请选择策略", "warning");
      return;
    }

    StrategiesManager.executeWithParams(strategy, topN, includeScores);
  },

  // 执行策略
  executeWithParams: async (strategyName, topN = 20, includeScores = false) => {
    try {
      Utils.showToast("正在执行策略...", "info");

      // 调用策略执行API
      const response = await StrategyAPI.execute(strategyName, topN);

      if (response.success && response.data) {
        // 显示结果
        StrategiesManager.showResults(response.data);

        Utils.showToast(
          `策略执行完成，筛选出 ${response.data.selected_count} 只股票`,
          "success"
        );
      } else {
        throw new Error(response.message || "策略执行失败");
      }
    } catch (error) {
      console.error("执行策略失败:", error);
      Utils.showToast("执行策略失败: " + error.message, "error");

      // 如果API调用失败，显示错误信息而不是假数据
      StrategiesManager.showError("策略执行失败，请检查网络连接或联系管理员");
    }
  },

  // 显示策略结果
  showResults: (result) => {
    const card = $("#strategy-results-card");
    const container = $("#strategy-results");

    if (!result.data || result.data.length === 0) {
      container.html(
        '<div class="text-center text-muted">没有找到符合条件的股票</div>'
      );
      card.show();
      return;
    }

    const html = `
      <div class="mb-3">
        <h6>执行结果统计</h6>
        <div class="row">
          <div class="col-md-3">
            <div class="metric-card">
              <div class="metric-value">${
                result.selected_count || result.data.length
              }</div>
              <div class="metric-label">筛选股票</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="metric-card">
              <div class="metric-value">${result.total_stocks}</div>
              <div class="metric-label">总股票数</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="metric-card">
              <div class="metric-value">${result.execution_time}s</div>
              <div class="metric-label">执行时间</div>
            </div>
          </div>
          <div class="col-md-3">
            <div class="metric-card">
              <div class="metric-value">${
                result.selection_ratio ||
                ((result.data.length / result.total_stocks) * 100).toFixed(2)
              }%</div>
              <div class="metric-label">筛选比例</div>
            </div>
          </div>
        </div>
      </div>
      <div class="table-responsive">
        <table class="table table-striped">
          <thead class="table-dark">
            <tr>
              <th>排名</th>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>评分</th>
              <th>推荐理由</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            ${result.data
              .map(
                (item) => `
              <tr>
                <td><span class="badge bg-primary">${item.rank}</span></td>
                <td>${item.code}</td>
                <td>${item.name}</td>
                <td><strong>${item.score}</strong></td>
                <td><span class="tag success">${item.reason}</span></td>
                <td>
                  <button class="btn btn-sm btn-outline-primary" onclick="StocksManager.showDetail('${item.code}')">
                    查看详情
                  </button>
                </td>
              </tr>
            `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;

    container.html(html);
    card.show();

    // 滚动到结果区域
    card[0].scrollIntoView({ behavior: "smooth" });
  },

  // 显示错误信息
  showError: (errorMessage) => {
    const card = $("#strategy-results-card");
    const container = $("#strategy-results");

    const html = `
      <div class="alert alert-danger text-center">
        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
        <h6>策略执行失败</h6>
        <p class="mb-0">${errorMessage}</p>
      </div>
    `;

    container.html(html);
    card.show();

    // 滚动到结果区域
    card[0].scrollIntoView({ behavior: "smooth" });
  },

  // 编辑策略
  edit: (name) => {
    Utils.showToast(`编辑策略: ${name}`, "info");
  },

  // 执行策略
  execute: (name) => {
    StrategiesManager.executeWithParams(name, 20, true);
  },

  // 删除策略
  delete: (name) => {
    if (confirm(`确定要删除策略 "${name}" 吗？`)) {
      Utils.showToast(`策略 "${name}" 已删除`, "success");
      StrategiesManager.load();
    }
  },

  // 执行默认策略
  executeDefault: () => {
    StrategiesManager.executeWithParams("价值策略", 10, true);
  },
};

// 导出策略管理模块
window.StrategiesManager = StrategiesManager;
