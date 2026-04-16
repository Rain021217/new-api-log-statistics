const STORAGE_KEYS = {
  visibleColumns: "new-api-log-statistics-visible-columns",
  savedFilter: "new-api-log-statistics-saved-filter",
  recentSource: "new-api-log-statistics-recent-source",
  theme: "new-api-log-statistics-theme",
};

const healthOutput = document.getElementById("health-output");
const healthBadge = document.getElementById("health-badge");
const sourcesCount = document.getElementById("sources-count");
const sourcesList = document.getElementById("sources-list");
const sourcesEmpty = document.getElementById("sources-empty");
const sourceSelect = document.getElementById("source-id");
const sourceUriForm = document.getElementById("source-uri-form");
const sourceManualForm = document.getElementById("source-manual-form");
const sourceSaveOutput = document.getElementById("source-save-output");
const scanLocalConfigsButton = document.getElementById("scan-local-configs");
const columnSettingsToggle = document.getElementById("column-settings-toggle");
const columnSettingsPanel = document.getElementById("column-settings-panel");
const columnSettingInputs = Array.from(columnSettingsPanel.querySelectorAll("input[type='checkbox']"));
const themeToggleButton = document.getElementById("theme-toggle");
const authSessionBadge = document.getElementById("auth-session-badge");
const authLogoutButton = document.getElementById("auth-logout");
const authGate = document.getElementById("auth-gate");
const authLoginForm = document.getElementById("auth-login-form");
const authUsernameInput = document.getElementById("auth-username");
const authPasswordInput = document.getElementById("auth-password");
const authMessage = document.getElementById("auth-message");
const protectedShell = document.getElementById("protected-shell");
const saveFilterButton = document.getElementById("save-filter");
const restoreFilterButton = document.getElementById("restore-filter");
const exportChartsImageButton = document.getElementById("export-charts-image");
const uriSourceNameInput = document.getElementById("uri-source-name");
const sourceUriInput = document.getElementById("source-uri");
const manualSourceNameInput = document.getElementById("manual-source-name");
const manualDbTypeInput = document.getElementById("manual-db-type");
const manualHostInput = document.getElementById("manual-host");
const manualPortInput = document.getElementById("manual-port");
const manualDatabaseInput = document.getElementById("manual-database");
const manualUserInput = document.getElementById("manual-user");
const manualPasswordInput = document.getElementById("manual-password");
const tokenInput = document.getElementById("token-name");
const tokenSuggestions = document.getElementById("token-suggestions");
const modelNameInput = document.getElementById("model-name");
const usernameInput = document.getElementById("username");
const groupNameInput = document.getElementById("group-name");
const channelIdInput = document.getElementById("channel-id");
const requestIdInput = document.getElementById("request-id");
const ipInput = document.getElementById("ip");
const startTimeInput = document.getElementById("start-time");
const endTimeInput = document.getElementById("end-time");
const queryForm = document.getElementById("query-form");
const resetFormButton = document.getElementById("reset-form");
const exportLink = document.getElementById("export-link");
const exportXlsxLink = document.getElementById("export-xlsx-link");
const detailsBody = document.getElementById("details-body");
const detailsMeta = document.getElementById("details-meta");
const prevPageButton = document.getElementById("prev-page");
const nextPageButton = document.getElementById("next-page");
const pageInfo = document.getElementById("page-info");
const pageSizeSelect = document.getElementById("page-size-select");
const chartsMeta = document.getElementById("charts-meta");
const sortButtons = Array.from(document.querySelectorAll(".sort-button"));
const chartCostTrend = document.getElementById("chart-cost-trend");
const chartRequestTrend = document.getElementById("chart-request-trend");
const chartCostStack = document.getElementById("chart-cost-stack");
const chartModelRanking = document.getElementById("chart-model-ranking");
const chartModelRequestRanking = document.getElementById("chart-model-request-ranking");
const chartGroupRanking = document.getElementById("chart-group-ranking");
const chartChannelRanking = document.getElementById("chart-channel-ranking");
const chartCacheSavings = document.getElementById("chart-cache-savings");

const DEFAULT_VISIBLE_COLUMNS = {
  id: true,
  created_at: true,
  token_name: true,
  model_name: true,
  quota: true,
  cost_total: true,
  pure_prompt_tokens: true,
  cost_input: true,
  completion_tokens: true,
  cost_output: true,
  cache_tokens: true,
  cost_cache_read: true,
  cache_write_tokens_total: true,
  cost_cache_write: true,
};

let currentSortField = "created_at";
let currentSortDir = "desc";
let currentPage = 1;
let currentPageSize = 20;
let sourceCapabilities = {};
const queryCache = new Map();
const bundledQueryCache = new Map();
let authState = {
  enabled: false,
  authenticated: true,
  username: "",
  allow_basic: true,
  public_health: true,
};
let protectedBootstrapped = false;

function setDefaultTimes() {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  const format = (date) => {
    const pad = (value) => String(value).padStart(2, "0");
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  };
  startTimeInput.value = format(start);
  endTimeInput.value = format(now);
}

function localInputToUnix(value) {
  if (!value) return "";
  const ts = Date.parse(value);
  if (Number.isNaN(ts)) return "";
  return String(Math.floor(ts / 1000));
}

function buildQueryCacheKey(url) {
  return url;
}

