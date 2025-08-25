/**
 * 系统配置管理模块
 */

const ConfigManager = {
  // 加载配置数据
  load: async () => {
    try {
      // 加载系统信息
      await ConfigManager.loadSystemInfo();
      // 加载配置编辑器
      $("#config-editor").html(
        '<div class="alert alert-info">配置管理功能正在开发中。</div>'
      );
    } catch (error) {
      console.error("加载配置数据失败:", error);
    }
  },

  // 加载系统信息
  loadSystemInfo: async () => {
    try {
      const info = await SystemAPI.getInfo();
      STATE.systemInfo = info;

      const infoHtml = `
        <table class="table table-sm">
          <tr><td>Python 版本</td><td>${info.system.python_version}</td></tr>
          <tr><td>操作系统</td><td>${info.system.os}</td></tr>
          <tr><td>CPU 核心数</td><td>${info.system.cpu_cores}</td></tr>
          <tr><td>总内存</td><td>${Utils.formatNumber(
            info.system.memory.total_gb,
            2
          )} GB</td></tr>
          <tr><td>可用内存</td><td>${Utils.formatNumber(
            info.system.memory.available_gb,
            2
          )} GB</td></tr>
          <tr><td>数据源</td><td>${info.dependencies
            .map((d) => `${d.name} (${d.status})`)
            .join("<br>")}</td></tr>
        </table>
      `;
      $("#system-info").html(infoHtml);
    } catch (error) {
      $("#system-info").html(
        '<div class="alert alert-danger">无法加载系统信息。</div>'
      );
    }
  },

  // 清除缓存
  clearCache: () => {
    if (confirm("确定要清除所有缓存吗？此操作不可逆。")) {
      SystemAPI.clearCache()
        .then(() => {
          Utils.showToast("缓存已成功清除", "success");
        })
        .catch(() => {
          Utils.showToast("清除缓存失败", "error");
        });
    }
  },

  // 重置配置
  resetConfig: () => {
    if (confirm("确定要将所有配置重置为默认值吗？")) {
      ConfigAPI.reset()
        .then(() => {
          Utils.showToast("配置已重置", "success");
          ConfigManager.load(); // 重新加载配置
        })
        .catch(() => {
          Utils.showToast("重置配置失败", "error");
        });
    }
  },

  // 获取缓存信息
  getCacheInfo: async () => {
    try {
      const response = await SystemAPI.getCacheInfo();
      if (response.success) {
        const info = response.data;
        const message = `
          缓存条目数: ${info.item_count}
          总大小: ${Utils.formatNumber(info.total_size_mb, 2)} MB
          平均大小: ${Utils.formatNumber(info.average_size_kb, 2)} KB
          命中率: ${Utils.formatPercent(info.hit_rate)}
        `;
        alert("缓存信息:\\n" + message.replace(/ /g, ""));
      } else {
        Utils.showToast(response.message || "获取缓存信息失败", "error");
      }
    } catch (error) {
      console.error("获取缓存信息失败:", error);
      Utils.showToast("获取缓存信息失败", "error");
    }
  },

  // 导出数据
  exportData: () => {
    Utils.showToast("正在准备导出数据...", "info");
    ConfigAPI.exportData()
      .then((response) => {
        if (response.success) {
          Utils.showToast(
            `数据导出成功，文件路径: ${response.data.file_path}`,
            "success"
          );
        } else {
          Utils.showToast(response.message || "导出数据失败", "error");
        }
      })
      .catch((error) => {
        console.error("导出数据失败:", error);
        Utils.showToast("导出数据失败", "error");
      });
  },
};

// 导出配置管理模块
window.ConfigManager = ConfigManager;
