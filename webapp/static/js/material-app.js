/**
 * Material Design Financial Agent App
 * 精简版前端应用 - 采用Material Design 3
 */

class FinancialApp {
  constructor() {
    this.currentView = "dashboard";
    this.isDrawerOpen = false;
    this.cache = new Map();
    this.isLoading = false;

    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setupNavigation();
    this.loadInitialData();
    console.log("🚀 Financial Agent App initialized with Material Design");
  }

  setupEventListeners() {
    // Menu toggle
    document.getElementById("menu-toggle")?.addEventListener("click", () => {
      this.toggleDrawer();
    });

    // Navigation items
    document.querySelectorAll(".md-list-item[data-view]").forEach((item) => {
      item.addEventListener("click", (e) => {
        const view = e.currentTarget.dataset.view;
        this.switchView(view);
      });
    });

    // Action buttons
    document.getElementById("refresh-btn")?.addEventListener("click", () => {
      this.refreshData();
    });

    document
      .getElementById("refresh-stocks-btn")
      ?.addEventListener("click", () => {
        this.refreshStocksData();
      });

    document
      .getElementById("toggle-filter-btn")
      ?.addEventListener("click", () => {
        this.toggleFilterCard();
      });

    document
      .getElementById("apply-filter-btn")
      ?.addEventListener("click", () => {
        this.applyFilters();
      });

    document
      .getElementById("clear-filter-btn")
      ?.addEventListener("click", () => {
        this.clearFilters();
      });

    document.getElementById("export-btn")?.addEventListener("click", () => {
      this.exportStocksData();
    });

    document.getElementById("view-mode-btn")?.addEventListener("click", () => {
      this.toggleViewMode();
    });

    document.getElementById("main-fab")?.addEventListener("click", () => {
      this.handleFabClick();
    });

    // Strategy management events
    document
      .getElementById("create-strategy-btn")
      ?.addEventListener("click", () => {
        this.openStrategyModal();
      });

    document
      .getElementById("import-strategy-btn")
      ?.addEventListener("click", () => {
        this.importStrategy();
      });

    document
      .getElementById("close-strategy-modal")
      ?.addEventListener("click", () => {
        this.closeStrategyModal();
      });

    document
      .getElementById("cancel-strategy-btn")
      ?.addEventListener("click", () => {
        this.closeStrategyModal();
      });

    document
      .getElementById("test-strategy-btn")
      ?.addEventListener("click", () => {
        this.testStrategy();
      });

    document
      .getElementById("save-strategy-btn")
      ?.addEventListener("click", () => {
        this.saveStrategy();
      });

    // Strategy filters
    document
      .getElementById("strategy-search")
      ?.addEventListener("input", (e) => {
        this.debounce(() => this.filterStrategies(), 300)();
      });

    document
      .getElementById("strategy-type-filter")
      ?.addEventListener("change", () => {
        this.filterStrategies();
      });

    document
      .getElementById("strategy-status-filter")
      ?.addEventListener("change", () => {
        this.filterStrategies();
      });

    // Weight sliders
    document
      .querySelectorAll('.md-weight-item input[type="range"]')
      .forEach((slider) => {
        slider.addEventListener("input", (e) => {
          this.updateWeightDisplay(e.target);
        });
      });

    // Search functionality
    document.getElementById("search-input")?.addEventListener("input", (e) => {
      this.debounce(() => this.searchStocks(e.target.value), 300)();
    });

    // Market filter
    document
      .getElementById("market-select")
      ?.addEventListener("change", (e) => {
        this.filterByMarket(e.target.value);
      });

    // Close snackbar
    document
      .querySelector(".md-snackbar__action")
      ?.addEventListener("click", () => {
        this.hideSnackbar();
      });

    // Close drawer when clicking outside (mobile)
    document.addEventListener("click", (e) => {
      if (
        this.isDrawerOpen &&
        !e.target.closest(".md-navigation-drawer") &&
        !e.target.closest(".md-app-bar__nav-icon")
      ) {
        this.closeDrawer();
      }
    });
  }

  setupNavigation() {
    // Update main content margin based on screen size
    this.updateLayout();
    window.addEventListener("resize", () => this.updateLayout());
  }

  updateLayout() {
    const mainContent = document.querySelector(".md-main-content");
    if (window.innerWidth > 768) {
      this.openDrawer();
    } else {
      this.closeDrawer();
    }
  }

  toggleDrawer() {
    if (this.isDrawerOpen) {
      this.closeDrawer();
    } else {
      this.openDrawer();
    }
  }

  openDrawer() {
    const drawer = document.querySelector(".md-navigation-drawer");
    const mainContent = document.querySelector(".md-main-content");

    drawer?.classList.add("md-navigation-drawer--open");
    if (window.innerWidth > 768) {
      mainContent?.classList.add("md-main-content--drawer-open");
    }
    this.isDrawerOpen = true;
  }