function isAuthLocked() {
  return authState.enabled && !authState.authenticated;
}

function setProtectedVisible(visible) {
  protectedShell.classList.toggle("hidden", !visible);
}

function resetProtectedView(message = "请先登录后再查看受保护内容。") {
  setProtectedVisible(false);
  sourcesCount.textContent = "0";
  sourcesList.innerHTML = "";
  sourceSelect.innerHTML = `<option value="">无可用数据源</option>`;
  sourcesEmpty.style.display = "block";
  sourcesEmpty.textContent = message;
  tokenSuggestions.innerHTML = "";
  sourceSaveOutput.textContent = message;
  fillSummary({});
  detailsMeta.textContent = message;
  chartsMeta.textContent = message;
  detailsBody.innerHTML = `<tr><td colspan="14" class="table-empty">${message}</td></tr>`;
  updatePagination({ page: 1, page_size: currentPageSize, total: 0 });
  renderCharts({});
}

function updateAuthUi() {
  if (!authState.enabled) {
    authSessionBadge.className = "badge badge-muted";
    authSessionBadge.textContent = "鉴权关闭";
    authLogoutButton.classList.add("hidden");
    authGate.classList.add("hidden");
    setProtectedVisible(true);
    return;
  }

  if (authState.authenticated) {
    authSessionBadge.className = "badge badge-success";
    authSessionBadge.textContent = `已登录: ${authState.username || "authorized"}`;
    authLogoutButton.classList.remove("hidden");
    authGate.classList.add("hidden");
    authMessage.textContent = "登录成功。";
    setProtectedVisible(true);
    return;
  }

  authSessionBadge.className = "badge badge-warning";
  authSessionBadge.textContent = "需要登录";
  authLogoutButton.classList.add("hidden");
  authGate.classList.remove("hidden");
  authMessage.textContent = "请输入部署时配置的访问账号和密码。";
  resetProtectedView("鉴权已启用，请先登录。");
}

async function handleUnauthorized() {
  queryCache.clear();
  bundledQueryCache.clear();
  protectedBootstrapped = false;
  authState = {
    ...authState,
    enabled: true,
    authenticated: false,
    username: "",
  };
  updateAuthUi();
  try {
    await loadAuthStatus();
  } catch (_) {}
}

async function fetchJson(url, options = {}) {
  const cacheKey = buildQueryCacheKey(url);
  if (!options.bypassCache && queryCache.has(cacheKey)) {
    return queryCache.get(cacheKey);
  }
  const response = await fetch(url, {
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  });
  if (response.status === 401 && !options.allowUnauthorized) {
    await handleUnauthorized();
    throw new Error("需要登录");
  }
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  const data = await response.json();
  if (!options.bypassCache) {
    queryCache.set(cacheKey, data);
  }
  return data;
}

async function fetchJsonWithBody(url, method, body, options = {}) {
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    credentials: "same-origin",
    body: JSON.stringify(body),
  });
  if (response.status === 401 && !options.allowUnauthorized) {
    await handleUnauthorized();
    throw new Error("需要登录");
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  queryCache.clear();
  bundledQueryCache.clear();
  return response.json();
}

function setHealthState(ok) {
  healthBadge.className = `badge ${ok ? "badge-success" : "badge-warning"}`;
  healthBadge.textContent = ok ? "正常" : "异常";
}

function setSummaryValue(id, value) {
  const node = document.getElementById(id);
  if (!node) return;
  node.textContent = value ?? "-";
}

