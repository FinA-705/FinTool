/**
 * 策略管理模块
 */

const StrategiesManager = {
  // 加载策略
  load: async () => {
    try {
  // 注入工具栏（一次性）
  StrategiesManager._ensureToolbar();

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
                <button class="btn btn-sm btn-outline-secondary" title="启用/禁用" onclick="StrategiesManager.toggleEnable('${
                  strategy.name
                }', ${strategy.status === "active" ? "false" : "true"})">
                  <i class="fas ${
                    strategy.status === "active" ? "fa-pause" : "fa-check"
                  }"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" title="克隆" onclick="StrategiesManager.clone('${
                  strategy.name
                }')">
                  <i class="fas fa-clone"></i>
                </button>
                <button class="btn btn-sm btn-outline-dark" title="导出" onclick="StrategiesManager.export('${
                  strategy.name
                }')">
                  <i class="fas fa-download"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning" title="导入(覆盖)" onclick="StrategiesManager.import('${
                  strategy.name
                }')">
                  <i class="fas fa-upload"></i>
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
    // 仅更新现存的选择器，避免引用已删除的遗留元素
    const $backtestSelect = $("#backtest-strategy");
    if ($backtestSelect.length) {
      $backtestSelect.find("option:not(:first)").remove();
      strategies.forEach((s) => {
        $backtestSelect.append(`<option value="${s.name}">${s.name}</option>`);
      });
    }
  },

  // 处理策略提交
  handleSubmit: (e) => {
    e.preventDefault();

    const name = $("#strategy-name").val();
    const description = $("#strategy-description").val();
    const filtersRaw = $("#strategy-filters").val();
    const scoreFormula = $("#strategy-score").val();

    if (!name) {
      Utils.showToast("策略名称不能为空", "warning");
      return;
    }

    // 将简单表单映射到后端结构（示例：filters 作为标签数组放入 filters.tags）
    const payload = {
      name,
      description,
      version: "1.0.0",
      parameters: { score_formula: scoreFormula },
      weight_config: {},
      filters: { tags: (filtersRaw || "")
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean) },
      enabled: true,
    };

    StrategyAPI.create(payload)
      .then((resp) => {
        if (resp.success) {
          Utils.showToast(`策略 "${name}" 创建成功`, "success");
          $("#strategy-form")[0]?.reset?.();
          StrategiesManager.load();
        } else {
          Utils.showToast(resp.message || "创建失败", "error");
        }
      })
      .catch((err) => {
        console.error(err);
        Utils.showToast("创建失败", "error");
      });
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
    if (!confirm(`确定要删除策略 "${name}" 吗？`)) return;
    StrategyAPI.delete(name)
      .then((resp) => {
        if (resp.success) {
          Utils.showToast(`策略 "${name}" 已删除`, "success");
          StrategiesManager.load();
        } else {
          Utils.showToast(resp.message || "删除失败", "error");
        }
      })
      .catch((e) => {
        console.error(e);
        Utils.showToast("删除失败", "error");
      });
  },

  // 执行默认策略
  executeDefault: () => {
    StrategiesManager.executeWithParams("价值策略", 10, true);
  },

  // ========== 新增：启用/禁用、克隆、导出、导入、编辑 ==========

  toggleEnable: (name, enabled) => {
    StrategyAPI.enable(name, !!enabled)
      .then((resp) => {
        if (resp.success) {
          Utils.showToast(`已${enabled ? "启用" : "禁用"}策略 ${name}`, "success");
          StrategiesManager.load();
        } else {
          Utils.showToast(resp.message || "操作失败", "error");
        }
      })
      .catch((e) => {
        console.error(e);
        Utils.showToast("操作失败", "error");
      });
  },

  clone: (name) => {
    const newName = prompt("输入新策略名称:");
    if (!newName) return;
    StrategyAPI.clone(name, newName)
      .then((resp) => {
        if (resp.success) {
          Utils.showToast("克隆成功", "success");
          StrategiesManager.load();
        } else {
          Utils.showToast(resp.message || "克隆失败", "error");
        }
      })
      .catch((e) => {
        console.error(e);
        Utils.showToast("克隆失败", "error");
      });
  },

  export: async (name) => {
    try {
      const resp = await StrategyAPI.export(name);
      if (!resp || !resp.success) {
        Utils.showToast((resp && resp.message) || "导出失败", "error");
        return;
      }
      const data = resp.data || {};
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${name}.strategy.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      Utils.showToast("已下载配置", "success");
    } catch (e) {
      console.error(e);
      Utils.showToast("导出失败", "error");
    }
  },

  import: async (name) => {
    try {
      const content = await StrategiesManager._promptLarge(
        `导入覆盖策略 ${name} 的配置`,
        '{\n  "version": "1.0.1",\n  "parameters": {},\n  "weight_config": {},\n  "filters": {},\n  "enabled": true\n}'
      );

      if (!content) return;
      let config;
      try {
        config = JSON.parse(content);
      } catch (e) {
        Utils.showToast("JSON 解析失败", "error");
        return;
      }

      const resp = await StrategyAPI.import(name, config);
      if (resp && resp.success) {
        Utils.showToast("导入成功", "success");
        StrategiesManager.load();
      } else {
        Utils.showToast((resp && resp.message) || "导入失败", "error");
      }
    } catch (e) {
      console.error(e);
      Utils.showToast("导入失败", "error");
    }
  },

  edit: async (name) => {
    try {
      const resp = await StrategyAPI.get(name);
      if (!resp || !resp.success) {
        Utils.showToast((resp && resp.message) || "获取策略失败", "error");
        return;
      }
      const data = resp.data || {};
      const content = `
        <div class="mb-2">
          <label class="form-label">版本</label>
          <input id="_st_ver" class="form-control" value="${
            (data.version || "").toString().replace(/"/g, "&quot;")
          }" />
        </div>
        <div class="form-check form-switch mb-2">
          <input class="form-check-input" type="checkbox" id="_st_enabled" ${
            data.enabled ? "checked" : ""
          }>
          <label class="form-check-label" for="_st_enabled">启用</label>
        </div>
        <div class="mb-2">
          <label class="form-label">参数 (JSON)</label>
          <textarea id="_st_params" class="form-control" rows="6">${
            JSON.stringify(data.parameters || {}, null, 2)
          }</textarea>
        </div>
        <div class="mb-2">
          <label class="form-label">权重 (JSON)</label>
          <textarea id="_st_weights" class="form-control" rows="6">${
            JSON.stringify(data.weight_config || {}, null, 2)
          }</textarea>
        </div>
        <div class="mb-2">
          <label class="form-label">过滤器 (JSON)</label>
          <textarea id="_st_filters" class="form-control" rows="6">${
            JSON.stringify(data.filters || {}, null, 2)
          }</textarea>
        </div>
      `;

      StrategiesManager._showModal(`编辑策略 - ${name}`, content, async () => {
        try {
          const version = document.getElementById('_st_ver').value;
          const enabled = document.getElementById('_st_enabled').checked;
          let parameters = {}, weight_config = {}, filters = {};
          try { parameters = JSON.parse(document.getElementById('_st_params').value || '{}'); } catch { throw new Error('参数 JSON 无效'); }
          try { weight_config = JSON.parse(document.getElementById('_st_weights').value || '{}'); } catch { throw new Error('权重 JSON 无效'); }
          try { filters = JSON.parse(document.getElementById('_st_filters').value || '{}'); } catch { throw new Error('过滤器 JSON 无效'); }

          const updates = { version, parameters, weight_config, filters, enabled };
          const resp2 = await StrategyAPI.update(name, updates);
          if (resp2 && resp2.success) {
            Utils.showToast('保存成功', 'success');
            StrategiesManager.load();
            return true; // 关闭
          } else {
            Utils.showToast((resp2 && resp2.message) || '保存失败', 'error');
            return false;
          }
        } catch (e) {
          console.error(e);
          Utils.showToast(e.message || '保存失败', 'error');
          return false;
        }
      });
    } catch (e) {
      console.error(e);
      Utils.showToast('获取策略失败', 'error');
    }
  },

  // ========== 辅助UI ==========

  _ensureToolbar: () => {
    const toolbarId = 'strategies-toolbar-actions';
    if (document.getElementById(toolbarId)) return;
    const toolbar = document.createElement('div');
    toolbar.id = toolbarId;
    toolbar.className = 'mb-2 d-flex gap-2';
    toolbar.innerHTML = `
      <button id="btn-strategy-create" class="btn btn-outline-primary btn-sm">
        <i class="fas fa-plus"></i> 新建策略
      </button>
      <button id="btn-strategy-import-global" class="btn btn-outline-warning btn-sm">
        <i class="fas fa-upload"></i> 导入策略
      </button>
      <button id="btn-strategy-refresh" class="btn btn-outline-secondary btn-sm">
        <i class="fas fa-sync"></i> 刷新
      </button>
    `;
    const container = document.getElementById('strategies-list');
    if (container && container.parentElement) {
      container.parentElement.insertBefore(toolbar, container);
    } else {
      document.body.insertBefore(toolbar, document.body.firstChild);
    }

    document.getElementById('btn-strategy-create').addEventListener('click', () => {
      StrategiesManager._openCreateModal();
    });
    document.getElementById('btn-strategy-import-global').addEventListener('click', async () => {
      const name = prompt('导入到策略名称（不存在则创建）：');
      if (!name) return;
      const content = await StrategiesManager._promptLarge('粘贴策略配置 JSON', '{\n  "version": "1.0.0",\n  "parameters": {},\n  "weight_config": {},\n  "filters": {},\n  "enabled": true\n}');
      if (!content) return;
      let config;
      try { config = JSON.parse(content); } catch { Utils.showToast('JSON 解析失败', 'error'); return; }
      // 复用 import 接口：若策略不存在，先 create，再 import
      try {
        const list = await StrategyAPI.list();
        const exists = (list && list.success && (list.data||[]).some(s=>s.name===name));
        if (!exists) {
          await StrategyAPI.create({ name, version: config.version||'1.0.0', parameters: config.parameters||{}, weight_config: config.weight_config||{}, filters: config.filters||{}, enabled: !!config.enabled });
        }
        const resp = await StrategyAPI.import(name, config);
        if (resp && resp.success) {
          Utils.showToast('导入成功', 'success');
          StrategiesManager.load();
        } else {
          Utils.showToast((resp && resp.message) || '导入失败', 'error');
        }
      } catch (e) {
        console.error(e);
        Utils.showToast('导入失败', 'error');
      }
    });
    document.getElementById('btn-strategy-refresh').addEventListener('click', () => StrategiesManager.load());
  },

  _openCreateModal: () => {
    const content = `
      <div class="mb-2">
        <label class="form-label">名称</label>
        <input id="_st_new_name" class="form-control" placeholder="如 schloss" />
      </div>
      <div class="mb-2">
        <label class="form-label">版本</label>
        <input id="_st_new_ver" class="form-control" value="1.0.0" />
      </div>
      <div class="mb-2">
        <label class="form-label">参数 (JSON)</label>
        <textarea id="_st_new_params" class="form-control" rows="5">{}</textarea>
      </div>
      <div class="mb-2">
        <label class="form-label">权重 (JSON)</label>
        <textarea id="_st_new_weights" class="form-control" rows="5">{}</textarea>
      </div>
      <div class="mb-2">
        <label class="form-label">过滤器 (JSON)</label>
        <textarea id="_st_new_filters" class="form-control" rows="5">{}</textarea>
      </div>
      <div class="form-check form-switch mb-2">
        <input class="form-check-input" type="checkbox" id="_st_new_enabled" checked>
        <label class="form-check-label" for="_st_new_enabled">启用</label>
      </div>
    `;
    StrategiesManager._showModal('新建策略', content, async () => {
      const name = document.getElementById('_st_new_name').value.trim();
      if (!name) { Utils.showToast('名称不能为空', 'warning'); return false; }
      const version = document.getElementById('_st_new_ver').value;
      let parameters = {}, weight_config = {}, filters = {};
      try { parameters = JSON.parse(document.getElementById('_st_new_params').value || '{}'); } catch { Utils.showToast('参数 JSON 无效', 'error'); return false; }
      try { weight_config = JSON.parse(document.getElementById('_st_new_weights').value || '{}'); } catch { Utils.showToast('权重 JSON 无效', 'error'); return false; }
      try { filters = JSON.parse(document.getElementById('_st_new_filters').value || '{}'); } catch { Utils.showToast('过滤器 JSON 无效', 'error'); return false; }
      const enabled = document.getElementById('_st_new_enabled').checked;
      const resp = await StrategyAPI.create({ name, version, parameters, weight_config, filters, enabled });
      if (resp && resp.success) {
        Utils.showToast('创建成功', 'success');
        StrategiesManager.load();
        return true;
      } else {
        Utils.showToast((resp && resp.message) || '创建失败', 'error');
        return false;
      }
    });
  },

  _showModal: (title, innerHTML, onSubmit) => {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1050;display:flex;align-items:center;justify-content:center;padding:20px;';
    const box = document.createElement('div');
    box.className = 'card';
    box.style.cssText = 'max-width:720px;width:100%;';
    box.innerHTML = `
      <div class="card-header d-flex justify-content-between align-items-center">
        <strong>${title}</strong>
        <button class="btn btn-sm btn-outline-secondary" id="_st_close">×</button>
      </div>
      <div class="card-body">${innerHTML}</div>
      <div class="card-footer d-flex justify-content-end gap-2">
        <button class="btn btn-secondary btn-sm" id="_st_cancel">取消</button>
        <button class="btn btn-primary btn-sm" id="_st_save">保存</button>
      </div>
    `;
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    const close = () => overlay.remove();
    box.querySelector('#_st_close').onclick = close;
    box.querySelector('#_st_cancel').onclick = close;
    box.querySelector('#_st_save').onclick = async () => {
      const ok = (await onSubmit?.()) !== false;
      if (ok) close();
    };
  },

  _promptLarge: (title, defaultText = '') => {
    return new Promise((resolve) => {
      const content = `<textarea id="_st_text" class="form-control" rows="12">${defaultText}</textarea>`;
      StrategiesManager._showModal(title, content, async () => {
        const val = document.getElementById('_st_text').value;
        resolve(val);
        return true;
      });
    });
  },
};

// 导出策略管理模块
window.StrategiesManager = StrategiesManager;