  closeDrawer() {
    const drawer = document.querySelector(".md-navigation-drawer");
    const mainContent = document.querySelector(".md-main-content");

    drawer?.classList.remove("md-navigation-drawer--open");
    mainContent?.classList.remove("md-main-content--drawer-open");
    this.isDrawerOpen = false;
  }

  switchView(viewName) {
    // Hide current view
    document.querySelectorAll(".md-view").forEach((view) => {
      view.classList.remove("md-view--active");
    });

    // Show new view
    const newView = document.getElementById(`${viewName}-view`);
    if (newView) {
      newView.classList.add("md-view--active");
      this.currentView = viewName;

      // Update navigation state
      document.querySelectorAll(".md-list-item").forEach((item) => {
        item.classList.remove("md-list-item--active");
      });
      document
        .querySelector(`.md-list-item[data-view="${viewName}"]`)
        ?.classList.add("md-list-item--active");

      // Load view-specific data
      this.loadViewData(viewName);

      // Close drawer on mobile
      if (window.innerWidth <= 768) {
        this.closeDrawer();
      }
    }
  }

  async loadViewData(viewName) {
    switch (viewName) {
      case "dashboard":
        await this.loadDashboardData();
        break;
      case "stocks":
        await this.loadStocksData();
        break;
      case "strategies":
        await this.loadStrategiesData();
        break;
      case "backtest":
        await this.loadBacktestData();
        break;
    }
  }

  async loadInitialData() {
    this.showLoading("正在初始化应用...");

    try {
      await Promise.all([this.loadSystemStats(), this.loadTrendingStocks()]);
      this.showSnackbar("应用初始化完成", "success");
    } catch (error) {
      console.error("Failed to load initial data:", error);
      this.showSnackbar("初始化失败，请稍后重试", "error");
    } finally {
      this.hideLoading();
    }
  }

  async loadSystemStats() {
    try {
      const response = await this.apiCall("/api/v1/stats");
      if (response.success) {
        this.updateStats(response.data);
      }
    } catch (error) {
      console.error("Failed to load system stats:", error);
    }
  }

  async loadTrendingStocks() {
    try {
      const response = await this.apiCall("/api/v1/stocks/trending?limit=5");
      if (response.success) {
        this.updateTrendingStocks(response.data);
      }
    } catch (error) {
      console.error("Failed to load trending stocks:", error);
    }
  }