function parseNumeric(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function formatNumeric(value, fractionDigits = 6) {
  const numeric = parseNumeric(value);
  if (numeric === null) return "-";
  if (numeric === 0) return "0";
  if (Number.isInteger(numeric)) return numeric.toLocaleString();
  return numeric.toFixed(fractionDigits).replace(/0+$/, "").replace(/\.$/, "");
}

function formatCell(value, numeric = false) {
  if (value === null || value === undefined || value === "") {
    return { text: "-", className: "cell-empty" };
  }
  if (!numeric) return { text: String(value), className: "" };
  const numericValue = parseNumeric(value);
  if (numericValue === null) return { text: "-", className: "cell-empty" };
  if (numericValue === 0) return { text: "0", className: "cell-zero" };
  return { text: formatNumeric(value), className: "" };
}

function fillSummary(summary = {}) {
  setSummaryValue("summary-total-tokens-consumed", formatNumeric(summary.total_tokens_consumed, 0));
  setSummaryValue("summary-input-tokens-total", formatNumeric(summary.input_tokens_total, 0));
  setSummaryValue("summary-output-tokens-total", formatNumeric(summary.output_tokens_total, 0));
  setSummaryValue("summary-cache-read-tokens-total", formatNumeric(summary.cache_read_tokens_total, 0));
  setSummaryValue("summary-cache-write-tokens-total", formatNumeric(summary.cache_write_tokens_total, 0));
  setSummaryValue("summary-actual-cost-total", formatNumeric(summary.actual_cost_total));
  setSummaryValue("summary-input-cost-total", formatNumeric(summary.input_cost_total));
  setSummaryValue("summary-output-cost-total", formatNumeric(summary.output_cost_total));
  setSummaryValue("summary-cache-read-cost-total", formatNumeric(summary.cache_read_cost_total));
  setSummaryValue("summary-cache-write-cost-total", formatNumeric(summary.cache_write_cost_total));
  setSummaryValue("summary-cache-savings-total", formatNumeric(summary.cache_saving_total));
  setSummaryValue("summary-request-count", formatNumeric(summary.request_count, 0));
  setSummaryValue("summary-avg-rpm", formatNumeric(summary.avg_rpm, 3));
  setSummaryValue("summary-avg-tpm", formatNumeric(summary.avg_tpm, 3));
  setSummaryValue("foot-quota-total", formatNumeric(summary.quota_total, 0));
  setSummaryValue("foot-actual-cost-total", formatNumeric(summary.actual_cost_total));
  setSummaryValue("foot-input-tokens-total", formatNumeric(summary.input_tokens_total, 0));
  setSummaryValue("foot-input-cost-total", formatNumeric(summary.input_cost_total));
  setSummaryValue("foot-output-tokens-total", formatNumeric(summary.output_tokens_total, 0));
  setSummaryValue("foot-output-cost-total", formatNumeric(summary.output_cost_total));
  setSummaryValue("foot-cache-read-tokens-total", formatNumeric(summary.cache_read_tokens_total, 0));
  setSummaryValue("foot-cache-read-cost-total", formatNumeric(summary.cache_read_cost_total));
  setSummaryValue("foot-cache-write-tokens-total", formatNumeric(summary.cache_write_tokens_total, 0));
  setSummaryValue("foot-cache-write-cost-total", formatNumeric(summary.cache_write_cost_total));
}

function renderSourceCard(item) {
  const article = document.createElement("article");
  article.className = "source-card";
  article.innerHTML = `
    <div class="source-card-header">
      <h3>${item.source_name}</h3>
      <div class="source-card-actions">
        ${sourceCapabilities.source_config_writable ? `<button type="button" class="button button-secondary source-delete-button">删除</button>` : ""}
      </div>
    </div>
    <p class="source-meta">
      source_id: ${item.source_id}<br />
      type: ${item.db_type}<br />
      host: ${item.host}:${item.port}<br />
      database: ${item.database}<br />
      timezone: ${item.timezone}<br />
      readonly: ${item.readonly ? "yes" : "no"}<br />
      password saved: ${item.has_password ? "yes" : "no"}
    </p>
  `;
  const deleteButton = article.querySelector(".source-delete-button");
  if (deleteButton) {
    deleteButton.addEventListener("click", async () => {
      await deleteSource(item);
    });
  }
  return article;
}

async function fetchJsonWithMethod(url, method, options = {}) {
  const response = await fetch(url, {
    method,
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  });
  if (response.status === 401 && !options.allowUnauthorized) {
    await handleUnauthorized();
    throw new Error("需要登录");
  }
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }
  queryCache.clear();
  bundledQueryCache.clear();
  return response.json();
}

function getVisibleColumns() {
  try {
    return { ...DEFAULT_VISIBLE_COLUMNS, ...JSON.parse(localStorage.getItem(STORAGE_KEYS.visibleColumns) || "{}") };
  } catch (_) {
    return { ...DEFAULT_VISIBLE_COLUMNS };
  }
}

function persistVisibleColumns(visibleColumns) {
  localStorage.setItem(STORAGE_KEYS.visibleColumns, JSON.stringify(visibleColumns));
}

function applyColumnVisibility() {
  const visibleColumns = getVisibleColumns();
  document.querySelectorAll("[data-column]").forEach((node) => {
    const key = node.getAttribute("data-column");
    node.classList.toggle("hidden", visibleColumns[key] === false);
  });
  columnSettingInputs.forEach((input) => {
    input.checked = visibleColumns[input.dataset.column] !== false;
  });
}

function renderDetails(items = []) {
  if (!items.length) {
    detailsBody.innerHTML = `<tr><td colspan="14" class="table-empty">当前条件下无结果。</td></tr>`;
    return;
  }
  detailsBody.innerHTML = items.map((item) => {
    const quotaCell = formatCell(item.quota, true);
    const costCell = formatCell(item.cost_total, true);
    const promptTokensCell = formatCell(item.pure_prompt_tokens, true);
    const inputCostCell = formatCell(item.cost_input, true);
    const completionTokensCell = formatCell(item.completion_tokens, true);
    const outputCostCell = formatCell(item.cost_output, true);
    const cacheTokensCell = formatCell(item.cache_tokens, true);
    const cacheCostCell = formatCell(item.cost_cache_read, true);
    const cacheWriteTokensCell = formatCell(item.cache_write_tokens_total, true);
    const cacheWriteCostCell = formatCell(item.cost_cache_write, true);
    return `
      <tr>
        <td data-column="id">${item.id}</td>
        <td data-column="created_at">${new Date(item.created_at * 1000).toLocaleString()}</td>
        <td data-column="token_name">${item.token_name ?? ""}</td>
        <td data-column="model_name">${item.model_name ?? ""}</td>
        <td data-column="quota" class="numeric ${quotaCell.className}">${quotaCell.text}</td>
        <td data-column="cost_total" class="numeric ${costCell.className}">${costCell.text}</td>
        <td data-column="pure_prompt_tokens" class="numeric ${promptTokensCell.className}">${promptTokensCell.text}</td>
        <td data-column="cost_input" class="numeric ${inputCostCell.className}">${inputCostCell.text}</td>
        <td data-column="completion_tokens" class="numeric ${completionTokensCell.className}">${completionTokensCell.text}</td>
        <td data-column="cost_output" class="numeric ${outputCostCell.className}">${outputCostCell.text}</td>
        <td data-column="cache_tokens" class="numeric ${cacheTokensCell.className}">${cacheTokensCell.text}</td>
        <td data-column="cost_cache_read" class="numeric ${cacheCostCell.className}">${cacheCostCell.text}</td>
        <td data-column="cache_write_tokens_total" class="numeric ${cacheWriteTokensCell.className}">${cacheWriteTokensCell.text}</td>
        <td data-column="cost_cache_write" class="numeric ${cacheWriteCostCell.className}">${cacheWriteCostCell.text}</td>
      </tr>`;
  }).join("");
  applyColumnVisibility();
}

