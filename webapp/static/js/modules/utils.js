/**
 * 工具函数库
 */

const Utils = {
  // 格式化数字
  formatNumber: (num, decimals = 2) => {
    if (
      num === null ||
      num === undefined ||
      typeof num !== "number" ||
      isNaN(num)
    ) {
      return "--";
    }
    return new Intl.NumberFormat("zh-CN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  },

  // 格式化百分比
  formatPercent: (num, decimals = 2) => {
    if (
      num === null ||
      num === undefined ||
      typeof num !== "number" ||
      isNaN(num)
    ) {
      return "--";
    }
    return (num * 100).toFixed(decimals) + "%";
  },

  // 格式化金额
  formatCurrency: (num) => {
    if (
      num === null ||
      num === undefined ||
      typeof num !== "number" ||
      isNaN(num)
    ) {
      return "--";
    }
    if (num >= 1e8) return (num / 1e8).toFixed(2) + "亿";
    if (num >= 1e4) return (num / 1e4).toFixed(2) + "万";
    return num.toFixed(2);
  },

  // 格式化市盈率等指标，精确判断亏损
  formatPERatio: (num, decimals = 2) => {
    if (
      num === null ||
      num === undefined ||
      typeof num !== "number" ||
      isNaN(num)
    ) {
      // 只有当明确知道是亏损时才显示红色"亏损"
      // 这里需要结合EPS数据来判断，如果没有EPS数据则显示"--"
      return '<span class="text-muted">--</span>';
    }
    if (num < 0) {
      return '<span class="text-danger">亏损</span>';
    }
    return new Intl.NumberFormat("zh-CN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
  },

  // 智能格式化PE，结合EPS判断
  formatPEWithEPS: (pe, eps, decimals = 2) => {
    // 如果EPS为负数，明确是亏损
    if (eps !== null && eps !== undefined && typeof eps === "number" && eps < 0) {
      return '<span class="text-danger">亏损</span>';
    }

    // 如果EPS为正但PE为null，可能是数据缺失
    if ((eps === null || eps === undefined) && (pe === null || pe === undefined)) {
      return '<span class="text-muted">--</span>';
    }

    // 如果有有效的PE值
    if (pe !== null && pe !== undefined && typeof pe === "number" && !isNaN(pe)) {
      return new Intl.NumberFormat("zh-CN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(pe);
    }

    return '<span class="text-muted">--</span>';
  },

  // 格式化财务指标，null值显示为--
  formatFinancialRatio: (num, decimals = 2, unit = '') => {
    if (
      num === null ||
      num === undefined ||
      typeof num !== "number" ||
      isNaN(num)
    ) {
      return "--";
    }
    const formatted = new Intl.NumberFormat("zh-CN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(num);
    return unit ? formatted + unit : formatted;
  },

  // 获取颜色（根据数值正负）
  getColor: (value) => {
    if (typeof value !== "number" || isNaN(value)) return "text-muted";
    return value > 0
      ? "text-success"
      : value < 0
      ? "text-danger"
      : "text-muted";
  },

  // 显示通知
  showToast: (message, type = "info") => {
    const toast = $("#toast");
    const toastBody = toast.find(".toast-body");
    const toastHeader = toast.find(".toast-header strong");

    toastBody.text(message);

    // 设置图标和颜色
    const icons = {
      success: "fa-check-circle text-success",
      error: "fa-exclamation-circle text-danger",
      warning: "fa-exclamation-triangle text-warning",
      info: "fa-info-circle text-info",
    };

    toastHeader.html(
      `<i class="fas ${icons[type] || icons.info} me-2"></i>系统通知`
    );

    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();
  },

  // 防抖函数
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // 节流函数
  throttle: (func, limit) => {
    let inThrottle;
    return function () {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => (inThrottle = false), limit);
      }
    };
  },
};

// 导出工具函数
window.Utils = Utils;