  async loadDashboardData() {
    this.showLoading("正在加载仪表板数据...");

    try {
      await Promise.all([
        this.loadSystemStats(),
        this.loadTrendingStocks(),
        this.loadMarketChart(),
      ]);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
      this.showSnackbar("加载仪表板数据失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async loadStocksData() {
    this.showLoading("正在加载股票数据...");

    try {
      const market =
        document.getElementById("market-select")?.value || "a_stock";
      const response = await this.apiCall(
        `/api/v1/stocks/data?market=${market}&limit=100`
      );

      if (response.success) {
        this.updateStocksTable(response.data);
      }
    } catch (error) {
      console.error("Failed to load stocks data:", error);
      this.showSnackbar("加载股票数据失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async loadStrategiesData() {
    this.showLoading("正在加载策略数据...");

    try {
      const response = await this.apiCall("/api/v1/strategies");
      if (response.success) {
        this.updateStrategiesGrid(response.data);
      }
    } catch (error) {
      console.error("Failed to load strategies data:", error);
      this.showSnackbar("加载策略数据失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async loadBacktestData() {
    this.showLoading("正在加载回测数据...");

    try {
      const response = await this.apiCall("/api/v1/backtest/tasks");
      if (response.success) {
        this.updateBacktestData(response.data);
      }
    } catch (error) {
      console.error("Failed to load backtest data:", error);
      this.showSnackbar("加载回测数据失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async screenStocks() {
    this.showLoading("正在执行智能筛选...");

    try {
      const strategy =
        document.getElementById("strategy-select")?.value || "schloss";
      const response = await this.apiCall("/api/v1/stocks/screen", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          strategy: strategy,
          top_n: 20,
        }),
      });

      if (response.success) {
        this.updateStocksTable(response.data);
        this.showSnackbar(
          `成功筛选出 ${response.data.length} 只股票`,
          "success"
        );
      }
    } catch (error) {
      console.error("Failed to screen stocks:", error);
      this.showSnackbar("股票筛选失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async searchStocks(query) {
    if (!query || query.length < 2) {
      await this.loadStocksData();
      return;
    }

    try {
      const response = await this.apiCall(
        `/api/v1/stocks/search?q=${encodeURIComponent(query)}&limit=50`
      );
      if (response.success) {
        this.updateStocksTable(response.data);
      }
    } catch (error) {
      console.error("Failed to search stocks:", error);
    }
  }

  async filterByMarket(market) {
    this.showLoading("正在切换市场...");

    try {
      const response = await this.apiCall(
        `/api/v1/stocks/data?market=${market}&limit=100`
      );
      if (response.success) {
        this.updateStocksTable(response.data);
        this.showSnackbar(`已切换到${this.getMarketName(market)}`, "success");
      }
    } catch (error) {
      console.error("Failed to filter by market:", error);
      this.showSnackbar("切换市场失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async refreshData() {
    this.showLoading("正在刷新数据...");

    try {
      // Clear cache
      this.cache.clear();

      // Reload current view data
      await this.loadViewData(this.currentView);
      this.showSnackbar("数据刷新完成", "success");
    } catch (error) {
      console.error("Failed to refresh data:", error);
      this.showSnackbar("数据刷新失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  handleFabClick() {
    switch (this.currentView) {
      case "dashboard":
        this.refreshData();
        break;
      case "stocks":
        this.screenStocks();
        break;
      case "strategies":
        this.showSnackbar("创建策略功能即将推出", "info");
        break;
      case "backtest":
        this.showSnackbar("运行回测功能即将推出", "info");
        break;
    }
  }

  updateStats(stats) {
    document.getElementById("strategy-count").textContent =
      stats.strategies || 0;
    document.getElementById("stock-count").textContent = stats.stocks || 0;
    document.getElementById("backtest-count").textContent =
      stats.backtest_tasks || 0;
    document.getElementById("system-status").textContent =
      stats.system_status || "正常";
  }

  updateTrendingStocks(stocks) {
    const container = document.getElementById("trending-stocks");
    if (!container) return;

    container.innerHTML = stocks
      .map(
        (stock) => `
            <div class="md-stock-item">
                <div class="md-stock-item__info">
                    <div class="md-stock-item__code">${stock.code}</div>
                    <div class="md-stock-item__name">${stock.name}</div>
                </div>
                <div class="md-stock-item__value">
                    ${
                      stock.market_value
                        ? this.formatNumber(stock.market_value / 100000000) +
                          "亿"
                        : "-"
                    }
                </div>
            </div>
        `
      )
      .join("");
  }

  renderStocksTable(stocks) {
    const tbody = document.querySelector("#stocks-table tbody");
    if (!tbody) return;

    tbody.innerHTML = stocks
      .map(
        (stock, index) => `
            <tr>
                <td>${stock.rank || index + 1}</td>
                <td class="stock-code">${
                  stock.code || stock.ts_code?.split(".")[0] || "-"
                }</td>
                <td class="stock-name">${stock.name || "-"}</td>
                <td class="stock-price">${
                  stock.close ? "¥" + stock.close.toFixed(2) : "-"
                }</td>
                <td class="stock-change ${this.getChangeClass(stock.pct_chg)}">
                    ${
                      stock.pct_chg
                        ? (stock.pct_chg > 0 ? "+" : "") +
                          stock.pct_chg.toFixed(2) +
                          "%"
                        : "-"
                    }
                </td>
                <td class="stock-market-cap">
                    ${
                      stock.market_value
                        ? this.formatNumber(stock.market_value / 100000000) +
                          "亿"
                        : "-"
                    }
                </td>
                <td class="stock-score">
                    ${stock.score ? this.renderScoreBadge(stock.score) : "-"}
                </td>
                <td class="stock-actions">
                    <button class="md-icon-button" onclick="app.viewStockDetail('${
                      stock.code || stock.ts_code
                    }')" title="查看详情">
                        <span class="material-icons">visibility</span>
                    </button>
                    <button class="md-icon-button" onclick="app.addToWatchlist('${
                      stock.code || stock.ts_code
                    }')" title="加入关注">
                        <span class="material-icons">star_border</span>
                    </button>
                </td>
            </tr>
        `
      )
      .join("");

    // 更新摘要信息
    this.updateStocksSummary(stocks.length, stocks.length);
  }

  getChangeClass(pctChg) {
    if (!pctChg) return "";
    return pctChg > 0 ? "positive" : pctChg < 0 ? "negative" : "";
  }

  renderScoreBadge(score) {
    const level = score >= 80 ? "high" : score >= 60 ? "medium" : "low";
    const color = score >= 80 ? "success" : score >= 60 ? "warning" : "error";

    return `<span class="score-badge score-badge--${level}" style="color: var(--md-sys-color-${color})">${score.toFixed(
      1
    )}</span>`;
  }

  // 兼容旧方法名
  updateStocksTable(stocks) {
    this.renderStocksTable(stocks);
  }

  updateStrategiesGrid(strategies) {
    const container = document.getElementById("strategies-container");
    if (!container) return;

    container.innerHTML = strategies
      .map(
        (strategy) => `
            <div class="md-card md-strategy-card">
                <div class="md-card__content">
                    <div class="md-strategy-card__status md-strategy-card__status--${
                      strategy.status === "active" ? "active" : "inactive"
                    }">
                        ${strategy.status === "active" ? "激活" : "未激活"}
                    </div>
                    <h3 class="md-card__title">${strategy.name}</h3>
                    <p>${strategy.description}</p>
                    <div class="md-card__actions">
                        <button class="md-button md-button--text" onclick="app.executeStrategy('${
                          strategy.name
                        }')">
                            执行策略
                        </button>
                    </div>
                </div>
            </div>
        `
      )
      .join("");
  }

  updateBacktestData(tasks) {
    // Implementation for backtest data update
    console.log("Backtest data:", tasks);
  }

  async loadMarketChart() {
    // Simple market overview chart using Chart.js
    const ctx = document.getElementById("market-chart");
    if (!ctx) return;

    try {
      const response = await this.apiCall("/api/v1/stocks/market/summary");
      if (response.success && response.data) {
        this.renderMarketChart(ctx, response.data);
      }
    } catch (error) {
      console.error("Failed to load market chart:", error);
    }
  }

  renderMarketChart(ctx, data) {
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: Object.keys(data.top_industries || {}),
        datasets: [
          {
            data: Object.values(data.top_industries || {}),
            backgroundColor: [
              "#6750a4",
              "#625b71",
              "#7d5260",
              "#006e1c",
              "#8b5000",
              "#ba1a1a",
              "#005ac1",
              "#8e4ec6",
              "#c4a147",
              "#4285f4",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "行业分布",
          },
        },
      },
    });
  }

  async viewStockDetail(stockCode) {
    this.showLoading("正在加载股票详情...");

    try {
      const response = await this.apiCall(`/api/v1/stocks/info/${stockCode}`);
      if (response.success) {
        this.showSnackbar(`${response.data.name} 详情加载完成`, "success");
        // TODO: Show detailed stock information in a dialog
      }
    } catch (error) {
      console.error("Failed to load stock detail:", error);
      this.showSnackbar("加载股票详情失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async executeStrategy(strategyName) {
    this.showLoading(`正在执行 ${strategyName} 策略...`);

    try {
      const response = await this.apiCall(
        `/api/v1/strategies/${strategyName}/execute`,
        {
          method: "POST",
        }
      );

      if (response.success) {
        this.showSnackbar(`${strategyName} 策略执行完成`, "success");
        // Switch to stocks view to show results
        this.switchView("stocks");
        this.updateStocksTable(response.data);
      }
    } catch (error) {
      console.error("Failed to execute strategy:", error);
      this.showSnackbar("策略执行失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async apiCall(url, options = {}) {
    const cacheKey = `${url}_${JSON.stringify(options)}`;

    // Check cache for GET requests
    if (!options.method || options.method === "GET") {
      if (this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (Date.now() - cached.timestamp < 300000) {
          // 5 minutes cache
          return cached.data;
        }
      }
    }

    try {
      const response = await fetch(url, options);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Cache successful GET responses
      if (!options.method || options.method === "GET") {
        this.cache.set(cacheKey, {
          data: data,
          timestamp: Date.now(),
        });
      }

      return data;
    } catch (error) {
      console.error("API call failed:", error);
      throw error;
    }
  }

  showLoading(message = "正在加载...") {
    if (this.isLoading) return;

    this.isLoading = true;
    const overlay = document.getElementById("loading-overlay");
    const text = document.querySelector(".md-loading-text");

    if (text) text.textContent = message;
    if (overlay) overlay.classList.add("md-loading-overlay--show");
  }

  hideLoading() {
    this.isLoading = false;
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.classList.remove("md-loading-overlay--show");
  }

  showSnackbar(message, type = "info") {
    const snackbar = document.getElementById("snackbar");
    const messageEl = document.querySelector(".md-snackbar__message");

    if (messageEl) messageEl.textContent = message;
    if (snackbar) {
      snackbar.classList.add("md-snackbar--show");

      // Auto hide after 4 seconds
      setTimeout(() => {
        this.hideSnackbar();
      }, 4000);
    }
  }

  hideSnackbar() {
    const snackbar = document.getElementById("snackbar");
    if (snackbar) snackbar.classList.remove("md-snackbar--show");
  }

  getMarketName(market) {
    const marketNames = {
      a_stock: "A股市场",
      us: "美股市场",
      hk: "港股市场",
    };
    return marketNames[market] || market;
  }

  formatNumber(num) {
    if (num >= 1000000000) {
      return (num / 1000000000).toFixed(1) + "B";
    } else if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toFixed(2);
  }

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ===== 新的筛选相关方法 =====

  toggleFilterCard() {
    const filterCard = document.getElementById("filter-card");
    const toggleBtn = document.getElementById("toggle-filter-btn");

    if (filterCard.style.display === "none") {
      filterCard.style.display = "block";
      toggleBtn.innerHTML =
        '<span class="material-icons">filter_list_off</span>隐藏筛选';
    } else {
      filterCard.style.display = "none";
      toggleBtn.innerHTML =
        '<span class="material-icons">filter_list</span>筛选设置';
    }
  }

  async refreshStocksData() {
    this.showLoading("正在刷新股票数据...");
    try {
      await this.loadStocksData();
      this.showSnackbar("股票数据已更新", "success");
    } catch (error) {
      console.error("Failed to refresh stocks data:", error);
      this.showSnackbar("刷新失败，请稍后重试", "error");
    } finally {
      this.hideLoading();
    }
  }

  applyFilters() {
    const searchText = document.getElementById("search-input")?.value || "";
    const market = document.getElementById("market-select")?.value || "";
    const strategy = document.getElementById("strategy-select")?.value || "";
    const sortBy = document.getElementById("sort-select")?.value || "code";

    this.showLoading("正在应用筛选条件...");

    // 构建筛选参数
    const filters = {
      search: searchText,
      market: market,
      strategy: strategy,
      sort: sortBy,
    };

    this.filterStocks(filters);
  }

  clearFilters() {
    // 清除所有筛选表单
    document.getElementById("search-input").value = "";
    document.getElementById("market-select").value = "";
    document.getElementById("strategy-select").value = "";
    document.getElementById("sort-select").value = "code";

    // 重新加载所有股票数据
    this.loadStocksData();
    this.showSnackbar("筛选条件已清除", "info");
  }

  async filterStocks(filters) {
    try {
      // 构建API查询参数
      const params = new URLSearchParams();
      if (filters.search) params.append("search", filters.search);
      if (filters.market) params.append("market", filters.market);
      if (filters.strategy) params.append("strategy", filters.strategy);
      if (filters.sort) params.append("sort", filters.sort);

      const response = await this.apiCall(
        `/api/v1/stocks/filter?${params.toString()}`
      );

      if (response.success && response.data) {
        this.renderStocksTable(response.data);
        this.updateStocksSummary(
          response.data.length,
          response.total || response.data.length
        );
        this.showSnackbar(`找到 ${response.data.length} 只股票`, "success");
      }
    } catch (error) {
      console.error("Filter failed:", error);
      this.showSnackbar("筛选失败，请稍后重试", "error");
    } finally {
      this.hideLoading();
    }
  }

  updateStocksSummary(filtered, total) {
    const totalEl = document.getElementById("total-stocks");
    const filteredEl = document.getElementById("filtered-stocks");

    if (totalEl) totalEl.textContent = total;
    if (filteredEl) filteredEl.textContent = filtered;
  }

  exportStocksData() {
    const table = document.getElementById("stocks-table");
    if (!table) return;

    // 简单的CSV导出功能
    let csv = "";
    const rows = table.querySelectorAll("tr");

    rows.forEach((row) => {
      const cols = row.querySelectorAll("th, td");
      const csvRow = Array.from(cols)
        .map((col) => `"${col.textContent.trim()}"`)
        .join(",");
      csv += csvRow + "\n";
    });

    // 创建下载链接
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `stocks_data_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();

    this.showSnackbar("数据已导出", "success");
  }

  toggleViewMode() {
    const table = document.querySelector(".md-data-table");
    const viewBtn = document.getElementById("view-mode-btn");

    if (table.classList.contains("compact-view")) {
      table.classList.remove("compact-view");
      viewBtn.innerHTML = '<span class="material-icons">view_compact</span>';
    } else {
      table.classList.add("compact-view");
      viewBtn.innerHTML = '<span class="material-icons">view_module</span>';
    }
  }

  // ===== 股票详情和收藏功能 =====

  async viewStockDetail(stockCode) {
    this.showLoading("正在加载股票详情...");
    try {
      const response = await this.apiCall(`/api/v1/stocks/${stockCode}/detail`);
      if (response.success) {
        this.showStockDetailModal(response.data);
      }
    } catch (error) {
      console.error("Failed to load stock detail:", error);
      this.showSnackbar("加载股票详情失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async addToWatchlist(stockCode) {
    try {
      const response = await this.apiCall(`/api/v1/watchlist`, {
        method: "POST",
        body: JSON.stringify({ stock_code: stockCode }),
      });

      if (response.success) {
        this.showSnackbar("已加入关注列表", "success");
        // 更新图标状态 - 需要通过事件来获取按钮
        this.updateWatchlistButton(stockCode, true);
      }
    } catch (error) {
      console.error("Failed to add to watchlist:", error);
      this.showSnackbar("加入关注列表失败", "error");
    }
  }

  async removeFromWatchlist(stockCode) {
    try {
      const response = await this.apiCall(`/api/v1/watchlist/${stockCode}`, {
        method: "DELETE",
      });

      if (response.success) {
        this.showSnackbar("已取消关注", "info");
        this.updateWatchlistButton(stockCode, false);
      }
    } catch (error) {
      console.error("Failed to remove from watchlist:", error);
      this.showSnackbar("取消关注失败", "error");
    }
  }

  updateWatchlistButton(stockCode, isWatched) {
    const buttons = document.querySelectorAll(
      `button[onclick*="${stockCode}"]`
    );
    buttons.forEach((btn) => {
      if (btn.getAttribute("onclick").includes("Watchlist")) {
        if (isWatched) {
          btn.innerHTML = '<span class="material-icons">star</span>';
          btn.title = "取消关注";
          btn.setAttribute(
            "onclick",
            `app.removeFromWatchlist('${stockCode}')`
          );
        } else {
          btn.innerHTML = '<span class="material-icons">star_border</span>';
          btn.title = "加入关注";
          btn.setAttribute("onclick", `app.addToWatchlist('${stockCode}')`);
        }
      }
    });
  }

  showStockDetailModal(stockData) {
    // 创建模态框显示股票详情
    // 这里可以后续实现完整的股票详情弹窗
    console.log("Stock detail:", stockData);
    this.showSnackbar(
      `${stockData.name || stockData.ts_code} 详情加载完成`,
      "info"
    );
  }

  // ===== 策略管理方法 =====

  openStrategyModal(strategyData = null) {
    const modal = document.getElementById("strategy-modal");
    const title = document.getElementById("strategy-modal-title");

    if (strategyData) {
      title.textContent = "编辑投资策略";
      this.populateStrategyForm(strategyData);
    } else {
      title.textContent = "创建投资策略";
      this.resetStrategyForm();
    }

    modal.classList.remove("hidden");
    modal.style.display = "flex";
  }

  closeStrategyModal() {
    const modal = document.getElementById("strategy-modal");
    modal.classList.add("hidden");
    modal.style.display = "none";
    this.resetStrategyForm();
  }

  resetStrategyForm() {
    const form = document.getElementById("strategy-form");
    form.reset();

    // 重置权重滑块显示
    document
      .querySelectorAll('.md-weight-item input[type="range"]')
      .forEach((slider) => {
        this.updateWeightDisplay(slider);
      });
  }

  populateStrategyForm(strategyData) {
    // 填充表单数据
    document.getElementById("strategy-name").value = strategyData.name || "";
    document.getElementById("strategy-description").value =
      strategyData.description || "";
    document.getElementById("strategy-type").value = strategyData.type || "";

    // 填充筛选条件
    if (strategyData.conditions) {
      const conditions = strategyData.conditions;
      document.getElementById("pe-ratio-min").value =
        conditions.pe_ratio_min || "";
      document.getElementById("pe-ratio-max").value =
        conditions.pe_ratio_max || "";
      document.getElementById("pb-ratio-min").value =
        conditions.pb_ratio_min || "";
      document.getElementById("pb-ratio-max").value =
        conditions.pb_ratio_max || "";
      document.getElementById("roe-min").value = conditions.roe_min || "";
      document.getElementById("debt-ratio-max").value =
        conditions.debt_ratio_max || "";
      document.getElementById("market-cap-min").value =
        conditions.market_cap_min || "";
      document.getElementById("market-cap-max").value =
        conditions.market_cap_max || "";
    }

    // 填充权重
    if (strategyData.weights) {
      const weights = strategyData.weights;
      document.getElementById("financial-weight").value =
        weights.financial || 40;
      document.getElementById("growth-weight").value = weights.growth || 30;
      document.getElementById("valuation-weight").value =
        weights.valuation || 20;
      document.getElementById("risk-weight").value = weights.risk || 10;

      // 更新显示
      document
        .querySelectorAll('.md-weight-item input[type="range"]')
        .forEach((slider) => {
          this.updateWeightDisplay(slider);
        });
    }
  }

  updateWeightDisplay(slider) {
    const value = slider.value;
    const valueDisplay = slider.parentElement.querySelector(".weight-value");
    if (valueDisplay) {
      valueDisplay.textContent = value + "%";
    }
  }

  async saveStrategy() {
    const form = document.getElementById("strategy-form");
    const formData = new FormData(form);

    // 收集表单数据
    const strategyData = {
      name: document.getElementById("strategy-name").value,
      description: document.getElementById("strategy-description").value,
      type: document.getElementById("strategy-type").value,
      conditions: {
        pe_ratio_min:
          parseFloat(document.getElementById("pe-ratio-min").value) || null,
        pe_ratio_max:
          parseFloat(document.getElementById("pe-ratio-max").value) || null,
        pb_ratio_min:
          parseFloat(document.getElementById("pb-ratio-min").value) || null,
        pb_ratio_max:
          parseFloat(document.getElementById("pb-ratio-max").value) || null,
        roe_min: parseFloat(document.getElementById("roe-min").value) || null,
        debt_ratio_max:
          parseFloat(document.getElementById("debt-ratio-max").value) || null,
        market_cap_min:
          parseFloat(document.getElementById("market-cap-min").value) || null,
        market_cap_max:
          parseFloat(document.getElementById("market-cap-max").value) || null,
        included_industries: document
          .getElementById("included-industries")
          .value.split(",")
          .map((s) => s.trim())
          .filter((s) => s),
        excluded_industries: document
          .getElementById("excluded-industries")
          .value.split(",")
          .map((s) => s.trim())
          .filter((s) => s),
        allowed_markets: Array.from(
          document.getElementById("allowed-markets").selectedOptions
        ).map((option) => option.value),
      },
      weights: {
        financial: parseInt(document.getElementById("financial-weight").value),
        growth: parseInt(document.getElementById("growth-weight").value),
        valuation: parseInt(document.getElementById("valuation-weight").value),
        risk: parseInt(document.getElementById("risk-weight").value),
      },
    };

    // 验证权重总和
    const totalWeight = Object.values(strategyData.weights).reduce(
      (sum, weight) => sum + weight,
      0
    );
    if (totalWeight !== 100) {
      this.showSnackbar("权重总和必须为100%", "error");
      return;
    }

    this.showLoading("正在保存策略...");

    try {
      const response = await this.apiCall("/api/v1/strategies", {
        method: "POST",
        body: JSON.stringify(strategyData),
      });

      if (response.success) {
        this.showSnackbar("策略保存成功", "success");
        this.closeStrategyModal();
        await this.loadStrategiesData(); // 重新加载策略列表

        // 更新股票筛选中的策略选项
        this.updateStrategySelect();
      }
    } catch (error) {
      console.error("Failed to save strategy:", error);
      this.showSnackbar("策略保存失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async testStrategy() {
    const strategyData = this.collectStrategyFormData();

    this.showLoading("正在测试策略...");

    try {
      const response = await this.apiCall("/api/v1/strategies/test", {
        method: "POST",
        body: JSON.stringify(strategyData),
      });

      if (response.success) {
        const results = response.data;
        this.showSnackbar(
          `策略测试完成：找到 ${results.total_stocks} 只符合条件的股票`,
          "success"
        );

        // 可以显示测试结果的详细信息
        console.log("Strategy test results:", results);
      }
    } catch (error) {
      console.error("Failed to test strategy:", error);
      this.showSnackbar("策略测试失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  collectStrategyFormData() {
    return {
      name: document.getElementById("strategy-name").value,
      description: document.getElementById("strategy-description").value,
      type: document.getElementById("strategy-type").value,
      conditions: {
        pe_ratio_min:
          parseFloat(document.getElementById("pe-ratio-min").value) || null,
        pe_ratio_max:
          parseFloat(document.getElementById("pe-ratio-max").value) || null,
        pb_ratio_min:
          parseFloat(document.getElementById("pb-ratio-min").value) || null,
        pb_ratio_max:
          parseFloat(document.getElementById("pb-ratio-max").value) || null,
        roe_min: parseFloat(document.getElementById("roe-min").value) || null,
        debt_ratio_max:
          parseFloat(document.getElementById("debt-ratio-max").value) || null,
        market_cap_min:
          parseFloat(document.getElementById("market-cap-min").value) || null,
        market_cap_max:
          parseFloat(document.getElementById("market-cap-max").value) || null,
      },
      weights: {
        financial: parseInt(document.getElementById("financial-weight").value),
        growth: parseInt(document.getElementById("growth-weight").value),
        valuation: parseInt(document.getElementById("valuation-weight").value),
        risk: parseInt(document.getElementById("risk-weight").value),
      },
    };
  }

  async importStrategy() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";

    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const text = await file.text();
        const strategyData = JSON.parse(text);

        this.openStrategyModal(strategyData);
        this.showSnackbar("策略导入成功", "success");
      } catch (error) {
        console.error("Failed to import strategy:", error);
        this.showSnackbar("策略导入失败：文件格式错误", "error");
      }
    };

    input.click();
  }

  filterStrategies() {
    const searchTerm =
      document.getElementById("strategy-search")?.value.toLowerCase() || "";
    const typeFilter =
      document.getElementById("strategy-type-filter")?.value || "";
    const statusFilter =
      document.getElementById("strategy-status-filter")?.value || "";

    const strategyCards = document.querySelectorAll(".md-strategy-card");

    strategyCards.forEach((card) => {
      const title =
        card
          .querySelector(".md-strategy-card__title")
          ?.textContent.toLowerCase() || "";
      const description =
        card
          .querySelector(".md-strategy-card__description")
          ?.textContent.toLowerCase() || "";
      const type = card.dataset.type || "";
      const status = card.dataset.status || "";

      const matchesSearch =
        !searchTerm ||
        title.includes(searchTerm) ||
        description.includes(searchTerm);
      const matchesType = !typeFilter || type === typeFilter;
      const matchesStatus = !statusFilter || status === statusFilter;

      if (matchesSearch && matchesType && matchesStatus) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  }

  async updateStrategySelect() {
    try {
      const response = await this.apiCall("/api/v1/strategies");
      if (response.success && response.data) {
        const select = document.getElementById("strategy-select");
        if (select) {
          // 保留现有选项，添加新策略
          const existingOptions = select.innerHTML;
          const newOptions = response.data
            .map(
              (strategy) =>
                `<option value="${strategy.id}">${strategy.name}</option>`
            )
            .join("");

          select.innerHTML = existingOptions + newOptions;
        }
      }
    } catch (error) {
      console.error("Failed to update strategy select:", error);
    }
  }

  async renderStrategiesGrid(strategies) {
    const container = document.getElementById("strategies-container");
    if (!container) return;

    container.innerHTML = strategies
      .map(
        (strategy) => `
      <div class="md-strategy-card" data-type="${strategy.type}" data-status="${
          strategy.status
        }">
        <div class="md-strategy-card__header">
          <div class="md-strategy-card__status md-strategy-card__status--${
            strategy.status
          }">
            ${this.getStatusLabel(strategy.status)}
          </div>
          <button class="md-icon-button" onclick="app.editStrategy('${
            strategy.id
          }')">
            <span class="material-icons">edit</span>
          </button>
        </div>
        <div class="md-card__content">
          <h3 class="md-strategy-card__title">${strategy.name}</h3>
          <p class="md-strategy-card__description">${
            strategy.description || "暂无描述"
          }</p>

          <div class="md-strategy-card__metrics">
            <div class="md-strategy-metric">
              <div class="md-strategy-metric__value">${
                strategy.matched_stocks || 0
              }</div>
              <div class="md-strategy-metric__label">匹配股票</div>
            </div>
            <div class="md-strategy-metric">
              <div class="md-strategy-metric__value">${
                strategy.avg_score || 0
              }</div>
              <div class="md-strategy-metric__label">平均评分</div>
            </div>
          </div>

          <div class="md-card__actions">
            <button class="md-button md-button--text" onclick="app.executeStrategy('${
              strategy.id
            }')">
              <span class="material-icons">play_arrow</span>
              执行策略
            </button>
            <button class="md-button md-button--outlined" onclick="app.toggleStrategyStatus('${
              strategy.id
            }')">
              ${strategy.status === "active" ? "停用" : "激活"}
            </button>
          </div>
        </div>
      </div>
    `
      )
      .join("");
  }

  getStatusLabel(status) {
    const labels = {
      active: "已激活",
      inactive: "未激活",
      testing: "测试中",
    };
    return labels[status] || status;
  }

  async executeStrategy(strategyId) {
    this.showLoading("正在执行策略...");

    try {
      const response = await this.apiCall(
        `/api/v1/strategies/${strategyId}/execute`,
        {
          method: "POST",
        }
      );

      if (response.success) {
        this.showSnackbar(
          `策略执行完成：找到 ${response.data.total} 只推荐股票`,
          "success"
        );

        // 切换到股票列表视图显示结果
        this.switchView("stocks");
        this.renderStocksTable(response.data.stocks);
      }
    } catch (error) {
      console.error("Failed to execute strategy:", error);
      this.showSnackbar("策略执行失败", "error");
    } finally {
      this.hideLoading();
    }
  }

  async toggleStrategyStatus(strategyId) {
    try {
      const response = await this.apiCall(
        `/api/v1/strategies/${strategyId}/toggle`,
        {
          method: "POST",
        }
      );

      if (response.success) {
        this.showSnackbar("策略状态已更新", "success");
        await this.loadStrategiesData();
      }
    } catch (error) {
      console.error("Failed to toggle strategy status:", error);
      this.showSnackbar("状态更新失败", "error");
    }
  }

  async editStrategy(strategyId) {
    try {
      const response = await this.apiCall(`/api/v1/strategies/${strategyId}`);
      if (response.success) {
        this.openStrategyModal(response.data);
      }
    } catch (error) {
      console.error("Failed to load strategy for editing:", error);
      this.showSnackbar("加载策略失败", "error");
    }
  }
}

// Initialize app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.app = new FinancialApp();
});

// Service worker registration for PWA capabilities
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/static/sw.js")
      .then((registration) => {
        console.log("SW registered: ", registration);
      })
      .catch((registrationError) => {
        console.log("SW registration failed: ", registrationError);
      });
  });
}