function getCurrentFilterState() {
  return {
    source_id: sourceSelect.value,
    token_name: tokenInput.value,
    model_name: modelNameInput.value,
    username: usernameInput.value,
    group_name: groupNameInput.value,
    channel_id: channelIdInput.value,
    request_id: requestIdInput.value,
    ip: ipInput.value,
    start_time: startTimeInput.value,
    end_time: endTimeInput.value,
  };
}

function saveFilterState() {
  localStorage.setItem(STORAGE_KEYS.savedFilter, JSON.stringify(getCurrentFilterState()));
}

function restoreFilterState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEYS.savedFilter) || "{}");
    sourceSelect.value = saved.source_id || sourceSelect.value;
    tokenInput.value = saved.token_name || "";
    modelNameInput.value = saved.model_name || "";
    usernameInput.value = saved.username || "";
    groupNameInput.value = saved.group_name || "";
    channelIdInput.value = saved.channel_id || "";
    requestIdInput.value = saved.request_id || "";
    ipInput.value = saved.ip || "";
    startTimeInput.value = saved.start_time || startTimeInput.value;
    endTimeInput.value = saved.end_time || endTimeInput.value;
  } catch (_) {}
}

function persistRecentSource() {
  localStorage.setItem(STORAGE_KEYS.recentSource, sourceSelect.value || "");
}

function restoreRecentSource() {
  const recentSource = localStorage.getItem(STORAGE_KEYS.recentSource) || "";
  if (recentSource) sourceSelect.value = recentSource;
}

function setTheme(theme) {
  document.body.classList.toggle("dark-theme", theme === "dark");
  localStorage.setItem(STORAGE_KEYS.theme, theme);
}

function restoreTheme() {
  setTheme(localStorage.getItem(STORAGE_KEYS.theme) || "light");
}

function getQueryParams() {
  const params = new URLSearchParams();
  const state = getCurrentFilterState();
  Object.entries(state).forEach(([key, value]) => {
    if (!value) return;
    if (typeof value === "string" && value.trim()) params.set(key, value.trim());
  });
  if (state.start_time) params.set("start_time", localInputToUnix(state.start_time));
  if (state.end_time) params.set("end_time", localInputToUnix(state.end_time));
  params.set("page", String(currentPage));
  params.set("page_size", String(currentPageSize));
  params.set("order_by", currentSortField);
  params.set("order_dir", currentSortDir);
  return params;
}

function updatePagination(details = {}) {
  const total = Number(details.total || 0);
  const page = Number(details.page || currentPage || 1);
  const pageSize = Number(details.page_size || currentPageSize || 20);
  currentPage = page;
  currentPageSize = pageSize;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  pageInfo.textContent = `第 ${page} / ${totalPages} 页`;
  prevPageButton.disabled = page <= 1;
  nextPageButton.disabled = page >= totalPages;
  pageSizeSelect.value = String(pageSize);
}

async function loadTokenSuggestions() {
  tokenSuggestions.innerHTML = "";
  if (!sourceSelect.value) return;
  try {
    const data = await fetchJson(`/api/meta/tokens?source_id=${encodeURIComponent(sourceSelect.value)}&limit=50`);
    (data?.data?.items || []).forEach((item) => {
      const option = document.createElement("option");
      option.value = item.token_name;
      tokenSuggestions.appendChild(option);
    });
  } catch (_) {}
}

function setChartLoading() {
  chartsMeta.textContent = "查询中";
  [chartCostTrend, chartRequestTrend, chartCostStack, chartModelRanking, chartModelRequestRanking, chartGroupRanking, chartChannelRanking, chartCacheSavings].forEach((container) => {
    container.innerHTML = `<div class="chart-empty">加载中...</div>`;
  });
}

function applyFilterPatch(patch) {
  if (patch.model_name !== undefined) modelNameInput.value = patch.model_name;
  if (patch.group_name !== undefined) groupNameInput.value = patch.group_name;
  if (patch.channel_id !== undefined) channelIdInput.value = patch.channel_id;
  if (patch.request_id !== undefined) requestIdInput.value = patch.request_id;
}

