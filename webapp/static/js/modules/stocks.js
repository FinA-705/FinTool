/**
 * 股票数据管理模块
 */

const StocksManager = {
  // 加载股票数据
  load: async () => {
    try {
      if (!STATE.stocksTable) {
        StocksManager.initializeTable();
      }
      await StocksManager.refresh();
    } catch (error) {
      console.error("加载股票数据失败:", error);
    }
  },

  // 初始化数据表格
  initializeTable: () => {
    STATE.stocksTable = $("#stocks-table").DataTable({
      columns: [
        { data: "code", title: "股票代码", defaultContent: "-" },
        { data: "name", title: "股票名称", defaultContent: "-" },
        { data: "market", title: "市场", defaultContent: "-" },
        {
          data: "price",
          title: "价格",
          render: function (data) {
            return Utils.formatNumber(data);
          },
        },
        {
          data: "change",
          title: "涨跌幅",
          render: function (data) {
            const colorClass = Utils.getColor(data);
            return `<span class="${colorClass}">${Utils.formatPercent(
              data
            )}</span>`;
          },
        },
        {
          data: "volume",
          title: "成交量",
          render: function (data) {
            return Utils.formatCurrency(data);
          },
        },
        {
          data: "market_cap",
          title: "市值",
          render: function (data) {
            return Utils.formatCurrency(data);
          },
        },
        {
          data: "pe",
          title: "PE",
          render: function (data, type, row) {
            // 使用EPS来智能判断PE显示
            return Utils.formatPEWithEPS(data, row.eps, 1);
          },
        },
        {
          data: "pb",
          title: "PB",
          render: function (data) {
            return Utils.formatNumber(data, 1);
          },
        },
        {
          data: null,
          title: "操作",
          render: function (data, type, row) {
            return `
              <button class="btn btn-sm btn-primary" onclick="StocksManager.showDetail('${row.code}')">
                <i class="fas fa-eye"></i>
              </button>
              <button class="btn btn-sm btn-success" onclick="StocksManager.addToWatchlist('${row.code}')">
                <i class="fas fa-star"></i>
              </button>
            `;
          },
        },
      ],
      pageLength: 25,
      responsive: true,
      language: {
        url: "//cdn.datatables.net/plug-ins/1.10.25/i18n/Chinese.json",
      },
    });
  },

  // 刷新股票数据
  refresh: async () => {
    try {
      const market = $("#market-select").val() || "a_stock";
      const symbols = $("#symbols-input").val();

      // 构建API参数
      const params = { market };
      if (symbols) {
        params.symbols = symbols;
      }

      // 显示加载提示
      Utils.showToast("正在获取股票数据，请稍候...", "info");

      const response = await StockAPI.getStockData(params);

      if (response.success && response.data) {
        STATE.stocksTable.clear().rows.add(response.data).draw();
        Utils.showToast(
          `成功加载 ${response.data.length} 条股票数据`,
          "success"
        );
      } else {
        Utils.showToast(response.message || "获取股票数据失败", "error");
      }
    } catch (error) {
      console.error("刷新股票数据失败:", error);
      Utils.showToast("刷新股票数据失败", "error");
    }
  },

  // 搜索股票
  search: () => {
    StocksManager.refresh();
  },

  // 导出数据
  export: () => {
    if (!STATE.stocksTable) {
      Utils.showToast("没有数据可导出", "warning");
      return;
    }

    // 获取当前表格数据
    const data = STATE.stocksTable.data().toArray();

    // 转换为CSV
    const headers = [
      "股票代码",
      "股票名称",
      "市场",
      "价格",
      "涨跌幅",
      "成交量",
      "市值",
      "PE",
      "PB",
    ];
    const csvContent = [
      headers.join(","),
      ...data.map((row) =>
        [
          row.code,
          row.name,
          row.market,
          row.price,
          row.change,
          row.volume,
          row.market_cap,
          row.pe,
          row.pb,
        ].join(",")
      ),
    ].join("\n");

    // 下载文件
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `股票数据_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();

    Utils.showToast("数据导出成功", "success");
  },

  // 显示股票详情
  showDetail: async (code) => {
    const modal = new bootstrap.Modal($("#stockDetailModal")[0]);
    $("#stock-detail-content").html(`
      <div class="text-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
        <p class="mt-2">正在加载股票 ${code} 的详细信息...</p>
      </div>
    `);
    modal.show();

    try {
      const response = await StockAPI.getStockInfo(code);

      if (!response.success) {
        throw new Error(response.detail || response.message || "获取失败");
      }

      const d = response.data || {};
      const safe = (v, fallback = "-") =>
        v === null || v === undefined || v === "" ? fallback : v;
      const safePE = (pe, eps) => {
        // 使用EPS来智能判断PE显示
        if (eps !== null && eps !== undefined && typeof eps === "number" && eps < 0) {
          return '<span class="text-danger">亏损</span>';
        }
        if (pe === null || pe === undefined || pe === "") {
          return '<span class="text-muted">--</span>';
        }
        return pe;
      };
      const pct = (v) =>
        v === null || v === undefined ? "-" : (v * 100).toFixed(2) + "%";
      const fm = d.financial_metrics || {};
      const ti = d.technical_indicators || {};

      $("#stock-detail-content").html(`
        <div class="row">
          <div class="col-md-6">
            <h6>基本信息</h6>
            <table class="table table-sm">
              <tr><td>股票代码</td><td>${safe(d.code)}</td></tr>
              <tr><td>股票名称</td><td>${safe(d.name)}</td></tr>
              <tr><td>所属行业</td><td>${safe(d.industry)}</td></tr>
              <tr><td>地区</td><td>${safe(d.area)}</td></tr>
              <tr><td>市场</td><td>${safe(d.market)}</td></tr>
              <tr><td>上市日期</td><td>${safe(
                String(d.listing_date).split(" ")[0]
              )}</td></tr>
            </table>
          </div>
          <div class="col-md-6">
            <h6>财务指标</h6>
            <table class="table table-sm">
              <tr><td>市盈率</td><td>${safePE(fm.pe, fm.eps)}</td></tr>
              <tr><td>市净率</td><td>${safe(fm.pb)}</td></tr>
              <tr><td>ROE</td><td>${safe(fm.roe)}</td></tr>
              <tr><td>ROA</td><td>${safe(fm.roa)}</td></tr>
              <tr><td>负债率</td><td>${safe(fm.debt_ratio)}</td></tr>
              <tr><td>每股收益(EPS)</td><td>${safe(fm.eps)}</td></tr>
            </table>
          </div>
        </div>
      `);
    } catch (error) {
      $("#stock-detail-content").html(
        `<div class='text-danger'>获取股票详情失败: ${error.message}</div>`
      );
    }
  },

  // 添加到自选股
  addToWatchlist: (code) => {
    Utils.showToast(`股票 ${code} 已添加到自选股`, "success");
  },

  // 手动缓存财务指标
  cacheMetrics: async (limit = null, forceUpdate = false) => {
    try {
      const params = {};
      if (limit) params.limit = limit;
      if (forceUpdate) params.force_update = forceUpdate;

      Utils.showToast("正在缓存财务指标，请稍候...", "info");

      const response = await StockAPI.cacheMetrics(params);

      if (response.success) {
        const data = response.data || {};
        Utils.showToast(
          `缓存成功：处理了 ${data.total_processed || 0} 只股票，保存了 ${data.cached_count || 0} 条财务指标`,
          "success"
        );
      } else {
        Utils.showToast(response.message || "缓存财务指标失败", "error");
      }
    } catch (error) {
      console.error("缓存财务指标失败:", error);
      Utils.showToast("缓存财务指标失败", "error");
    }
  },

  // 搜索股票
  searchStocks: async (query, market = "a_stock", limit = 20) => {
    try {
      const params = { query, market, limit };
      const response = await StockAPI.searchStocks(params);

      if (response.success) {
        return response.data || [];
      } else {
        Utils.showToast(response.message || "搜索失败", "error");
        return [];
      }
    } catch (error) {
      console.error("搜索股票失败:", error);
      Utils.showToast("搜索股票失败", "error");
      return [];
    }
  },

  // 获取热门股票
  getTrendingStocks: async (market = "a_stock", limit = 10) => {
    try {
      const params = { market, limit };
      const response = await StockAPI.getTrendingStocks(params);

      if (response.success) {
        return response.data || [];
      } else {
        Utils.showToast(response.message || "获取热门股票失败", "error");
        return [];
      }
    } catch (error) {
      console.error("获取热门股票失败:", error);
      Utils.showToast("获取热门股票失败", "error");
      return [];
    }
  },

  // 获取支持的市场
  getMarkets: async () => {
    try {
      const response = await StockAPI.getMarkets();

      if (response.success) {
        return response.data || [];
      } else {
        Utils.showToast(response.message || "获取市场信息失败", "error");
        return [];
      }
    } catch (error) {
      console.error("获取市场信息失败:", error);
      Utils.showToast("获取市场信息失败", "error");
      return [];
    }
  },

  // 获取行业分类
  getIndustries: async (market = "a_stock") => {
    try {
      const params = { market };
      const response = await StockAPI.getIndustries(params);

      if (response.success) {
        return response.data || [];
      } else {
        Utils.showToast(response.message || "获取行业信息失败", "error");
        return [];
      }
    } catch (error) {
      console.error("获取行业信息失败:", error);
      Utils.showToast("获取行业信息失败", "error");
      return [];
    }
  },

  // 检查Tushare健康状态
  checkTushareHealth: async () => {
    try {
      const response = await StockAPI.checkTushareHealth();

      if (response.success) {
        const data = response.data || {};
        const status = data.token_valid ? "健康" : "异常";
        Utils.showToast(`Tushare状态: ${status}`, data.token_valid ? "success" : "warning");
        return data;
      } else {
        Utils.showToast(response.message || "健康检查失败", "error");
        return null;
      }
    } catch (error) {
      console.error("Tushare健康检查失败:", error);
      Utils.showToast("Tushare健康检查失败", "error");
      return null;
    }
  },

  // 执行选股策略
  screenStocks: async (strategyData) => {
    try {
      Utils.showToast("正在执行选股策略，请稍候...", "info");

      const response = await StockAPI.screenStocks(strategyData);

      if (response.success) {
        const data = response.data || [];
        Utils.showToast(
          `策略执行成功，找到 ${data.length} 只股票`,
          "success"
        );
        return data;
      } else {
        Utils.showToast(response.message || "策略执行失败", "error");
        return [];
      }
    } catch (error) {
      console.error("策略执行失败:", error);
      Utils.showToast("策略执行失败", "error");
      return [];
    }
  },
};

// 导出股票管理模块
window.StocksManager = StocksManager;