function renderLineChart(container, points, valueKey, labelFormatter) {
  if (!points.length) {
    container.innerHTML = `<div class="chart-empty">当前条件下无图表数据。</div>`;
    return;
  }
  const values = points.map((point) => Number(point[valueKey] || 0));
  const maxValue = Math.max(...values, 1);
  const width = 520;
  const height = 220;
  const paddingX = 20;
  const paddingTop = 18;
  const paddingBottom = 30;
  const usableWidth = width - paddingX * 2;
  const usableHeight = height - paddingTop - paddingBottom;
  const step = points.length > 1 ? usableWidth / (points.length - 1) : 0;
  const polyline = points.map((point, index) => {
    const x = paddingX + index * step;
    const value = Number(point[valueKey] || 0);
    const y = paddingTop + usableHeight - (value / maxValue) * usableHeight;
    return `${x},${y}`;
  }).join(" ");
  const circles = points.map((point, index) => {
    const x = paddingX + index * step;
    const value = Number(point[valueKey] || 0);
    const y = paddingTop + usableHeight - (value / maxValue) * usableHeight;
    return `<circle class="chart-point chart-filter-point" data-bucket="${point.bucket_label}" cx="${x}" cy="${y}" r="3"></circle>`;
  }).join("");
  const labels = points.map((point, index) => {
    if (points.length > 8 && index % Math.ceil(points.length / 8) !== 0 && index !== points.length - 1) return "";
    const x = paddingX + index * step;
    return `<text class="chart-label" x="${x}" y="${height - 8}" text-anchor="middle">${point.bucket_label}</text>`;
  }).join("");
  container.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" class="line-chart-svg" preserveAspectRatio="none">
      <line class="chart-axis" x1="${paddingX}" y1="${height - paddingBottom}" x2="${width - paddingX}" y2="${height - paddingBottom}"></line>
      <line class="chart-axis" x1="${paddingX}" y1="${paddingTop}" x2="${paddingX}" y2="${height - paddingBottom}"></line>
      <polyline class="chart-line" points="${polyline}"></polyline>
      ${circles}
      ${labels}
      <text class="chart-label" x="${paddingX}" y="${paddingTop + 4}">${labelFormatter(maxValue)}</text>
    </svg>`;
  container.querySelectorAll(".chart-filter-point").forEach((pointNode) => {
    pointNode.addEventListener("click", async () => {
      const bucket = pointNode.dataset.bucket || "";
      if (!bucket || !/^\d{4}-\d{2}-\d{2}$/.test(bucket)) return;
      startTimeInput.value = `${bucket}T00:00`;
      endTimeInput.value = `${bucket}T23:59`;
      currentPage = 1;
      await runQuery();
    });
  });
}

function renderRankingChart(container, items, formatter, valueKey = "actual_cost_total", patchField = null) {
  if (!items.length) {
    container.innerHTML = `<div class="chart-empty">当前条件下无排行数据。</div>`;
    return;
  }
  const maxValue = Math.max(...items.map((item) => Number(item[valueKey] || 0)), 1);
  container.innerHTML = `<div class="ranking-list">${items.map((item) => {
    const value = Number(item[valueKey] || 0);
    const width = Math.max(2, (value / maxValue) * 100);
    return `<div class="ranking-item" data-name="${item.name}" data-patch-field="${patchField || ""}">
      <div class="ranking-name">${item.name}</div>
      <div class="ranking-bar"><div class="ranking-fill" style="width:${width}%"></div></div>
      <div class="ranking-value">${formatter(value)}</div>
    </div>`;
  }).join("")}</div>`;
  if (patchField) {
    container.querySelectorAll(".ranking-item").forEach((node) => {
      node.addEventListener("click", async () => {
        const name = node.dataset.name || "";
        if (!name || name === "其他") return;
        if (patchField === "channel_id") applyFilterPatch({ channel_id: name });
        if (patchField === "model_name") applyFilterPatch({ model_name: name });
        if (patchField === "group_name") applyFilterPatch({ group_name: name });
        currentPage = 1;
        await runQuery();
      });
    });
  }
}

function renderStackedChart(container, points) {
  if (!points.length) {
    container.innerHTML = `<div class="chart-empty">当前条件下无构成数据。</div>`;
    return;
  }
  const visiblePoints = points.slice(-8);
  container.innerHTML = `<div class="stack-chart">${visiblePoints.map((point) => {
    const input = Number(point.input_cost_total || 0);
    const output = Number(point.output_cost_total || 0);
    const cacheRead = Number(point.cache_read_cost_total || 0);
    const cacheWrite = Number(point.cache_write_cost_total || 0);
    const fixed = Number(point.fixed_cost_total || 0);
    const total = Math.max(input + output + cacheRead + cacheWrite + fixed, 1);
    return `<div class="stack-row">
      <div class="stack-label">${point.bucket_label}</div>
      <div class="stack-track">
        <div class="stack-segment-input" style="width:${(input / total) * 100}%"></div>
        <div class="stack-segment-output" style="width:${(output / total) * 100}%"></div>
        <div class="stack-segment-cache-read" style="width:${(cacheRead / total) * 100}%"></div>
        <div class="stack-segment-cache-write" style="width:${(cacheWrite / total) * 100}%"></div>
        <div class="stack-segment-fixed" style="width:${(fixed / total) * 100}%"></div>
      </div>
      <div class="stack-value">${formatNumeric(total)}</div>
    </div>`;
  }).join("")}</div>`;
}

function renderCharts(charts = {}) {
  const costTrend = Array.isArray(charts.cost_trend) ? charts.cost_trend : [];
  const requestTrend = Array.isArray(charts.request_trend) ? charts.request_trend : [];
  renderLineChart(chartCostTrend, costTrend, "actual_cost_total", (value) => formatNumeric(value));
  renderLineChart(chartRequestTrend, requestTrend, "request_count", (value) => formatNumeric(value, 0));
  renderStackedChart(chartCostStack, Array.isArray(charts.stacked_cost_trend) ? charts.stacked_cost_trend : []);
  renderRankingChart(chartModelRanking, charts.top_models || [], (value) => formatNumeric(value), "actual_cost_total", "model_name");
  renderRankingChart(chartModelRequestRanking, charts.top_models || [], (value) => formatNumeric(value, 0), "request_count", "model_name");
  renderRankingChart(chartGroupRanking, charts.top_groups || [], (value) => formatNumeric(value), "actual_cost_total", "group_name");
  renderRankingChart(chartChannelRanking, charts.top_channels || [], (value) => formatNumeric(value), "actual_cost_total", "channel_id");
  renderLineChart(chartCacheSavings, costTrend, "cache_saving_total", (value) => formatNumeric(value));
  const start = localInputToUnix(startTimeInput.value);
  const end = localInputToUnix(endTimeInput.value);
  const spanDays = start && end ? Math.floor((Number(end) - Number(start)) / 86400) : 0;
  chartsMeta.textContent = charts.granularity ? `粒度: ${charts.granularity}${spanDays > 31 ? "，时间跨度较大" : ""}` : "未查询";
}

async function exportChartsAsPng() {
  const target = document.querySelector(".charts-grid");
  if (!target) return;
  const serializer = new XMLSerializer();
  const clone = target.cloneNode(true);
  clone.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
  const html = serializer.serializeToString(clone);
  const width = target.scrollWidth || 1200;
  const height = target.scrollHeight || 800;
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
      <foreignObject width="100%" height="100%">${html}</foreignObject>
    </svg>`;
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    ctx.fillStyle = getComputedStyle(document.body).backgroundColor || "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0);
    URL.revokeObjectURL(url);
    canvas.toBlob((pngBlob) => {
      if (!pngBlob) return;
      const a = document.createElement("a");
      a.href = URL.createObjectURL(pngBlob);
      a.download = "charts-snapshot.png";
      a.click();
    });
  };
  img.src = url;
}

async function loadHealth() {
  healthBadge.textContent = "加载中";
  healthBadge.className = "badge badge-muted";
  try {
    const data = await fetchJson("/api/health");
    setHealthState(Boolean(data.ok));
    healthOutput.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    setHealthState(false);
    healthOutput.textContent = `请求失败: ${String(error)}`;
  }
}

async function loadAuthStatus() {
  const data = await fetchJson(`/api/auth/status?_=${Date.now()}`, { bypassCache: true, allowUnauthorized: true });
  authState = {
    enabled: Boolean(data?.data?.enabled),
    authenticated: Boolean(data?.data?.authenticated),
    username: data?.data?.username || "",
    allow_basic: Boolean(data?.data?.allow_basic),
    public_health: Boolean(data?.data?.public_health),
  };
  updateAuthUi();
  return authState;
}

async function ensureProtectedContentLoaded(force = false) {
  if (isAuthLocked()) return;
  if (protectedBootstrapped && !force) return;
  await loadSources();
  protectedBootstrapped = true;
}

async function loadSources() {
  if (isAuthLocked()) {
    resetProtectedView("鉴权已启用，请先登录。");
    return;
  }
  try {
    const data = await fetchJson("/api/sources");
    const items = Array.isArray(data?.data?.items) ? data.data.items : [];
    sourceCapabilities = data?.data?.capabilities || {};
    sourcesCount.textContent = String(items.length);
    sourcesList.innerHTML = "";
    sourceSelect.innerHTML = "";
    if (!items.length) {
      sourcesEmpty.style.display = "block";
      sourceSelect.innerHTML = `<option value="">无可用数据源</option>`;
      return;
    }
    sourcesEmpty.style.display = "none";
    items.forEach((item) => {
      sourcesList.appendChild(renderSourceCard(item));
      const option = document.createElement("option");
      option.value = item.source_id;
      option.textContent = item.source_name;
      sourceSelect.appendChild(option);
    });
    restoreRecentSource();
    scanLocalConfigsButton.disabled = !Boolean(sourceCapabilities.enable_local_import);
    await loadTokenSuggestions();
  } catch (error) {
    sourcesCount.textContent = "!";
    sourcesEmpty.style.display = "block";
    sourcesEmpty.textContent = `加载数据源失败: ${String(error)}`;
  }
}

async function runQuery() {
  if (isAuthLocked()) {
    detailsMeta.textContent = "请先登录";
    chartsMeta.textContent = "请先登录";
    return;
  }
  const params = getQueryParams();
  if (!params.get("source_id")) {
    detailsMeta.textContent = "请先选择数据源";
    chartsMeta.textContent = "请先选择数据源";
    return;
  }
  persistRecentSource();
  detailsMeta.textContent = "查询中";
  setChartLoading();
  exportLink.href = `/api/export/token-cost.csv?${params.toString()}`;
  exportXlsxLink.href = `/api/export/token-cost.xlsx?${params.toString()}`;

  try {
    const summaryParams = new URLSearchParams(params);
    summaryParams.delete("page");
    summaryParams.delete("page_size");
    summaryParams.delete("order_by");
    summaryParams.delete("order_dir");
    const summaryBundleKey = `bundle:${summaryParams.toString()}`;
    let summary;
    let charts;
    if (bundledQueryCache.has(summaryBundleKey)) {
      ({ summary, charts } = bundledQueryCache.get(summaryBundleKey));
    } else {
      const [summaryResult, chartsResult] = await Promise.all([
        fetchJson(`/api/stats/token-cost-summary?${summaryParams.toString()}`),
        fetchJson(`/api/stats/token-cost-charts?${summaryParams.toString()}`),
      ]);
      summary = summaryResult?.data ?? {};
      charts = chartsResult?.data ?? {};
      bundledQueryCache.set(summaryBundleKey, { summary, charts });
    }
    const detailsResult = await fetchJson(`/api/stats/token-cost-details?${params.toString()}`);
    const details = detailsResult?.data ?? {};
    fillSummary(summary);
    renderDetails(details.items ?? []);
    updatePagination(details);
    renderCharts(charts);
    detailsMeta.textContent = `共 ${details.total ?? 0} 条结果`;
  } catch (error) {
    detailsMeta.textContent = "查询失败";
    chartsMeta.textContent = "查询失败";
    detailsBody.innerHTML = `<tr><td colspan="14" class="table-empty">查询失败: ${String(error)}</td></tr>`;
    renderCharts({});
  }
}

async function saveSourceFromUri(event) {
  event.preventDefault();
  if (isAuthLocked()) {
    sourceSaveOutput.textContent = "请先登录后再保存数据源。";
    return;
  }
  sourceSaveOutput.textContent = "正在测试并保存 URI 数据源...";
  try {
    const importResult = await fetchJsonWithBody("/api/sources/import-uri", "POST", {
      source_name: uriSourceNameInput.value.trim(),
      uri: sourceUriInput.value.trim(),
    });
    const source = importResult?.data?.source;
    if (!source) throw new Error("导入结果缺少 source 数据");
    const parsed = new URL(sourceUriInput.value.trim());
    await fetchJsonWithBody("/api/sources", "POST", { ...source, password: parsed.password });
    sourceSaveOutput.textContent = JSON.stringify(importResult, null, 2);
    await loadSources();
  } catch (error) {
    sourceSaveOutput.textContent = `URI 导入失败: ${String(error)}`;
  }
}

async function saveSourceManual(event) {
  event.preventDefault();
  if (isAuthLocked()) {
    sourceSaveOutput.textContent = "请先登录后再保存数据源。";
    return;
  }
  sourceSaveOutput.textContent = "正在保存手工数据源...";
  try {
    const dbType = manualDbTypeInput.value || "mysql";
    const payload = {
      source_name: manualSourceNameInput.value.trim(),
      host: manualHostInput.value.trim(),
      port: Number(manualPortInput.value || 3306),
      database: manualDatabaseInput.value.trim(),
      user: manualUserInput.value.trim(),
      password: manualPasswordInput.value,
      db_type: dbType,
      charset: dbType === "postgres" ? "" : "utf8mb4",
      timezone: "Asia/Shanghai",
      readonly: true,
    };
    const testResult = await fetchJsonWithBody("/api/sources/test", "POST", {
      source_id: payload.source_name.toLowerCase().replace(" ", "-"),
      ...payload,
    });
    const result = await fetchJsonWithBody("/api/sources", "POST", payload);
    sourceSaveOutput.textContent = JSON.stringify({ test_result: testResult.data, save_result: result.data }, null, 2);
    await loadSources();
  } catch (error) {
    sourceSaveOutput.textContent = `手工保存失败: ${String(error)}`;
  }
}

async function deleteSource(item) {
  if (isAuthLocked()) {
    sourceSaveOutput.textContent = "请先登录后再删除数据源。";
    return;
  }
  const confirmed = window.confirm(`确认删除数据源 "${item.source_name}" (${item.source_id}) 吗？`);
  if (!confirmed) return;
  sourceSaveOutput.textContent = `正在删除数据源 ${item.source_name}...`;
  try {
    const result = await fetchJsonWithMethod(`/api/sources/${encodeURIComponent(item.source_id)}`, "DELETE");
    if (sourceSelect.value === item.source_id) {
      localStorage.removeItem(STORAGE_KEYS.recentSource);
      fillSummary({});
      detailsMeta.textContent = "当前数据源已删除";
      chartsMeta.textContent = "当前数据源已删除";
      detailsBody.innerHTML = `<tr><td colspan="14" class="table-empty">当前数据源已删除，请重新选择数据源。</td></tr>`;
      renderCharts({});
      updatePagination({ page: 1, page_size: currentPageSize, total: 0 });
    }
    sourceSaveOutput.textContent = JSON.stringify(result, null, 2);
    await loadSources();
  } catch (error) {
    sourceSaveOutput.textContent = `删除数据源失败: ${String(error)}`;
  }
}

async function scanLocalConfigs() {
  if (isAuthLocked()) {
    sourceSaveOutput.textContent = "请先登录后再扫描本机配置。";
    return;
  }
  sourceSaveOutput.textContent = "正在扫描本机配置...";
  try {
    const result = await fetchJsonWithBody("/api/sources/import-local", "POST", {});
    sourceSaveOutput.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    sourceSaveOutput.textContent = `本机扫描失败: ${String(error)}`;
  }
}

async function handleLogin(event) {
  event.preventDefault();
  authMessage.textContent = "正在登录...";
  try {
    const data = await fetchJsonWithBody(
      "/api/auth/login",
      "POST",
      {
        username: authUsernameInput.value.trim(),
        password: authPasswordInput.value,
      },
      { allowUnauthorized: true },
    );
    authPasswordInput.value = "";
    queryCache.clear();
    bundledQueryCache.clear();
    authMessage.textContent = data?.message || "登录成功";
    await loadAuthStatus();
    await ensureProtectedContentLoaded(true);
  } catch (error) {
    authMessage.textContent = `登录失败: ${String(error)}`;
  }
}

async function handleLogout() {
  try {
    await fetchJsonWithBody("/api/auth/logout", "POST", {}, { allowUnauthorized: true });
  } catch (_) {}
  queryCache.clear();
  bundledQueryCache.clear();
  protectedBootstrapped = false;
  authState = {
    ...authState,
    enabled: true,
    authenticated: false,
    username: "",
  };
  updateAuthUi();
}

document.getElementById("refresh-health").addEventListener("click", loadHealth);
document.getElementById("refresh-sources").addEventListener("click", loadSources);
authLoginForm.addEventListener("submit", handleLogin);
authLogoutButton.addEventListener("click", handleLogout);
sourceUriForm.addEventListener("submit", saveSourceFromUri);
sourceManualForm.addEventListener("submit", saveSourceManual);
scanLocalConfigsButton.addEventListener("click", scanLocalConfigs);
exportChartsImageButton.addEventListener("click", exportChartsAsPng);
manualDbTypeInput.addEventListener("change", () => {
  if (manualDbTypeInput.value === "postgres" && manualPortInput.value === "3306") {
    manualPortInput.value = "5432";
  } else if ((manualDbTypeInput.value === "mysql" || manualDbTypeInput.value === "mariadb") && manualPortInput.value === "5432") {
    manualPortInput.value = "3306";
  }
});

columnSettingsToggle.addEventListener("click", () => columnSettingsPanel.classList.toggle("hidden"));
columnSettingInputs.forEach((input) => {
  input.addEventListener("change", () => {
    const visibleColumns = getVisibleColumns();
    visibleColumns[input.dataset.column] = input.checked;
    persistVisibleColumns(visibleColumns);
    applyColumnVisibility();
  });
});

themeToggleButton.addEventListener("click", () => {
  setTheme(document.body.classList.contains("dark-theme") ? "light" : "dark");
});
saveFilterButton.addEventListener("click", () => {
  saveFilterState();
  detailsMeta.textContent = "筛选已保存";
});
restoreFilterButton.addEventListener("click", async () => {
  restoreFilterState();
  await loadTokenSuggestions();
  detailsMeta.textContent = "筛选已恢复";
});

queryForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  currentPage = 1;
  await runQuery();
});

resetFormButton.addEventListener("click", () => {
  tokenInput.value = "";
  modelNameInput.value = "";
  usernameInput.value = "";
  groupNameInput.value = "";
  channelIdInput.value = "";
  requestIdInput.value = "";
  ipInput.value = "";
  currentSortField = "created_at";
  currentSortDir = "desc";
  currentPage = 1;
  bundledQueryCache.clear();
  setDefaultTimes();
  fillSummary({});
  detailsMeta.textContent = "已重置";
  chartsMeta.textContent = "已重置";
  detailsBody.innerHTML = `<tr><td colspan="14" class="table-empty">请先选择数据源并执行查询。</td></tr>`;
  updatePagination({ page: 1, page_size: currentPageSize, total: 0 });
  renderCharts({});
  applyColumnVisibility();
});

sourceSelect.addEventListener("change", async () => {
  persistRecentSource();
  await loadTokenSuggestions();
});

sortButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const field = button.dataset.sortField;
    if (!field) return;
    if (currentSortField === field) currentSortDir = currentSortDir === "desc" ? "asc" : "desc";
    else {
      currentSortField = field;
      currentSortDir = "desc";
    }
    currentPage = 1;
    await runQuery();
  });
});

prevPageButton.addEventListener("click", async () => {
  if (currentPage <= 1) return;
  currentPage -= 1;
  await runQuery();
});

nextPageButton.addEventListener("click", async () => {
  currentPage += 1;
  await runQuery();
});

pageSizeSelect.addEventListener("change", async () => {
  currentPageSize = Number(pageSizeSelect.value || 20);
  currentPage = 1;
  await runQuery();
});

restoreTheme();
setDefaultTimes();
restoreFilterState();
fillSummary({});
renderCharts({});
updatePagination({ page: 1, page_size: currentPageSize, total: 0 });
applyColumnVisibility();
loadHealth();

(async () => {
  try {
    await loadAuthStatus();
    await ensureProtectedContentLoaded();
  } catch (error) {
    authSessionBadge.className = "badge badge-warning";
    authSessionBadge.textContent = "鉴权检查失败";
    authGate.classList.remove("hidden");
    authMessage.textContent = `鉴权初始化失败: ${String(error)}`;
    resetProtectedView("鉴权初始化失败，请检查服务日志。");
  }
})();
