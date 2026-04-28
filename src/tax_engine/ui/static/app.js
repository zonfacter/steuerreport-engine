const el = (id) => document.getElementById(id);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = {
  unmatchedOutbound: [],
  unmatchedInbound: [],
  transferLedger: [],
  legacyHntTransfers: null,
  issues: [],
  lotRows: [],
  taxLines: [],
  derivativeLines: [],
  reportFiles: [],
  processingJobs: [],
  processOptions: null,
  preflight: null,
  processingJobsLimit: 25,
  processingJobsOffset: 0,
  processingJobsMode: "default",
  processingJobsSort: "updated_at",
  processingJobsSortDir: "desc",
  processingJobsAutoRefreshTimer: null,
  processingJobsAutoRefreshSec: "",
  processingJobsCount: 0,
  taxEventOverrides: [],
  integrationRows: [],
  importSources: [],
  importJobs: [],
  selectedImportJob: null,
  dashboard: null,
  admin: {
    settings: [],
    runtime: null,
    aliases: [],
    ignoredTokens: [],
    backfillService: null,
  },
  walletGroups: [],
  selectedWalletGroupId: "",
  charts: {},
  fx: {
    usdToEur: 1,
    source: "fallback",
  },
  ui: {
    displayCurrency: "eur",
    expertMode: false,
  },
  paging: {
    tokenPage: 1,
    transferPage: 1,
    issuePage: 1,
    taxPage: 1,
    derivPage: 1,
  },
  workflow: {
    importDone: false,
    reconcileDone: false,
    processDone: false,
    reviewDone: false,
    nextStep: "1",
    nextLabel: "Zu Import",
  },
  reviewGates: null,
};

const STEP_LABELS = {
  "1": "Integrationen",
  "2": "Transfer Review",
  "3": "Steuerlauf",
  "4": "Dashboard",
  "5": "Admin",
};

const REVIEW_LABELS = {
  cockpit: "Cockpit",
  performance: "Performance",
  holdings: "Bestände",
  mining: "Mining",
  trading: "Trading",
  transfers: "Transfers",
  tax: "Steuer",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

const numberFmt = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 8 });
const numberFmt2 = new Intl.NumberFormat("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function toNumber(value) {
  if (typeof value === "string") {
    const raw = value.trim();
    if (!raw) return 0;
    const normalized = raw.includes(",") && !raw.includes(".")
      ? raw.replace(/\./g, "").replace(",", ".")
      : raw.replace(/,/g, "");
    const n = Number(normalized);
    return Number.isFinite(n) ? n : 0;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatQty(value) {
  return numberFmt.format(toNumber(value));
}

function formatMoney(value) {
  return numberFmt2.format(toNumber(value));
}

function formatCurrency(value, currency = "EUR") {
  const code = String(currency || "EUR").toUpperCase();
  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency: code,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(toNumber(value));
}

function formatInt(value) {
  return new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 }).format(toNumber(value));
}

function shortAddress(value) {
  const raw = String(value || "").trim();
  if (raw.length <= 18) return raw;
  return `${raw.slice(0, 8)}...${raw.slice(-6)}`;
}

function shortText(value, maxLength = 60) {
  const raw = String(value || "").trim();
  if (raw.length <= maxLength) return raw;
  return `${raw.slice(0, Math.max(0, maxLength - 3))}...`;
}

function rulesetForYear(year) {
  const y = Number(year || 2026);
  const safeYear = Number.isFinite(y) ? Math.min(Math.max(Math.floor(y), 2020), 2026) : 2026;
  const ruleset = (state.processOptions?.rulesets || []).find((item) => {
    const fromYear = Number(String(item.valid_from || "").slice(0, 4));
    const toYear = Number(String(item.valid_to || "").slice(0, 4));
    return fromYear <= safeYear && safeYear <= toYear && String(item.jurisdiction || "") === "DE";
  });
  if (ruleset?.ruleset_id) return String(ruleset.ruleset_id);
  return `DE-${safeYear}-v1.0`;
}

function syncTaxRunSelection() {
  const year = String(el("taxYear")?.value || "2026");
  const ruleset = rulesetForYear(year);
  if (el("rulesetId")) el("rulesetId").value = ruleset;
  const host = el("taxRunPreview");
  if (!host) return;
  const exemption = Number(year) >= 2024 ? "1.000 EUR Freigrenze" : "600 EUR Freigrenze";
  host.innerHTML = `
    <span><strong>Jurisdiktion:</strong> Deutschland</span>
    <span><strong>FIFO:</strong> aktiv</span>
    <span><strong>Haltefrist:</strong> 12 Monate</span>
    <span><strong>SO:</strong> ${exemption}</span>
    <span><strong>Ruleset:</strong> ${ruleset}</span>
  `;
}

function processRequestPayload() {
  syncTaxRunSelection();
  return {
    tax_year: Number(el("taxYear")?.value || "2026"),
    ruleset_id: el("rulesetId")?.value.trim() || rulesetForYear(el("taxYear")?.value || "2026"),
    config: {
      tax_method: el("taxMethod")?.value || "fifo",
      calculation_mode: "global",
      validation_flags: {
        short_sell_guard: true,
        transfer_check: true,
        holding_period_check: true,
      },
    },
  };
}

function renderPreflight(data) {
  state.preflight = data || null;
  const panel = el("preflightPanel");
  if (!panel) return;
  const blockers = data?.blockers || [];
  const warnings = data?.warnings || [];
  const counts = data?.counts || {};
  panel.className = `notice ${blockers.length ? "notice-error" : warnings.length ? "notice-warn" : "notice-ok"}`;
  const status = data?.allow_run ? "Preflight bestanden" : "Preflight blockiert";
  const details = [
    `${formatInt(counts.tax_year_events || 0)} Events im Steuerjahr`,
    `${formatInt(counts.unmatched_transfers || 0)} offene Transfers`,
    `${formatInt(counts.high_severity_open || 0)} High-Issues`,
    `${formatInt(counts.unresolved_valuation_events || 0)} Bewertungswarnungen`,
  ];
  const renderAction = (item, idx, kind) => {
    if (!item?.action) return "";
    return `
      <button
        class="guided-action"
        data-preflight-kind="${escapeHtml(kind)}"
        data-preflight-index="${idx}"
        type="button"
      >${escapeHtml(item.action.label || "Öffnen")}</button>
    `;
  };
  const blockerHtml = blockers.length
    ? `<div><strong>Blocker:</strong> ${blockers.map((item) => escapeHtml(item.message || item.code)).join(" · ")}</div>
       <div class="guided-actions">${blockers.map((item, idx) => renderAction(item, idx, "blockers")).join("")}</div>`
    : "";
  const warningHtml = warnings.length
    ? `<div><strong>Warnungen:</strong> ${warnings.map((item) => escapeHtml(item.message || item.code)).join(" · ")}</div>
       <div class="guided-actions">${warnings.map((item, idx) => renderAction(item, idx, "warnings")).join("")}</div>`
    : "";
  panel.innerHTML = `
    <div><strong>${escapeHtml(status)}</strong> · ${details.map(escapeHtml).join(" · ")}</div>
    ${blockerHtml}
    ${warningHtml}
  `;
}

function applyPreflightAction(action) {
  if (!action) return;
  const step = String(action.target_step || "");
  const review = String(action.target_review_tab || "");
  if (step) {
    guardedSwitchStep(step);
  }
  if (step === "4" && review) {
    switchReviewTab(review);
  }
  if (Object.prototype.hasOwnProperty.call(action, "issue_search") && el("reviewIssueSearch")) {
    el("reviewIssueSearch").value = action.issue_search || "";
    savePref("field.reviewIssueSearch", el("reviewIssueSearch").value);
    state.paging.issuePage = 1;
    renderIssues(state.issues);
    el("btnIssuesLoad")?.click();
  }
  if (Object.prototype.hasOwnProperty.call(action, "issue_status") && el("reviewIssueStatus")) {
    el("reviewIssueStatus").value = action.issue_status || "";
    savePref("field.reviewIssueStatus", el("reviewIssueStatus").value);
    state.paging.issuePage = 1;
    renderIssues(state.issues);
  }
  if (Object.prototype.hasOwnProperty.call(action, "transfer_status") && el("reviewTransferStatus")) {
    el("reviewTransferStatus").value = action.transfer_status || "";
    savePref("field.reviewTransferStatus", el("reviewTransferStatus").value);
    state.paging.transferPage = 1;
    renderTransferLedger(state.transferLedger);
    el("btnReviewTransferLoad")?.click();
  }
  const target = action.target_element_id ? el(action.target_element_id) : null;
  if (target) {
    window.setTimeout(() => {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      target.classList.add("guided-focus");
      window.setTimeout(() => target.classList.remove("guided-focus"), 1800);
    }, 120);
  }
}

async function runPreflight(trigger = null, silent = false) {
  const payload = processRequestPayload();
  const data = await callApi("/api/v1/process/preflight", "POST", payload, trigger, silent);
  if (data?.status !== "success") return null;
  renderPreflight(data.data);
  return data.data;
}

async function loadProcessOptions() {
  const data = await callApi("/api/v1/process/options", "GET", null, null, true);
  if (data?.status !== "success") return;
  state.processOptions = data.data;
  const yearSelect = el("taxYear");
  if (yearSelect && Array.isArray(data.data?.tax_years)) {
    const current = yearSelect.value || String(data.data.default_tax_year || "2026");
    yearSelect.innerHTML = data.data.tax_years
      .map((year) => `<option value="${year}">${year}</option>`)
      .join("");
    yearSelect.value = data.data.tax_years.includes(Number(current)) ? current : String(data.data.default_tax_year || "2026");
  }
  syncTaxRunSelection();
}

function setCsvButtonsDisabled(disabled, reason = "") {
  ["btnTransferCsv", "btnIssuesCsv", "btnTaxCsv", "btnDerivCsv"].forEach((id) => {
    const button = el(id);
    if (!button) return;
    button.disabled = !!disabled;
    if (reason) {
      button.title = reason;
    } else {
      button.removeAttribute("title");
    }
  });
}

function debounce(fn, waitMs = 150) {
  let timer = null;
  return (...args) => {
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), waitMs);
  };
}

function usdToEur(value) {
  return toNumber(value) * toNumber(state.fx.usdToEur || 1);
}

function displayCurrency() {
  const raw = String(state.ui.displayCurrency || "eur").toLowerCase();
  return raw === "usd" ? "usd" : "eur";
}

function convertUsdForDisplay(valueUsd) {
  const usd = toNumber(valueUsd);
  return displayCurrency() === "usd" ? usd : usdToEur(usd);
}

function currencyLabel() {
  return displayCurrency().toUpperCase();
}

function prefKey(name) {
  return `ui.pref.${name}`;
}

function savePref(name, value) {
  try { localStorage.setItem(prefKey(name), String(value)); } catch (_) {}
}

function loadPref(name, fallback = "") {
  try {
    const value = localStorage.getItem(prefKey(name));
    return value == null ? fallback : value;
  } catch (_) {
    return fallback;
  }
}

function saveColumnPrefs(tableId) {
  const prefs = {};
  document.querySelectorAll(`.col-toggle[data-table-id="${tableId}"]`).forEach((input) => {
    prefs[input.dataset.colKey] = !!input.checked;
  });
  savePref(`cols.${tableId}`, JSON.stringify(prefs));
}

function loadColumnPrefs(tableId) {
  const raw = loadPref(`cols.${tableId}`, "");
  if (!raw) return {};
  try {
    return JSON.parse(raw) || {};
  } catch (_) {
    return {};
  }
}

function applyTableColumnVisibility(tableId) {
  const table = el(tableId);
  if (!table) return;
  const prefs = loadColumnPrefs(tableId);
  Object.entries(prefs).forEach(([col, enabled]) => {
    table.classList.toggle(`hide-col-${col}`, !enabled);
  });
}

const defaultEvents = [
  { timestamp: "2026-01-01T12:00:00Z", asset: "SOL", event_type: "withdrawal", amount: "10.00" },
  { timestamp: "2026-01-01T12:03:00Z", asset: "SOL", event_type: "deposit", amount: "9.99" },
  { timestamp: "2026-02-01T12:00:00Z", asset: "BTC", side: "buy", amount: "1", price_eur: "100", fee_eur: "1" },
  { timestamp: "2026-02-10T12:00:00Z", asset: "BTC", side: "sell", amount: "0.4", price_eur: "125", fee_eur: "0.5" },
];

function showToast(message, level = "ok") {
  const toast = el("toast");
  toast.className = `toast ${level}`;
  toast.textContent = message;
  toast.classList.remove("hidden");
}

function switchStep(step) {
  $$(".step").forEach((btn) => btn.classList.toggle("active", btn.dataset.step === String(step)));
  $$(".step-panel").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.panel !== String(step)));
  try { localStorage.setItem("ui.step", String(step)); } catch (_) {}
  updateContextPath();
  syncRailState();
  refreshPresetUi();
  if (state.processingJobsAutoRefreshTimer) {
    window.clearInterval(state.processingJobsAutoRefreshTimer);
    state.processingJobsAutoRefreshTimer = null;
  }
  if (String(step) === "4") {
    loadDashboard();
    if (currentJobId()) {
      refreshTaxReviewData(currentJobId(), true);
    }
  }
  if (String(step) === "3") {
    syncProcessJobsAutoRefresh();
    loadProcessJobs(true);
  }
}

function switchAdminTab(tab) {
  $$(".admin-tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.adminTab === tab));
  $$(".admin-panel").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.adminPanel !== tab));
}

function switchReviewTab(tab) {
  $$(".review-tab").forEach((btn) => btn.classList.toggle("active", btn.dataset.reviewTab === tab));
  $$(".review-panel").forEach((panel) => panel.classList.toggle("hidden", panel.dataset.reviewPanel !== tab));
  try { localStorage.setItem("ui.reviewTab", String(tab)); } catch (_) {}
  updateContextPath();
  syncRailState();
  refreshPresetUi();
}

function currentStep() {
  const active = document.querySelector(".step.active");
  return active?.dataset?.step || "1";
}

function currentReviewTab() {
  const active = document.querySelector(".review-tab.active");
  return active?.dataset?.reviewTab || "cockpit";
}

function syncRailState() {
  const step = currentStep();
  const review = currentReviewTab();
  $$(".rail-link").forEach((btn) => {
    const btnStep = btn.dataset.railStep || "";
    const btnReview = btn.dataset.railReview || "";
    const isActive = btnReview
      ? (btnStep === step && btnReview === review)
      : (btnStep === step && !btn.dataset.railReview);
    btn.classList.toggle("active", isActive);
  });
}

function updateContextPath() {
  const step = currentStep();
  const review = currentReviewTab();
  const root = STEP_LABELS[step] || "Import";
  const suffix = step === "4" ? ` / ${REVIEW_LABELS[review] || "Cockpit"}` : "";
  const host = el("contextPath");
  if (host) host.textContent = `Kontext: ${root}${suffix}`;
  updateWorkflowGuide();
  updateStepGuide();
}

function updateStepGuide() {
  const step = currentStep();
  const review = currentReviewTab();
  const title = el("guideTitle");
  const list = el("guideList");
  if (!title || !list) return;
  let steps = [];
  let heading = "Schrittanleitung";
  if (step === "1") {
    heading = "Integrationen: empfohlene Reihenfolge";
    steps = [
      "Lege zuerst Wallet-Gruppen oder einzelne Quellen an.",
      "Lade komplette Historie per API/RPC oder importiere CSV/XLS-Dateien.",
      "Prüfe danach im Dashboard, ob Events, Assets und Werte plausibel sind.",
    ];
  } else if (step === "2") {
    heading = "Review: interne Transfers klären";
    steps = [
      "Starte Auto-Match mit Zeitfenster und Toleranz.",
      "Prüfe Unmatched-Transfers und ergänze ggf. manuelle Matches.",
      "Kontrolliere, dass Haltefristen bei Eigenüberträgen fortgeführt werden.",
    ];
  } else if (step === "3") {
    heading = "Steuerlauf: Berechnung";
    steps = [
      "Steuerjahr, FIFO-Prinzip und Ruleset prüfen.",
      "Process Run starten und Job-ID übernehmen.",
      "Nach Abschluss Steuer-Tab und Review-Gates prüfen.",
    ];
  } else if (step === "4") {
    heading = `Dashboard: ${REVIEW_LABELS[review] || "Cockpit"}`;
    if (review === "performance") {
      steps = [
        "Dashboard aktualisieren und Rollenmodus prüfen.",
        "Snapshot-Zeitraum einstellen und Verlauf beurteilen.",
        "Bei Abweichungen Wallet-Live-Balance laden.",
      ];
    } else if (review === "cockpit") {
      steps = [
        "Cockpit aktualisieren, um Portfolio- und Steuerwerte gemeinsam zu sehen.",
        "SO/EÜR/Termingeschäfte auf Plausibilität prüfen.",
        "Bei Auffälligkeiten direkt in Steuer oder Bestände springen.",
      ];
    } else if (review === "holdings") {
      steps = [
        "Tokenliste filtern/sortieren und Werte in EUR/USD prüfen.",
        "Spam/Aliase per Quick Actions bereinigen.",
        "Lot Aging für steuerliche Haltedauer prüfen.",
      ];
    } else if (review === "mining") {
      steps = [
        "Reward- und Mining-KPIs prüfen.",
        "Unbewertete Rewards oder Data-Credit-Ereignisse im Steuer-Tab klassifizieren.",
        "Bei gewerblicher Einordnung EÜR-relevante Werte getrennt prüfen.",
      ];
    } else if (review === "trading") {
      steps = [
        "Spot- und Bot-Aktivität aggregiert prüfen.",
        "Tax Lines nach Asset und steuerlichem Status filtern.",
        "Bei PnL-Ausreißern Audit-Trace im Steuer-Tab öffnen.",
      ];
    } else if (review === "transfers") {
      steps = [
        "Transfers nach Status und Suchbegriff filtern.",
        "Issues priorisieren und Status aktualisieren.",
        "Gefilterte Tabellen als CSV exportieren.",
      ];
    } else {
      steps = [
        "Tax/Derivative Lines laden und Filter anwenden.",
        "Audit-Trace bei kritischen Zeilen öffnen.",
        "CSV-Exporte erzeugen und mit Steuerberater teilen.",
      ];
    }
  } else {
    heading = "Admin: Konfiguration";
    steps = [
      "Runtime-RPC und FX-Kurs setzen.",
      "Credentials speichern/laden und Test ausführen.",
      "Alias/Ignore-Regeln für stabile Reports pflegen.",
    ];
  }
  title.textContent = heading;
  list.innerHTML = "";
  steps.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    list.appendChild(li);
  });
}

function setExpertMode(on) {
  document.body.classList.toggle("expert-mode", !!on);
  state.ui.expertMode = !!on;
  savePref("expertMode", on ? "1" : "0");
  if (el("uiExpertMode")) el("uiExpertMode").checked = !!on;
}

function setWorkflowStatus(nodeId, done) {
  const node = el(nodeId);
  if (!node) return;
  node.className = done ? "pill pill-ok" : "pill pill-neutral";
  node.textContent = done ? "erledigt" : "offen";
}

function setRailDot(nodeId, done) {
  const node = el(nodeId);
  if (!node) return;
  node.classList.toggle("rail-dot-on", !!done);
  node.classList.toggle("rail-dot-off", !done);
}

function canNavigateToStep(targetStep) {
  // Vereinfachter Flow: Navigation immer zulassen, Workflow bleibt als Empfehlung sichtbar.
  return true;
}

function guardedSwitchStep(targetStep) {
  if (!canNavigateToStep(targetStep)) {
    const label = state.workflow?.nextLabel || "Nächste Aktion";
    showToast(`Bitte zuerst: ${label}`, "warn");
    switchStep(state.workflow?.nextStep || "1");
    return false;
  }
  switchStep(targetStep);
  return true;
}

function updateWorkflowGuide() {
  const totalEvents = Number(state.dashboard?.summary?.total_events || 0);
  const importDone = totalEvents > 0;
  const reconcileDone = state.transferLedger.length > 0 || state.unmatchedOutbound.length > 0 || state.unmatchedInbound.length > 0;
  const processDone = String(el("mStatus")?.textContent || "-") !== "-" || String(currentJobId() || "").length > 0;
  const reviewDone = state.taxLines.length > 0 || state.derivativeLines.length > 0 || state.lotRows.length > 0;

  setWorkflowStatus("wfImportStatus", importDone);
  setWorkflowStatus("wfReconcileStatus", reconcileDone);
  setWorkflowStatus("wfProcessStatus", processDone);
  setWorkflowStatus("wfReviewStatus", reviewDone);
  setRailDot("railDot1", importDone);
  setRailDot("railDot2", reconcileDone);
  setRailDot("railDot3", processDone);
  setRailDot("railDot4", reviewDone);

  let hint = "Verbinde zuerst Wallets, Börsen oder Dateiimporte.";
  if (importDone && !reconcileDone) hint = "Prüfe interne Transfers, damit FIFO-Haltefristen fortgeführt werden.";
  if (importDone && reconcileDone && !processDone) hint = "Starte den Steuerlauf mit passendem Steuerjahr und Ruleset.";
  if (importDone && reconcileDone && processDone) hint = "Prüfe Dashboard, Steuerwerte und Review-Gates.";
  let nextStep = "1";
  let nextLabel = "Quellen verbinden";
  if (importDone && !reconcileDone) {
    nextStep = "2";
    nextLabel = "Transfers prüfen";
  } else if (importDone && reconcileDone && !processDone) {
    nextStep = "3";
    nextLabel = "Steuerlauf starten";
  } else if (importDone && reconcileDone && processDone && !reviewDone) {
    nextStep = "4";
    nextLabel = "Dashboard öffnen";
  } else if (importDone && reconcileDone && processDone && reviewDone) {
    nextStep = "4";
    nextLabel = "Dashboard öffnen";
    hint = "Workflow vollständig. Jetzt Detailprüfung, Exporte und Korrekturen.";
  }
  state.workflow = { importDone, reconcileDone, processDone, reviewDone, nextStep, nextLabel };
  const hintNode = el("workflowHint");
  if (hintNode) hintNode.textContent = hint;
  const subline = el("heroSubline");
  if (subline) subline.textContent = `Arbeitsstatus: ${hint}`;
  const btnA = el("btnNextAction");
  const btnB = el("btnNextActionInline");
  [btnA, btnB].forEach((btn) => {
    if (!btn) return;
    btn.textContent = nextLabel;
    btn.disabled = false;
  });
  const completed = [importDone, reconcileDone, processDone, reviewDone].filter(Boolean).length;
  const pct = Math.round((completed / 4) * 100);
  const bar = el("workflowProgressBar");
  if (bar) bar.style.width = `${pct}%`;
  const progressLabel = el("workflowProgressLabel");
  if (progressLabel) progressLabel.textContent = `${pct}% abgeschlossen`;
}

function runNextAction() {
  const targetStep = state.workflow?.nextStep || "1";
  switchStep(targetStep);
  if (targetStep === "1") {
    el("eventsJson")?.focus();
    return;
  }
  if (targetStep === "2") {
    const btn = el("btnUnmatched");
    if (btn) btn.click();
    return;
  }
  if (targetStep === "3") {
    el("taxYear")?.focus();
    return;
  }
  if (targetStep === "4") {
    switchReviewTab("cockpit");
    const btn = el("btnDashRefresh");
    if (btn) btn.click();
  }
}

function setRailCollapsed(collapsed) {
  const shell = document.querySelector(".app-shell");
  if (!shell) return;
  shell.classList.toggle("rail-collapsed", !!collapsed);
  const btn = el("btnRailToggle");
  if (btn) {
    btn.textContent = collapsed ? "▶" : "◀";
    btn.title = collapsed ? "Navigation ausklappen" : "Navigation einklappen";
  }
  try { localStorage.setItem("ui.railCollapsed", collapsed ? "1" : "0"); } catch (_) {}
}

function currentScopeKey() {
  const step = currentStep();
  if (step !== "4") return `step:${step}`;
  return `step:4:${currentReviewTab()}`;
}

function presetStorageKey(scope) {
  return `ui.presets.${scope}`;
}

function listPresets(scope) {
  try {
    const raw = localStorage.getItem(presetStorageKey(scope));
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_) {
    return {};
  }
}

function savePresets(scope, value) {
  try {
    localStorage.setItem(presetStorageKey(scope), JSON.stringify(value));
  } catch (_) {
    // ignore
  }
}

function collectCurrentViewState() {
  const fields = [
    "uiDisplayCurrency",
    "dashTokenSearch",
    "dashTokenStatusFilter",
    "dashTokenSort",
    "dashShowIgnored",
    "dashTokenPageSize",
    "dashLotAsset",
    "dashLotAsOf",
    "taxFilterAsset",
    "taxFilterStatus",
    "taxPageSize",
    "derivFilterAsset",
    "derivFilterType",
    "derivPageSize",
    "dashSnapshotWindow",
    "reviewTransferSearch",
    "reviewTransferStatus",
    "reviewTransferPageSize",
    "reviewIssueSearch",
    "reviewIssueStatus",
    "reviewIssuePageSize",
  ];
  const fieldValues = {};
  fields.forEach((id) => {
    const node = el(id);
    if (!node) return;
    fieldValues[id] = node.type === "checkbox" ? (node.checked ? "1" : "0") : node.value;
  });
  return {
    denseMode: document.body.classList.contains("dense-table") ? "1" : "0",
    fields: fieldValues,
    cols: {
      dashLiveTokenTable: loadColumnPrefs("dashLiveTokenTable"),
      taxTable: loadColumnPrefs("taxTable"),
    },
  };
}

function applyViewState(view) {
  if (!view || typeof view !== "object") return;
  const dense = String(view.denseMode || "0") === "1";
  document.body.classList.toggle("dense-table", dense);
  if (el("uiDenseMode")) el("uiDenseMode").checked = dense;
  savePref("denseMode", dense ? "1" : "0");
  const fields = view.fields || {};
  Object.entries(fields).forEach(([id, value]) => {
    const node = el(id);
    if (!node) return;
    if (node.type === "checkbox") node.checked = String(value) === "1";
    else node.value = String(value);
    savePref(`field.${id}`, node.type === "checkbox" ? (node.checked ? "1" : "0") : node.value);
  });
  state.ui.displayCurrency = String(el("uiDisplayCurrency")?.value || "eur").toLowerCase();
  if (view.cols?.dashLiveTokenTable) {
    savePref("cols.dashLiveTokenTable", JSON.stringify(view.cols.dashLiveTokenTable));
  }
  if (view.cols?.taxTable) {
    savePref("cols.taxTable", JSON.stringify(view.cols.taxTable));
  }
  document.querySelectorAll(".col-toggle").forEach((input) => {
    const tableId = input.dataset.tableId || "";
    const colKey = input.dataset.colKey || "";
    const prefs = loadColumnPrefs(tableId);
    if (Object.prototype.hasOwnProperty.call(prefs, colKey)) {
      input.checked = !!prefs[colKey];
    }
  });
  applyTableColumnVisibility("dashLiveTokenTable");
  applyTableColumnVisibility("taxTable");
  renderTaxTable();
  renderDerivativeTable();
  const lastTokens = state.dashboard?.last_live_tokens ?? [];
  if (Array.isArray(lastTokens)) renderLiveTokenTable(lastTokens);
  rerenderWalletSnapshotFromState();
}

function refreshPresetUi() {
  const scope = currentScopeKey();
  const presets = listPresets(scope);
  const select = el("uiPresetSelect");
  if (!select) return;
  select.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "-- Preset wählen --";
  select.appendChild(empty);
  Object.keys(presets).sort().forEach((name) => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  });
}

function setApiState(ok) {
  const pill = el("apiState");
  pill.className = ok ? "pill pill-ok" : "pill pill-err";
  pill.textContent = ok ? "API: erreichbar" : "API: nicht erreichbar";
}

function setResponse(json) {
  el("responseOut").textContent = JSON.stringify(json, null, 2);
}

function applyRuntimeDefaults(runtimeData) {
  const solana = runtimeData?.runtime?.solana;
  const fx = runtimeData?.runtime?.fx;
  if (solana) {
    if (solana.rpc_url) el("solRpc").value = solana.rpc_url;
    if (Array.isArray(solana.rpc_fallback_urls)) {
      el("solRpcFallbacks").value = solana.rpc_fallback_urls.join(",");
    }
    if (solana.rpc_url) el("adminRpcUrl").value = solana.rpc_url;
    if (Array.isArray(solana.rpc_fallback_urls)) {
      el("adminRpcFallbacks").value = solana.rpc_fallback_urls.join(",");
    }
  }
  const usdToEur = toNumber(fx?.usd_to_eur || 0);
  if (usdToEur > 0) {
    state.fx.usdToEur = usdToEur;
    state.fx.source = "runtime";
    if (el("adminUsdToEur")) {
      el("adminUsdToEur").value = String(usdToEur);
    }
  }
}

function updateMetrics(data) {
  if (!data) return;
  el("mStatus").textContent = data.status ?? "-";
  el("mProgress").textContent = data.progress != null ? `${data.progress}%` : "-";
  el("mTaxLines").textContent = String(data.tax_line_count ?? "-");
  el("mDerivLines").textContent = String(data.derivative_line_count ?? "-");
  el("summaryOut").textContent = JSON.stringify(data.result_summary ?? {}, null, 2);
}

function renderDashboard(data) {
  if (!data) return;
  state.dashboard = data;
  const summary = data.summary || {};
  const role = data.role_detection || {};
  const signals = role.signals || {};
  el("dTotalEvents").textContent = String(summary.total_events ?? "-");
  el("dAssets").textContent = String(summary.unique_assets ?? "-");
  el("dRole").textContent = String(role.effective_mode ?? "-");
  el("dSignals").textContent = `reward:${signals.reward_events ?? 0} / events:${signals.event_count ?? 0}`;
  el("dSuggestedTaxYear").textContent = String(summary.suggested_tax_year ?? "-");
  el("dashRoleMode").value = String(role.override_mode ?? "auto");
  renderActivityDailyChart(data.activity_history ?? []);
  renderActivityYearlyChart(data.activity_years ?? []);
  renderYearlyAssetActivity(data.yearly_asset_activity ?? {});
  renderAssetMix(data.asset_balances ?? []);
  renderWalletGroupsTable(data.wallet_groups ?? []);
  renderCockpitSources();
  if (Array.isArray(data.last_live_tokens)) {
    renderLiveTokenTable(data.last_live_tokens);
  }
  renderCockpit();
  renderMiningPanel();
  renderTradingPanel();
  updateWorkflowGuide();
}

async function refreshUsdEurRateBestEffort() {
  try {
    const res = await fetch("https://api.exchangerate.host/latest?base=USD&symbols=EUR");
    if (!res.ok) return;
    const json = await res.json();
    const rate = toNumber(json?.rates?.EUR || 0);
    if (rate > 0) {
      state.fx.usdToEur = rate;
      state.fx.source = "exchangerate.host";
      if (el("adminUsdToEur")) el("adminUsdToEur").value = String(rate);
    }
  } catch (_) {
    // Best effort only: keep runtime or fallback rate.
  }
}

function currentJobId() {
  return el("jobId").value.trim();
}

function renderTaxTable() {
  const tbody = el("taxTable").querySelector("tbody");
  tbody.innerHTML = "";
  const assetFilter = el("taxFilterAsset").value.trim().toUpperCase();
  const statusFilter = el("taxFilterStatus").value.trim();
  const rows = state.taxLines.filter((line) => {
    if (assetFilter && String(line.asset).toUpperCase() !== assetFilter) return false;
    if (statusFilter && line.tax_status !== statusFilter) return false;
    return true;
  });

  if (!rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="10">Keine Tax Lines für aktuellen Filter.</td>`;
    tbody.appendChild(tr);
    return;
  }

  const pageSize = Math.max(1, Number(el("taxPageSize")?.value || "50"));
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  if (state.paging.taxPage > totalPages) state.paging.taxPage = totalPages;
  if (state.paging.taxPage < 1) state.paging.taxPage = 1;
  const pageStart = (state.paging.taxPage - 1) * pageSize;
  const pageRows = rows.slice(pageStart, pageStart + pageSize);

  pageRows.forEach((line) => {
    const qty = toNumber(line.qty || 0);
    const cost = toNumber(line.cost_basis_eur || 0);
    const proceeds = toNumber(line.proceeds_eur || 0);
    const gain = toNumber(line.gain_loss_eur || 0);
    const holdDays = Number(line.hold_days || 0);
    const gainClass = gain < 0 ? "num-neg" : gain > 0 ? "num-pos" : "";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="c-line">${line.line_no}</td>
      <td class="c-asset">${line.asset}</td>
      <td class="num c-qty ${qty < 0 ? "num-neg" : ""}">${formatQty(qty)}</td>
      <td class="c-buy">${line.buy_timestamp_utc}</td>
      <td class="c-sell">${line.sell_timestamp_utc}</td>
      <td class="num c-cost">${formatMoney(cost)}</td>
      <td class="num c-proceeds">${formatMoney(proceeds)}</td>
      <td class="num c-gain ${gainClass}">${formatMoney(gain)}</td>
      <td class="num c-hold">${Number.isFinite(holdDays) ? holdDays : ""}</td>
      <td class="c-status">${line.tax_status}</td>
      <td class="c-audit">
        <button class="btn-audit" data-line-no="${line.line_no}">Trace</button>
        <button class="btn-classify" data-event-id="${line.source_event_id || ""}">Klassifizieren</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  const info = el("taxPageInfo");
  if (info) info.textContent = `${state.paging.taxPage}/${totalPages} · ${rows.length} rows`;
  const prev = el("btnTaxPrev");
  const next = el("btnTaxNext");
  if (prev) prev.disabled = state.paging.taxPage <= 1;
  if (next) next.disabled = state.paging.taxPage >= totalPages;
  applyTableColumnVisibility("taxTable");
  renderTradingPanel();
  updateWorkflowGuide();
}

function renderTaxEventOverrideTable(rows) {
  const tbody = el("taxOverrideTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (rows || []).forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.source_event_id || ""}</td>
      <td>${item.tax_category || ""}</td>
      <td>${item.reason_label || item.reason_code || ""}</td>
      <td>${item.note || ""}</td>
      <td>${item.updated_at_utc || ""}</td>
    `;
    tr.addEventListener("click", () => {
      el("taxOverrideEventId").value = item.source_event_id || "";
      el("taxOverrideCategory").value = item.tax_category || "PRIVATE_SO";
      if (el("taxOverrideReason")) el("taxOverrideReason").value = item.reason_code || "";
      el("taxOverrideNote").value = item.note || "";
    });
    tbody.appendChild(tr);
  });
  if (!(rows || []).length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5">Keine Tax-Overrides vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderDerivativeTable() {
  const tbody = el("derivTable").querySelector("tbody");
  tbody.innerHTML = "";
  const assetFilter = el("derivFilterAsset").value.trim().toUpperCase();
  const typeFilter = el("derivFilterType").value.trim();
  const rows = state.derivativeLines.filter((line) => {
    if (assetFilter && String(line.asset).toUpperCase() !== assetFilter) return false;
    if (typeFilter && line.event_type !== typeFilter) return false;
    return true;
  });

  if (!rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="11">Keine Derivative Lines für aktuellen Filter.</td>`;
    tbody.appendChild(tr);
    return;
  }

  const pageSize = Math.max(1, Number(el("derivPageSize")?.value || "50"));
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  if (state.paging.derivPage > totalPages) state.paging.derivPage = totalPages;
  if (state.paging.derivPage < 1) state.paging.derivPage = 1;
  const pageStart = (state.paging.derivPage - 1) * pageSize;
  const pageRows = rows.slice(pageStart, pageStart + pageSize);

  pageRows.forEach((line) => {
    const collateral = toNumber(line.collateral_eur || 0);
    const proceeds = toNumber(line.proceeds_eur || 0);
    const fees = toNumber(line.fees_eur || 0);
    const funding = toNumber(line.funding_eur || 0);
    const gain = toNumber(line.gain_loss_eur || 0);
    const gainClass = gain < 0 ? "num-neg" : gain > 0 ? "num-pos" : "";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${line.line_no}</td>
      <td>${line.position_id}</td>
      <td>${line.asset}</td>
      <td>${line.event_type}</td>
      <td>${line.open_timestamp_utc}</td>
      <td>${line.close_timestamp_utc}</td>
      <td class="num">${formatMoney(collateral)}</td>
      <td class="num">${formatMoney(proceeds)}</td>
      <td class="num">${formatMoney(fees)}</td>
      <td class="num">${formatMoney(funding)}</td>
      <td class="num ${gainClass}">${formatMoney(gain)}</td>
    `;
    tbody.appendChild(tr);
  });
  const info = el("derivPageInfo");
  if (info) info.textContent = `${state.paging.derivPage}/${totalPages} · ${rows.length} rows`;
  const prev = el("btnDerivPrev");
  const next = el("btnDerivNext");
  if (prev) prev.disabled = state.paging.derivPage <= 1;
  if (next) next.disabled = state.paging.derivPage >= totalPages;
  updateWorkflowGuide();
}

function toCsv(rows, headers) {
  const esc = (value) => {
    const v = value == null ? "" : String(value);
    return `"${v.replaceAll('"', '""')}"`;
  };
  const lines = [headers.join(",")];
  rows.forEach((row) => {
    lines.push(headers.map((h) => esc(row[h])).join(","));
  });
  return lines.join("\n");
}

function downloadCsv(filename, content) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function callApi(path, method = "GET", body = null, btn = null, silent = false) {
  try {
    if (btn) btn.disabled = true;
    const init = { method, headers: {} };
    if (body !== null) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const res = await fetch(path, init);
    const rawText = await res.text();
    let json = null;
    try {
      json = rawText ? JSON.parse(rawText) : null;
    } catch (_parseError) {
      json = null;
    }
    if (!json || typeof json !== "object") {
      json = {
        trace_id: "",
        status: res.ok ? "success" : "error",
        data: {},
        errors: [
          {
            code: "non_json_response",
            message: rawText?.trim() || `HTTP ${res.status}`,
          },
        ],
        warnings: [],
      };
    }
    setResponse(json);
    if (!silent) {
      if (!res.ok || json.status === "error") {
        showToast(`Fehler: ${json.errors?.[0]?.message ?? res.statusText}`, "err");
      } else if (json.warnings?.length) {
        showToast(`Hinweis: ${json.warnings[0].message}`, "warn");
      } else {
        showToast("Aktion erfolgreich.", "ok");
      }
    }
    return json;
  } catch (error) {
    showToast(`Netzwerkfehler: ${error}`, "err");
    return null;
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderUnmatchedLists() {
  const outEl = el("outboundList");
  const inEl = el("inboundList");
  outEl.innerHTML = "";
  inEl.innerHTML = "";

  if (!state.unmatchedOutbound.length) outEl.innerHTML = "<li>Keine offenen Outbound-Transfers</li>";
  if (!state.unmatchedInbound.length) inEl.innerHTML = "<li>Keine offenen Inbound-Transfers</li>";

  state.unmatchedOutbound.forEach((id) => {
    const li = document.createElement("li");
    li.textContent = id;
    outEl.appendChild(li);
  });
  state.unmatchedInbound.forEach((id) => {
    const li = document.createElement("li");
    li.textContent = id;
    inEl.appendChild(li);
  });

  const outSelect = el("manualOut");
  const inSelect = el("manualIn");
  outSelect.innerHTML = "";
  inSelect.innerHTML = "";
  state.unmatchedOutbound.forEach((id) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = id;
    outSelect.appendChild(opt);
  });
  state.unmatchedInbound.forEach((id) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = id;
    inSelect.appendChild(opt);
  });
}

function renderTransferLedgerTable(tableId, rows) {
  const tbody = el(tableId)?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  (rows || []).forEach((item) => {
    const quantity = toNumber(item.quantity || 0);
    const confidence = item.confidence_score
      ? ` (${(toNumber(item.confidence_score) * 100).toFixed(2)}%)`
      : "";
    const tr = document.createElement("tr");
    const status = item.status || "";
    const continuity = String(item.holding_period_continues || "").toLowerCase();
    const holdLabel = continuity === "true" ? "fortlaufend" : (continuity === "unknown" ? "prüfen" : "nein");
    tr.innerHTML = `
      <td>${item.timestamp_utc || ""}</td>
      <td>${status}</td>
      <td>${item.asset || ""}</td>
      <td class="num ${quantity < 0 ? "num-neg" : quantity > 0 ? "num-pos" : ""}">${formatQty(quantity)}</td>
      <td>${holdLabel}</td>
      <td>${item.from_platform || ""}</td>
      <td title="${item.from_counterparty || ""}">${item.from_wallet || ""}<br><small class="muted">${item.from_depot_id || ""}</small></td>
      <td>${item.to_platform || ""}</td>
      <td title="${item.to_counterparty || ""}">${item.to_wallet || ""}<br><small class="muted">${item.to_depot_id || ""}</small></td>
      <td>${item.method || ""}${confidence}</td>
    `;
    tbody.appendChild(tr);
  });

  if (!rows?.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="10">Keine Transfer-Daten vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderTransferLedger(rows) {
  const search = (el("reviewTransferSearch")?.value || "").trim().toLowerCase();
  const status = (el("reviewTransferStatus")?.value || "").trim().toLowerCase();
  const filtered = (rows || []).filter((item) => {
    const itemStatus = String(item.status || "").toLowerCase();
    if (status && itemStatus !== status) return false;
    if (!search) return true;
    const hay = [
      item.asset,
      item.from_platform,
      item.from_wallet,
      item.to_platform,
      item.to_wallet,
      item.method,
      item.match_id,
      item.status,
    ]
      .map((v) => String(v || "").toLowerCase())
      .join(" ");
    return hay.includes(search);
  });
  const pageSize = Math.max(1, Number(el("reviewTransferPageSize")?.value || "50"));
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (state.paging.transferPage > totalPages) state.paging.transferPage = totalPages;
  if (state.paging.transferPage < 1) state.paging.transferPage = 1;
  const pageStart = (state.paging.transferPage - 1) * pageSize;
  const pageRows = filtered.slice(pageStart, pageStart + pageSize);
  renderTransferLedgerTable("transferLedgerTable", pageRows);
  renderTransferLedgerTable("reviewTransferTable", pageRows);
  const info = el("reviewTransferPageInfo");
  if (info) info.textContent = `${state.paging.transferPage}/${totalPages} · ${filtered.length} rows`;
  const prev = el("btnTransferPrev");
  const next = el("btnTransferNext");
  if (prev) prev.disabled = state.paging.transferPage <= 1;
  if (next) next.disabled = state.paging.transferPage >= totalPages;
  updateWorkflowGuide();
}

function renderLegacyHntTransfers(data) {
  const summary = data?.summary || {};
  const rows = Array.isArray(data?.counterparties) ? data.counterparties : [];
  const range = summary.first_timestamp_utc || summary.last_timestamp_utc
    ? `${String(summary.first_timestamp_utc || "?").slice(0, 10)} bis ${String(summary.last_timestamp_utc || "?").slice(0, 10)}`
    : "-";

  [
    ["legacyHntSent", summary.sent_hnt],
    ["reviewLegacyHntSent", summary.sent_hnt],
    ["legacyHntReceived", summary.received_hnt],
    ["reviewLegacyHntReceived", summary.received_hnt],
  ].forEach(([id, value]) => {
    if (el(id)) el(id).textContent = `${formatQty(value || 0)} HNT`;
  });
  [
    ["legacyHntCounterparties", summary.counterparty_count],
    ["reviewLegacyHntCounterparties", summary.counterparty_count],
  ].forEach(([id, value]) => {
    if (el(id)) el(id).textContent = formatQty(value || 0);
  });
  ["legacyHntRange", "reviewLegacyHntRange"].forEach((id) => {
    if (el(id)) el(id).textContent = range;
  });

  ["legacyHntTransferTable", "reviewLegacyHntTransferTable"].forEach((tableId) => {
    const tbody = el(tableId)?.querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    rows.slice(0, 50).forEach((item) => {
      const sample = Array.isArray(item.sample_comments) && item.sample_comments.length
        ? item.sample_comments[0]
        : (Array.isArray(item.sample_tx_ids) ? item.sample_tx_ids[0] : "");
      const net = toNumber(item.net_hnt || 0);
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td title="${item.counterparty_wallet || ""}">${shortAddress(item.counterparty_wallet || "")}</td>
        <td class="num num-neg">${formatQty(item.sent_hnt || 0)}</td>
        <td class="num num-pos">${formatQty(item.received_hnt || 0)}</td>
        <td class="num">${formatQty(item.fees_hnt || 0)}</td>
        <td class="num ${net < 0 ? "num-neg" : net > 0 ? "num-pos" : ""}">${formatQty(item.net_hnt || 0)}</td>
        <td>${String(item.first_timestamp_utc || "").slice(0, 10)}</td>
        <td>${String(item.last_timestamp_utc || "").slice(0, 10)}</td>
        <td title="${sample || ""}">${shortText(sample || "", 42)}</td>
      `;
      tbody.appendChild(tr);
    });
    if (!rows.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="8">Keine Legacy-HNT-Transfers importiert.</td>';
      tbody.appendChild(tr);
    }
  });
}

function renderLotAging(rows) {
  const tbody = el("dashLotTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (rows || []).forEach((item) => {
    const status = item.tax_status || "";
    const statusClass = status === "exempt" ? "status-badge status-alias" : "status-badge status-default";
    const qty = toNumber(item.qty || 0);
    const holdDays = toNumber(item.hold_days || 0);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.asset || ""}</td>
      <td class="num ${qty < 0 ? "num-neg" : qty > 0 ? "num-pos" : ""}">${formatQty(qty)}</td>
      <td>${item.buy_timestamp_utc || ""}</td>
      <td class="num">${Number.isFinite(holdDays) ? Math.floor(holdDays) : ""}</td>
      <td><span class="${statusClass}">${status}</span></td>
    `;
    tbody.appendChild(tr);
  });
  if (!rows?.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5">Keine Lots vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderIssues(rows) {
  renderIssueSummary(rows);
  const tbody = el("issuesTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const search = (el("reviewIssueSearch")?.value || "").trim().toLowerCase();
  const statusFilter = (el("reviewIssueStatus")?.value || "").trim().toLowerCase();
  const filtered = (rows || []).filter((item) => {
    const itemStatus = String(item.status || "").toLowerCase();
    if (statusFilter && itemStatus !== statusFilter) return false;
    if (!search) return true;
    const hay = [
      item.issue_id,
      item.status,
      item.severity,
      item.type,
      item.asset,
      item.detail,
      item.note,
    ]
      .map((v) => String(v || "").toLowerCase())
      .join(" ");
    return hay.includes(search);
  });
  const pageSize = Math.max(1, Number(el("reviewIssuePageSize")?.value || "50"));
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (state.paging.issuePage > totalPages) state.paging.issuePage = totalPages;
  if (state.paging.issuePage < 1) state.paging.issuePage = 1;
  const pageStart = (state.paging.issuePage - 1) * pageSize;
  const pageRows = filtered.slice(pageStart, pageStart + pageSize);
  pageRows.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.issue_id || ""}</td>
      <td>${item.status || ""}</td>
      <td>${item.severity || ""}</td>
      <td>${item.type || ""}</td>
      <td>${item.asset || ""}</td>
      <td title="${item.note || ""}">${item.detail || ""}</td>
    `;
    tr.addEventListener("click", () => {
      el("issueId").value = item.issue_id || "";
      el("issueStatus").value = item.status || "open";
      el("issueNote").value = item.note || "";
    });
    tbody.appendChild(tr);
  });
  if (!filtered?.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="6">Keine offenen Issues.</td>';
    tbody.appendChild(tr);
  }
  const info = el("reviewIssuePageInfo");
  if (info) info.textContent = `${state.paging.issuePage}/${totalPages} · ${filtered.length} rows`;
  const prev = el("btnIssuePrev");
  const next = el("btnIssueNext");
  if (prev) prev.disabled = state.paging.issuePage <= 1;
  if (next) next.disabled = state.paging.issuePage >= totalPages;
  updateWorkflowGuide();
}

function countBy(rows, key) {
  return (rows || []).reduce((acc, row) => {
    const value = String(row?.[key] || "unknown");
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function topCountLabel(counts, fallback = "-") {
  const entries = Object.entries(counts || {}).sort((a, b) => Number(b[1]) - Number(a[1]));
  if (!entries.length) return fallback;
  return entries.slice(0, 3).map(([key, value]) => `${key}: ${value}`).join(" · ");
}

function renderIssueSummary(rows) {
  const host = el("issueSummaryCards");
  if (!host) return;
  const issues = Array.isArray(rows) ? rows : [];
  const byType = countBy(issues, "type");
  const bySeverity = countBy(issues, "severity");
  const byStatus = countBy(issues, "status");
  const byAsset = countBy(issues, "asset");
  const highOpen = issues.filter((item) => item.status === "open" && item.severity === "high").length;
  const mediumOpen = issues.filter((item) => item.status === "open" && item.severity === "medium").length;
  host.innerHTML = "";
  [
    { label: "Issues Gesamt", value: String(issues.length), sub: topCountLabel(byStatus) },
    { label: "High offen", value: String(highOpen), sub: highOpen ? "exportkritisch" : "kein Blocker" },
    { label: "Medium offen", value: String(mediumOpen), sub: "prüfen, aber nicht automatisch Blocker" },
    { label: "Typen", value: topCountLabel(byType), sub: "dominierende Issue-Arten" },
    { label: "Assets", value: topCountLabel(byAsset), sub: "betroffene Assets" },
    { label: "Severity", value: topCountLabel(bySeverity), sub: "Risikostufen" },
  ].forEach((item) => {
    const div = document.createElement("div");
    div.className = "metric";
    div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
    host.appendChild(div);
  });
}

function renderReviewGates(gates) {
  state.reviewGates = gates || null;
  const badge = el("gateStatusBadge");
  const summary = el("gateSummary");
  const blockersHost = el("gateBlockers");
  const warningsHost = el("gateWarnings");
  if (!badge || !summary || !blockersHost || !warningsHost) return;

  blockersHost.innerHTML = "";
  warningsHost.innerHTML = "";

  if (!gates || typeof gates !== "object") {
    badge.textContent = "unbekannt";
    badge.className = "status-badge status-default";
    summary.textContent = "Prüfung noch nicht ausgeführt.";
    if (el("globalIssueBadge")) el("globalIssueBadge").textContent = "Issues: -";
    setCsvButtonsDisabled(true, "Review-Gates noch nicht geprüft.");
    return;
  }

  const allow = !!gates.allow_export;
  const blockers = Array.isArray(gates.blocking_reasons) ? gates.blocking_reasons : [];
  const warns = Array.isArray(gates.warning_reasons) ? gates.warning_reasons : [];
  const counts = gates.counts || {};

  badge.textContent = allow ? "OK" : "BLOCKED";
  badge.className = allow ? "status-badge status-alias" : "status-badge status-spam";
  summary.textContent =
    `Unmatched: ${counts.unmatched_total || 0}, offene Issues: ${counts.issues_open || 0}, ` +
    `High-Severity offen: ${counts.issues_high_open || 0}`;
  if (el("globalIssueBadge")) {
    const totalOpen = Number(counts.issues_open || 0);
    const highOpen = Number(counts.issues_high_open || 0);
    el("globalIssueBadge").textContent = `Issues: ${totalOpen}${highOpen ? ` / High ${highOpen}` : ""}`;
    el("globalIssueBadge").className = highOpen ? "pill pill-err" : (totalOpen ? "pill pill-neutral" : "pill pill-ok");
  }

  blockers.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `Blocker: ${item.message || item.code || "unknown"}`;
    blockersHost.appendChild(li);
  });
  warns.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = `Hinweis: ${item.message || item.code || "unknown"}`;
    warningsHost.appendChild(li);
  });

  if (!blockers.length) {
    const li = document.createElement("li");
    li.textContent = "Keine Blocker gefunden.";
    blockersHost.appendChild(li);
  }

  setCsvButtonsDisabled(!allow, allow ? "" : "Export gesperrt: Review-Gates nicht erfüllt.");
}

async function loadReviewGates(silent = true) {
  const params = new URLSearchParams({
    time_window_seconds: String(Number(el("timeWindow")?.value || "600")),
    amount_tolerance_ratio: String(Number(el("amountTol")?.value || "0.02")),
    min_confidence: String(Number(el("minConf")?.value || "0.75")),
  });
  const jobId = currentJobId();
  if (jobId) {
    params.set("job_id", jobId);
  }
  const data = await callApi(`/api/v1/review/gates?${params.toString()}`, "GET", null, null, silent);
  if (!data?.data) return;
  renderReviewGates(data.data);
}

function parseEventsJson() {
  const text = el("eventsJson").value;
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) {
    throw new Error("Das JSON muss ein Array sein.");
  }
  return parsed;
}

function cexPayload() {
  const connectorId = el("cexConnector").value.trim();
  const apiKey = el("cexApiKey").value.trim();
  const apiSecret = el("cexApiSecret").value.trim();
  const passphrase = el("cexPassphrase").value.trim();
  const startDateRaw = el("cexStartDate").value.trim();
  const endDateRaw = el("cexEndDate").value.trim();
  const maxRows = Number(el("cexMaxRows").value || "200");
  if (!connectorId || !apiKey || !apiSecret) {
    throw new Error("Connector, API Key und API Secret sind erforderlich.");
  }
  const startMs = dateStartToUtcMs(startDateRaw);
  const endMs = dateEndToUtcMs(endDateRaw);
  if (startMs != null && endMs != null && startMs > endMs) {
    throw new Error("Startdatum darf nicht nach Enddatum liegen.");
  }
  return {
    connector_id: connectorId,
    api_key: apiKey,
    api_secret: apiSecret,
    passphrase: passphrase || null,
    max_rows: maxRows,
    start_time_ms: startMs,
    end_time_ms: endMs,
  };
}

function parseDateToUtcMs(raw, isEnd = false) {
  if (!raw) return null;
  const normalized = String(raw)
    .trim()
    .replace(/\./g, "/")
    .replace(/\s+/g, " ")
    .trim();
  if (!normalized) return null;

  if (/^\d{4}-\d{2}-\d{2}$/.test(normalized)) {
    const [y, m, d] = normalized.split("-").map((v) => Number(v));
    if (![y, m, d].every(Number.isFinite)) return null;
    return Date.UTC(y, m - 1, d, isEnd ? 23 : 0, isEnd ? 59 : 0, isEnd ? 59 : 0, isEnd ? 999 : 0);
  }

  if (/^\d{2}\/\d{2}\/\d{4}(?: \d{2}[:.]\d{2}(?::\d{2})?)?$/.test(normalized)) {
    const [datePart, timePart] = normalized.split(" ");
    const dateBits = datePart.split("/");
    if (dateBits.length !== 3) return null;
    const [d, m, y] = dateBits.map((v) => Number(v));
    if (![y, m, d].every(Number.isFinite)) return null;
    const tBits = timePart ? timePart.replace(":", ".").split(".") : ["0", "0", "0"];
    const hh = Number(tBits[0] || "0");
    const mm = Number(tBits[1] || "0");
    const ss = Number(tBits[2] || "0");
    if (![hh, mm, ss].every(Number.isFinite)) return null;
    return Date.UTC(y, m - 1, d, hh, mm, isEnd ? Math.max(ss, 59) : ss, isEnd ? 999 : 0);
  }

  if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}[:.]\d{2}(?::\d{2})?$/.test(normalized)) {
    const parsed = new Date(normalized.replace(" ", "T").replace(".", ":"));
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed.getTime();
  }

  const fallback = Date.parse(normalized);
  if (Number.isNaN(fallback)) return null;
  return fallback;
}

function dateStartToUtcMs(raw) {
  return parseDateToUtcMs(raw, false);
}

function dateEndToUtcMs(raw) {
  return parseDateToUtcMs(raw, true);
}

async function loadSavedCexCredentials(connectorId) {
  const connector = String(connectorId || "").trim();
  if (!connector) return null;
  const res = await callApi(
    "/api/v1/admin/cex-credentials/load",
    "POST",
    { connector_id: connector },
    null,
    true
  );
  if (res?.status !== "success") return null;
  return res.data || null;
}

function solanaPayload() {
  const walletAddress = el("solWallet").value.trim();
  const rpcUrl = el("solRpc").value.trim() || "https://api.mainnet.solana.com";
  const fallbackRaw = el("solRpcFallbacks").value.trim();
  const fallbackUrls = fallbackRaw
    ? fallbackRaw.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
    : [];
  const beforeSignature = el("solBeforeSignature").value.trim();
  const maxSignatures = Number(el("solMaxSignatures").value || "100");
  const maxTransactions = Number(el("solMaxTransactions").value || "50");
  const aggregateJupiter = el("solAggregateJupiter").value === "true";
  const jupiterWindowSeconds = Number(el("solJupiterWindow").value || "2");
  if (!walletAddress) {
    throw new Error("Wallet Address ist erforderlich.");
  }
  return {
    wallet_address: walletAddress,
    rpc_url: rpcUrl,
    rpc_fallback_urls: fallbackUrls,
    before_signature: beforeSignature || null,
    max_signatures: maxSignatures,
    max_transactions: maxTransactions,
    aggregate_jupiter: aggregateJupiter,
    jupiter_window_seconds: jupiterWindowSeconds,
  };
}

function solanaFullHistoryPayload() {
  const payload = solanaPayload();
  const startTimeMs = dateStartToUtcMs(el("solStartDate").value);
  const endTimeMs = dateEndToUtcMs(el("solEndDate").value);
  const maxTotal = Number(el("solMaxSignaturesTotal").value || "50000");
  if (!Number.isFinite(maxTotal) || maxTotal <= 0) {
    throw new Error("Solana Full-History: Max Signatures Total muss größer 0 sein.");
  }
  return {
    ...payload,
    start_time_ms: startTimeMs,
    end_time_ms: endTimeMs,
    max_signatures_total: Math.max(100, Math.floor(maxTotal)),
  };
}

function renderSolanaProbe(data) {
  const out = el("solProbeOut");
  if (!data) {
    out.textContent = "";
    return;
  }
  const summary = {
    ok_count: data.ok_count ?? 0,
    probe_count: data.probe_count ?? 0,
    first_working_endpoint: data.first_working_endpoint ?? null,
    results: data.results ?? [],
  };
  out.textContent = JSON.stringify(summary, null, 2);
}

async function pingApi() {
  const res = await callApi("/api/v1/health");
  setApiState(!!(res && res.status === "success"));
}

async function loadAdminData() {
  const runtimeRes = await callApi("/api/v1/admin/runtime-config", "GET", null, null, true);
  if (runtimeRes?.status === "success") {
    state.admin.runtime = runtimeRes.data;
    applyRuntimeDefaults(runtimeRes.data);
    el("adminSecurityOut").textContent = JSON.stringify(
      {
        master_key_configured: runtimeRes.data?.master_key_configured ?? null,
        credentials: runtimeRes.data?.credentials ?? {},
      },
      null,
      2
    );
    const runtimeSolana = runtimeRes?.data?.runtime?.solana;
    if (runtimeSolana?.default_wallet && !el("dashWallet").value.trim()) {
      el("dashWallet").value = runtimeSolana.default_wallet;
    }
  }

  const settingsRes = await callApi("/api/v1/admin/settings", "GET", null, null, true);
  if (settingsRes?.status === "success") {
    state.admin.settings = settingsRes.data?.settings ?? [];
    el("adminSettingsOut").textContent = JSON.stringify(settingsRes.data ?? {}, null, 2);
    if (settingsRes.data?.master_key_configured != null) {
      const base = state.admin.runtime ?? {};
      el("adminSecurityOut").textContent = JSON.stringify(
        {
          master_key_configured: settingsRes.data.master_key_configured,
          credentials: base.credentials ?? {},
        },
        null,
        2
      );
    }
  }

  await loadBackfillService();
  await loadTokenAliases();
  await loadIgnoredTokens();
  const lastTokens = state.dashboard?.last_live_tokens ?? [];
  if (Array.isArray(lastTokens) && lastTokens.length > 0) {
    renderLiveTokenTable(lastTokens);
  }
}

async function loadBackfillService() {
  const res = await callApi("/api/v1/admin/services/solana-backfill", "GET", null, null, true);
  if (res?.status === "success") {
    state.admin.backfillService = res.data;
    renderBackfillService(res.data);
  }
}

function renderBackfillService(data) {
  if (!data) return;
  const active = data.active_state || "unknown";
  const sub = data.sub_state || "";
  const stats = data.stats || {};
  const badge = el("backfillServiceBadge");
  if (badge) {
    badge.textContent = `${active}${sub ? ` / ${sub}` : ""}`;
    badge.className = `status-badge ${active === "active" ? "status-ok" : "status-warn"}`;
  }
  if (el("backfillServiceName")) el("backfillServiceName").textContent = data.service_name || "-";
  if (el("backfillEnabled")) el("backfillEnabled").textContent = data.enabled ? "enabled" : data.enabled_state || "-";
  if (el("backfillPid")) el("backfillPid").textContent = String(data.main_pid || "-");
  if (el("backfillInserted")) el("backfillInserted").textContent = formatInt(stats.total_inserted ?? 0);
  if (el("backfillDuplicates")) el("backfillDuplicates").textContent = formatInt(stats.total_duplicates ?? 0);
  if (el("backfillLastRun")) el("backfillLastRun").textContent = stats.last_run_utc || "-";
  const rate = firstRateControl(stats.rpc_rate_control);
  if (el("backfillRpcDelay")) {
    el("backfillRpcDelay").textContent = rate ? `${rate.delay_seconds}s` : "-";
  }
  if (el("backfillRateLimits")) {
    el("backfillRateLimits").textContent = rate ? formatInt(rate.backpressure_count ?? 0) : "-";
  }
  const coverage = data.import_coverage || {};
  if (el("backfillCoverageEvents")) {
    el("backfillCoverageEvents").textContent = `${formatInt(coverage.raw_event_count || 0)} Events / ${formatInt(coverage.distinct_tx_id_count || 0)} TX`;
  }
  if (el("backfillCoverageRange")) {
    const first = String(coverage.first_timestamp_utc || "").slice(0, 10) || "?";
    const last = String(coverage.last_timestamp_utc || "").slice(0, 10) || "?";
    el("backfillCoverageRange").textContent = first === "?" && last === "?" ? "-" : `${first} bis ${last}`;
  }
  if (el("backfillReachedStart")) {
    el("backfillReachedStart").textContent = data.scan_reached_start ? "ja" : "unbekannt";
  }
  if (el("backfillLogOut")) el("backfillLogOut").textContent = (data.log_tail || []).join("\n");
}

function firstRateControl(rateControl) {
  if (!rateControl || typeof rateControl !== "object") return null;
  const first = Object.values(rateControl)[0];
  return first && typeof first === "object" ? first : null;
}

async function controlBackfillService(action, button) {
  const res = await callApi(
    "/api/v1/admin/services/solana-backfill/action",
    "POST",
    { action },
    button
  );
  if (res?.status === "success") {
    renderBackfillService(res.data);
    showToast(`Backfill ${action} ausgeführt.`, "ok");
    return;
  }
  showToast(`Backfill ${action} fehlgeschlagen.`, "error");
}

async function loadDashboard() {
  const res = await callApi("/api/v1/dashboard/overview", "GET", null, null, true);
  if (res?.status === "success") {
    renderDashboard(res.data);
    loadLegacyHntTransfers(true);
    const suggestedYear = res.data?.summary?.suggested_tax_year;
    const currentTaxYear = el("taxYear").value.trim();
    if (suggestedYear && (!currentTaxYear || currentTaxYear === "2026")) {
      el("taxYear").value = String(suggestedYear);
      syncTaxRunSelection();
    }
  }
}

function renderIntegrationTable(rows) {
  const tbody = el("integrationTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (rows || []).forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.integration_id || ""}</td>
      <td class="num">${formatQty(item.event_count || 0)}</td>
      <td class="num">${formatQty(item.asset_count || 0)}</td>
      <td class="num">${formatQty(item.source_file_count || 0)}</td>
      <td>${item.first_timestamp_utc || "-"}</td>
      <td>${item.last_timestamp_utc || "-"}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!(rows || []).length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="6">Noch keine Integrationen mit Daten.</td>';
    tbody.appendChild(tr);
  }
}

function renderImportSourcesTable(rows) {
  const tbody = el("importSourcesTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (rows || []).forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.created_at_utc || "-"}</td>
      <td>${item.source_name || ""}</td>
      <td class="num">${formatQty(item.declared_row_count || 0)}</td>
      <td class="num">${formatQty(item.imported_event_count || 0)}</td>
      <td title="${item.source_file_id || ""}">${String(item.source_file_id || "").slice(0, 12)}...</td>
    `;
    tbody.appendChild(tr);
  });
  if (!(rows || []).length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5">Noch keine Importe vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function importJobStatusClass(status) {
  const value = String(status || "").toLowerCase();
  if (value === "completed") return "status-ok";
  if (value === "partial") return "status-warn";
  if (value === "duplicate") return "status-ignored";
  if (value === "empty") return "status-default";
  return "status-running";
}

function renderImportJobsTable(rows) {
  const tbody = el("importJobsTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (rows || []).forEach((item) => {
    const tr = document.createElement("tr");
    const selected = state.selectedImportJob?.job_id && state.selectedImportJob.job_id === item.job_id;
    tr.classList.toggle("row-selected", !!selected);
    tr.innerHTML = `
      <td>${escapeHtml(String(item.started_at_utc || "-").replace("T", " ").slice(0, 16))}</td>
      <td>${escapeHtml(item.connector || "unknown")}</td>
      <td><span class="${importJobStatusClass(item.status)}">${escapeHtml(item.status || "")}</span></td>
      <td class="num">${formatQty(item.rows || 0)}</td>
      <td class="num">${formatQty(item.inserted_events || 0)}</td>
      <td class="num">${formatQty(item.duplicates || 0)}</td>
      <td title="${escapeHtml(item.source_name || "")}">${escapeHtml(String(item.source_name || "").slice(0, 64))}</td>
    `;
    tr.addEventListener("click", () => {
      state.selectedImportJob = item;
      renderImportJobsTable(state.importJobs);
      renderImportJobDetail(item);
    });
    tbody.appendChild(tr);
  });
  if (!(rows || []).length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="7">Noch keine Import-Aktivität für die aktuelle Filterung vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderImportJobDetail(item) {
  const host = el("importJobDetail");
  if (!host) return;
  if (!item) {
    host.className = "notice notice-neutral";
    host.textContent = "Kein Import ausgewählt.";
    return;
  }
  const sourceName = String(item.source_name || "");
  const isBulk = sourceName.startsWith("bulk:");
  host.className = `notice ${item.status === "completed" ? "notice-ok" : item.status === "duplicate" ? "notice-warn" : "notice-neutral"}`;
  host.innerHTML = `
    <div><strong>${escapeHtml(item.connector || "unknown")}</strong> · ${escapeHtml(item.status || "")}</div>
    <div class="muted">Source-ID: ${escapeHtml(item.source_file_id || item.job_id || "-")}</div>
    <div class="muted">Quelle: ${escapeHtml(sourceName || "-")}</div>
    <div class="guided-actions">
      <button class="guided-action" type="button" data-import-detail-action="copy-id">Source-ID kopieren</button>
      <button class="guided-action" type="button" data-import-detail-action="${isBulk ? "retry-bulk" : "open-connector"}">
        ${isBulk ? "Bulk-Import erneut öffnen" : "Passende Integration öffnen"}
      </button>
    </div>
  `;
}

function renderIntegrationMetrics() {
  const intCount = state.integrationRows?.length || 0;
  const intEvents = (state.integrationRows || []).reduce((acc, row) => acc + Number(row.event_count || 0), 0);
  const sourceCount = state.importSources?.length || 0;
  const lastImport = sourceCount ? String(state.importSources[0]?.created_at_utc || "-") : "-";
  if (el("mIntCount")) el("mIntCount").textContent = formatQty(intCount);
  if (el("mIntEvents")) el("mIntEvents").textContent = formatQty(intEvents);
  if (el("mSourceCount")) el("mSourceCount").textContent = formatQty(sourceCount);
  if (el("mLastImportAt")) el("mLastImportAt").textContent = lastImport === "-" ? "-" : lastImport.replace("T", " ").slice(0, 16);
  renderCockpitSources();
  renderConnectorWizard();
}

function findIntegrationRow(...ids) {
  const wanted = ids.map((id) => String(id).toLowerCase());
  return (state.integrationRows || []).find((row) => {
    const id = String(row.integration_id || "").toLowerCase();
    return wanted.some((needle) => id.includes(needle));
  }) || null;
}

function formatRange(row) {
  if (!row) return "noch nicht geladen";
  const first = row.first_timestamp_utc ? String(row.first_timestamp_utc).slice(0, 10) : "?";
  const last = row.last_timestamp_utc ? String(row.last_timestamp_utc).slice(0, 10) : "?";
  return `${first} bis ${last}`;
}

function setConnectorCard(selector, row) {
  const card = document.querySelector(`[data-connector-card="${selector}"]`);
  if (!card) return;
  const count = toNumber(row?.event_count || 0);
  card.classList.toggle("connector-ready", count > 0);
}

function renderConnectorWizard() {
  const sol = findIntegrationRow("solana", "phantom");
  const cex = findIntegrationRow("binance", "bitget", "coinbase", "cex");
  const fileRows = (state.integrationRows || []).filter((row) => {
    const id = String(row.integration_id || "").toLowerCase();
    return id.includes("csv") || id.includes("xls") || id.includes("blockpit") || id.includes("helium") || id.includes("file");
  });
  const fileEvents = fileRows.reduce((acc, row) => acc + toNumber(row.event_count || 0), 0);
  const fileRange = fileRows.length ? `${fileRows.length} Importprofile` : "Ordner bereit";

  if (el("cwSolanaEvents")) el("cwSolanaEvents").textContent = `${formatQty(sol?.event_count || 0)} Events`;
  if (el("cwSolanaRange")) el("cwSolanaRange").textContent = formatRange(sol);
  if (el("cwCexEvents")) el("cwCexEvents").textContent = `${formatQty(cex?.event_count || 0)} Events`;
  if (el("cwCexRange")) el("cwCexRange").textContent = formatRange(cex);
  if (el("cwFileEvents")) el("cwFileEvents").textContent = `${formatQty(fileEvents)} Events`;
  if (el("cwFileRange")) el("cwFileRange").textContent = fileRange;
  if (el("cwWalletGroups")) el("cwWalletGroups").textContent = `${formatQty(state.walletGroups?.length || 0)} Gruppen`;

  setConnectorCard("solana_rpc", sol);
  setConnectorCard("binance_api", cex);
  const fileCard = document.querySelector('[data-connector-card="file_import"]');
  if (fileCard) fileCard.classList.toggle("connector-ready", fileEvents > 0);
  const walletCard = document.querySelector('[data-connector-card="wallet_groups"]');
  if (walletCard) walletCard.classList.toggle("connector-ready", (state.walletGroups?.length || 0) > 0);
}

function openSettingsPanel(id, focusId = "") {
  const panel = el(id);
  if (panel && panel.tagName.toLowerCase() === "details") {
    panel.open = true;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (focusId && el(focusId)) {
    window.setTimeout(() => el(focusId)?.focus(), 180);
  }
}

async function loadIntegrationOverview() {
  const data = await callApi("/api/v1/portfolio/integrations", "GET", null, null, true);
  if (data?.status !== "success") return;
  state.integrationRows = data.data?.rows ?? [];
  renderIntegrationTable(state.integrationRows);
  renderIntegrationMetrics();
  renderWalletGroupSourceFilters(selectedWalletGroup());
}

async function loadLegacyHntTransfers(silent = true) {
  const data = await callApi("/api/v1/portfolio/helium-legacy-transfers", "GET", null, null, silent);
  if (data?.status !== "success") return;
  state.legacyHntTransfers = data.data;
  renderLegacyHntTransfers(state.legacyHntTransfers);
}

async function loadImportSourcesSummary() {
  const data = await callApi("/api/v1/import/sources-summary?limit=200", "GET", null, null, true);
  if (data?.status !== "success") return;
  state.importSources = data.data?.rows ?? [];
  renderImportSourcesTable(state.importSources);
  renderIntegrationMetrics();
  await loadImportJobs(true);
}

async function loadImportJobs(silent = true) {
  const params = new URLSearchParams({ limit: "200", offset: "0" });
  const integration = String(el("importJobIntegration")?.value || "").trim();
  const status = String(el("importJobStatus")?.value || "").trim();
  if (integration) params.set("integration", integration);
  if (status) params.set("status", status);
  const data = await callApi(`/api/v1/import/jobs?${params.toString()}`, "GET", null, null, silent);
  if (data?.status !== "success") return;
  state.importJobs = data.data?.rows ?? [];
  if (state.selectedImportJob) {
    state.selectedImportJob = state.importJobs.find((item) => item.job_id === state.selectedImportJob.job_id) || null;
  }
  renderImportJobsTable(state.importJobs);
  renderImportJobDetail(state.selectedImportJob);
}

function handleImportJobDetailAction(action) {
  const item = state.selectedImportJob;
  if (!item) {
    showToast("Kein Import ausgewählt.", "warn");
    return;
  }
  if (action === "copy-id") {
    const value = String(item.source_file_id || item.job_id || "");
    if (navigator.clipboard && value) {
      navigator.clipboard.writeText(value);
      showToast("Source-ID kopiert.", "ok");
    } else if (value) {
      showToast(value, "ok");
    }
    return;
  }
  if (action === "retry-bulk") {
    openSettingsPanel("bulkSettings", "bulkFolderPath");
    showToast("Bulk-Import geöffnet. Prüfe Ordner und starte bei Bedarf erneut.", "ok");
    return;
  }
  if (action === "open-connector") {
    const connector = String(item.connector || "").toLowerCase();
    if (connector.includes("solana")) {
      openSettingsPanel("solanaSettings", "solWallet");
    } else if (["binance", "bitget", "coinbase", "pionex"].some((name) => connector.includes(name))) {
      openSettingsPanel("cexSettings", "cexConnector");
      if (el("cexConnector") && connector) el("cexConnector").value = connector;
    } else {
      openSettingsPanel("bulkSettings", "bulkFolderPath");
    }
    showToast("Passende Import-Konfiguration geöffnet.", "ok");
  }
}

function destroyChart(id) {
  const chart = state.charts[id];
  if (chart) {
    chart.destroy();
    delete state.charts[id];
  }
}

function buildChart(id, config) {
  if (typeof Chart === "undefined") return;
  const canvas = el(id);
  if (!canvas) return;
  destroyChart(id);
  state.charts[id] = new Chart(canvas, config);
}

function renderActivityDailyChart(rows) {
  const labels = rows.map((item) => String(item.day || "").slice(5));
  const data = rows.map((item) => Number(item.count || 0));
  buildChart("chartActivityDaily", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Events / Tag",
          data,
          borderColor: "#2f7fd1",
          backgroundColor: "rgba(47,127,209,0.15)",
          fill: true,
          tension: 0.2,
          pointRadius: 1.5,
        },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderActivityYearlyChart(rows) {
  const labels = rows.map((item) => String(item.year || ""));
  const data = rows.map((item) => Number(item.count || 0));
  buildChart("chartActivityYearly", {
    type: "bar",
    data: {
      labels,
      datasets: [{ data, backgroundColor: ["#89b5e7", "#5f9ee0", "#367fcf", "#225d9f"], borderColor: "#2f6ead", borderWidth: 1 }],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderYearlyAssetActivity(activity) {
  const rows = Array.isArray(activity?.rows) ? activity.rows : [];
  const totals = Array.isArray(activity?.totals_by_year) ? activity.totals_by_year : [];
  const breakdown = Array.isArray(activity?.event_breakdown) ? activity.event_breakdown : [];
  const sourceBreakdown = Array.isArray(activity?.source_breakdown) ? activity.source_breakdown : [];
  const filter = (el("yearlyAssetFilter")?.value || "").trim().toLowerCase();
  populateYearlyYearFilter(activity?.years ?? [], rows);
  populateYearlySourceFilter(sourceBreakdown, rows);
  const selectedYear = (el("yearlyYearFilter")?.value || "").trim();
  const selectedSources = selectedYearlySources(sourceBreakdown, rows);
  const sourceFilterActive = selectedSources.active;
  const mode = normalizeYearlyScaleMode(el("yearlyScaleMode")?.value || "events");
  const yearRows = selectedYear ? rows.filter((row) => String(row.year || "") === selectedYear) : rows;
  const sourceRows = sourceFilterActive ? yearRows.filter((row) => selectedSources.values.has(String(row.source || "unknown"))) : yearRows;
  const visibleRows = filter
    ? sourceRows.filter((row) => `${row.asset || ""} ${row.symbol || ""} ${row.name || ""} ${row.source || ""}`.toLowerCase().includes(filter))
    : sourceRows;
  const visibleTotals = selectedYear ? totals.filter((row) => String(row.year || "") === selectedYear) : totals;
  const visibleBreakdown = selectedYear ? breakdown.filter((row) => String(row.year || "") === selectedYear) : breakdown;
  const yearSourceBreakdown = selectedYear
    ? sourceBreakdown.filter((row) => String(row.year || "") === selectedYear)
    : sourceBreakdown;
  const visibleSourceBreakdown = sourceFilterActive
    ? yearSourceBreakdown.filter((row) => selectedSources.values.has(String(row.source || "unknown")))
    : yearSourceBreakdown;
  renderYearlyValueTrend(mode, visibleRows, visibleTotals, visibleSourceBreakdown, {
    assetFilterActive: !!filter,
    yearFilterActive: !!selectedYear,
    sourceFilterActive,
  });
  renderPortfolioValueHistory(state.dashboard?.portfolio_value_history ?? [], selectedYear);
  renderYearlyEventBreakdownTable(visibleBreakdown);
  renderYearlySourceBreakdownTable(visibleSourceBreakdown);
  renderYearlyActivityTable(visibleRows);
}

function populateYearlyYearFilter(years, rows) {
  const select = el("yearlyYearFilter");
  if (!select) return;
  const current = select.value || "";
  const yearValues = new Set(Array.isArray(years) ? years.map((year) => String(year)) : []);
  rows.forEach((row) => {
    if (row.year) yearValues.add(String(row.year));
  });
  const sorted = Array.from(yearValues).sort();
  const signature = sorted.join("|");
  if (select.dataset.signature === signature) return;
  select.dataset.signature = signature;
  select.innerHTML = '<option value="">Alle Jahre</option>';
  sorted.forEach((year) => {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    select.appendChild(option);
  });
  if (current && sorted.includes(current)) select.value = current;
}

function populateYearlySourceFilter(sourceBreakdown, rows) {
  const container = el("yearlySourceFilter");
  if (!container) return;
  const current = loadYearlySourcePrefs();
  $$("input[data-yearly-source]").forEach((input) => current.set(input.value, input.checked));
  const sources = new Set();
  (Array.isArray(sourceBreakdown) ? sourceBreakdown : []).forEach((row) => {
    sources.add(String(row.source || "unknown"));
  });
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    sources.add(String(row.source || "unknown"));
  });
  const sorted = Array.from(sources).sort((a, b) => a.localeCompare(b));
  const signature = sorted.join("|");
  if (container.dataset.signature === signature) return;
  container.dataset.signature = signature;
  container.innerHTML = "";
  sorted.forEach((source) => {
    const id = `yearly-source-${source.replace(/[^a-z0-9_-]/gi, "-")}`;
    const checked = current.has(source) ? current.get(source) !== false : !isReferenceImportSource(source);
    const label = document.createElement("label");
    label.className = "source-chip";
    if (isReferenceImportSource(source)) label.classList.add("source-chip-reference");
    label.setAttribute("for", id);
    label.title = isReferenceImportSource(source)
      ? "Referenzimport: getrennt prüfen, nicht ungefiltert mit Primärdaten addieren."
      : "Primärquelle";
    label.innerHTML = `
      <input id="${id}" data-yearly-source type="checkbox" value="${source}" ${checked ? "checked" : ""} />
      <span>${source}${isReferenceImportSource(source) ? " · Referenz" : ""}</span>
    `;
    container.appendChild(label);
  });
  renderYearlySourceSummary();
}

function selectedYearlySources(sourceBreakdown, rows) {
  const allSources = new Set();
  (Array.isArray(sourceBreakdown) ? sourceBreakdown : []).forEach((row) => allSources.add(String(row.source || "unknown")));
  (Array.isArray(rows) ? rows : []).forEach((row) => allSources.add(String(row.source || "unknown")));
  const selected = new Set();
  $$("input[data-yearly-source]").forEach((input) => {
    if (input.checked) selected.add(input.value);
  });
  if (!allSources.size || selected.size === allSources.size) {
    renderYearlySourceSummary(selected.size || allSources.size, allSources.size, false);
    return { values: allSources, active: false };
  }
  renderYearlySourceSummary(selected.size, allSources.size, true);
  return { values: selected, active: true };
}

function loadYearlySourcePrefs() {
  const raw = loadPref("yearly.sources", "");
  const prefs = new Map();
  if (!raw) return prefs;
  try {
    Object.entries(JSON.parse(raw) || {}).forEach(([source, enabled]) => prefs.set(source, !!enabled));
  } catch (_) {
    return new Map();
  }
  return prefs;
}

function saveYearlySourcePrefs() {
  const prefs = {};
  $$("input[data-yearly-source]").forEach((input) => {
    prefs[input.value] = !!input.checked;
  });
  savePref("yearly.sources", JSON.stringify(prefs));
}

function isReferenceImportSource(source) {
  const value = String(source || "").toLowerCase();
  return value.includes("blockpit")
    || value.includes("reference")
    || value.includes("referenz")
    || value.includes("tax_report")
    || value.includes("steuerreport");
}

function setYearlySourceSelection(mode) {
  $$("input[data-yearly-source]").forEach((input) => {
    if (mode === "none") {
      input.checked = false;
    } else if (mode === "primary") {
      input.checked = !isReferenceImportSource(input.value);
    } else {
      input.checked = true;
    }
  });
  saveYearlySourcePrefs();
  renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
}

function renderYearlySourceSummary(selected = null, total = null, active = null) {
  const host = el("yearlySourceSummary");
  if (!host) return;
  const inputs = $$("input[data-yearly-source]");
  const sourceTotal = total ?? inputs.length;
  const sourceSelected = selected ?? inputs.filter((input) => input.checked).length;
  const isActive = active ?? (sourceTotal > 0 && sourceSelected !== sourceTotal);
  if (!sourceTotal) {
    host.textContent = "Noch keine Quellen geladen.";
    return;
  }
  host.textContent = `${sourceSelected}/${sourceTotal} Quellen aktiv${isActive ? " (gefiltert)" : ""}.`;
}

function renderYearlyValueTrend(mode, rows, totals, sourceBreakdown, filters = {}) {
  const byYear = new Map();
  const hasAssetFilter = !!filters.assetFilterActive;
  const hasSourceFilter = !!filters.sourceFilterActive;
  const hasYearFilter = !!filters.yearFilterActive;
  if (hasAssetFilter) {
    rows.forEach((row) => {
      const year = String(row.year || "");
      const current = byYear.get(year) || { year, events: 0, value_usd: 0, value_eur: 0, quantity_abs: 0 };
      current.events += Number(row.events || 0);
      current.value_usd += toNumber(row.value_usd || 0);
      current.value_eur += toNumber(row.value_eur || 0);
      current.trading_value_usd = (current.trading_value_usd || 0) + toNumber(row.trading_value_usd || 0);
      current.trading_value_eur = (current.trading_value_eur || 0) + toNumber(row.trading_value_eur || 0);
      current.quantity_abs += Math.abs(toNumber(row.quantity_abs || 0));
      byYear.set(year, current);
    });
  } else if (hasSourceFilter) {
    sourceBreakdown.forEach((row) => {
      const year = String(row.year || "");
      const current = byYear.get(year) || { year, events: 0, value_usd: 0, value_eur: 0, quantity_abs: 0 };
      current.events += Number(row.events || 0);
      current.value_usd += toNumber(row.value_usd || 0);
      current.value_eur += toNumber(row.value_eur || 0);
      current.trading_value_usd = (current.trading_value_usd || 0) + toNumber(row.trading_value_usd || 0);
      current.trading_value_eur = (current.trading_value_eur || 0) + toNumber(row.trading_value_eur || 0);
      byYear.set(year, current);
    });
  } else {
    totals.forEach((row) => {
      if (hasYearFilter && rows.length && !rows.some((visible) => String(visible.year || "") === String(row.year || ""))) return;
      byYear.set(String(row.year || ""), {
        year: String(row.year || ""),
        events: Number(row.events || 0),
        value_usd: toNumber(row.value_usd || 0),
        value_eur: toNumber(row.value_eur || 0),
        trading_value_usd: toNumber(row.trading_value_usd || 0),
        trading_value_eur: toNumber(row.trading_value_eur || 0),
        quantity_abs: Math.abs(toNumber(row.quantity_abs || 0)),
      });
    });
  }
  const series = Array.from(byYear.values()).sort((a, b) => String(a.year).localeCompare(String(b.year)));
  const labels = series.map((item) => item.year);
  const values = series.map((item) => yearlyMetricValue(item, mode));
  buildChart("chartYearlyValueTrend", {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: yearlyMetricLabel(mode),
        data: values,
        backgroundColor: "#f0b84d",
        borderColor: "#d59a24",
        borderWidth: 1,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => `${yearlyMetricLabel(mode)}: ${formatYearlyMetric(ctx.parsed.y, mode)}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (value) => formatYearlyAxis(value, mode) },
        },
      },
    },
  });
}

function renderPortfolioValueHistory(points, selectedYear = "") {
  const visible = (Array.isArray(points) ? points : [])
    .filter((point) => !selectedYear || String(point.year || "") === selectedYear)
    .sort((a, b) => String(a.date || "").localeCompare(String(b.date || "")));
  const labels = visible.map((point) => point.date || "");
  const values = visible.map((point) => toNumber(point.value_eur || 0));
  buildChart("chartPortfolioValueHistory", {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Portfolio-Wert EUR",
        data: values,
        borderColor: "#54a2f0",
        backgroundColor: "rgba(84,162,240,0.18)",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.25,
        fill: true,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: (ctx) => `Portfolio-Wert: ${formatCurrency(ctx.parsed.y, "EUR")}`,
            afterLabel: (ctx) => {
              const point = visible[ctx.dataIndex] || {};
              return `bewertet: ${formatInt(point.priced_assets || 0)}, unbewertet: ${formatInt(point.unpriced_assets || 0)}`;
            },
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (value) => compactNumber(value) },
        },
      },
    },
  });
}

function yearlyMetricValue(item, mode) {
  if (mode === "trading_usd") return item.trading_value_usd || 0;
  if (mode === "trading_eur") return item.trading_value_eur || 0;
  if (mode === "events") return item.events || 0;
  if (mode === "quantity_log") return item.quantity_abs > 0 ? Math.log10(item.quantity_abs) : 0;
  return item.events || 0;
}

function yearlyMetricLabel(mode) {
  if (mode === "trading_usd") return "Dedupliziertes Swap-/Handelsvolumen USD";
  if (mode === "trading_eur") return "Dedupliziertes Swap-/Handelsvolumen EUR";
  if (mode === "events") return "Transaktionen";
  if (mode === "quantity_log") return "Menge normalisiert (log10)";
  return "Transaktionen";
}

function formatYearlyMetric(value, mode) {
  if (mode === "trading_eur") return formatCurrency(value, "EUR");
  if (mode === "trading_usd") return formatCurrency(value, "USD");
  if (mode === "quantity_log") return `${Number(value).toFixed(2)} log10`;
  return formatInt(value);
}

function formatYearlyAxis(value, mode) {
  if (mode === "trading_eur" || mode === "trading_usd") return compactNumber(value);
  if (mode === "quantity_log") return `${Number(value).toFixed(1)}`;
  return compactNumber(value);
}

function normalizeYearlyScaleMode(raw) {
  const mode = String(raw || "events").trim();
  if (["events", "trading_eur", "trading_usd", "quantity_log"].includes(mode)) return mode;
  const select = el("yearlyScaleMode");
  if (select) select.value = "events";
  return "events";
}

function compactNumber(value) {
  return new Intl.NumberFormat("de-DE", { notation: "compact", maximumFractionDigits: 1 }).format(toNumber(value));
}

function renderYearlyActivityTable(rows) {
  const tbody = el("yearlyActivityTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const sorted = [...rows].sort((a, b) => {
    const yearDiff = Number(b.year || 0) - Number(a.year || 0);
    if (yearDiff !== 0) return yearDiff;
    return toNumber(b.value_eur || 0) - toNumber(a.value_eur || 0);
  }).slice(0, 250);
  sorted.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.year || ""}</td>
      <td>${row.source || "unknown"}</td>
      <td>${row.symbol || row.asset || ""}<br><small class="muted">${row.asset || ""}</small></td>
      <td>${row.name || ""}</td>
      <td class="num">${formatInt(row.events || 0)}</td>
      <td class="num">${formatQty(row.quantity_in || 0)}</td>
      <td class="num">${formatQty(row.quantity_out || 0)}</td>
      <td class="num ${toNumber(row.quantity_net || 0) < 0 ? "num-neg" : "num-pos"}">${formatQty(row.quantity_net || 0)}</td>
      <td class="num">${formatCurrency(row.value_usd || 0, "USD")}</td>
      <td class="num">${formatCurrency(row.value_eur || 0, "EUR")}</td>
      <td class="num">${toNumber(row.avg_usd_to_eur || 0).toFixed(4)}</td>
      <td class="num">${formatCurrency(row.trading_value_eur || 0, "EUR")}</td>
      <td class="num">${formatValuationCoverage(row)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!sorted.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="13">Keine Jahresdaten für den aktuellen Filter vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderYearlyEventBreakdownTable(rows) {
  const tbody = el("yearlyEventBreakdownTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const sorted = [...rows].sort((a, b) => {
    const yearDiff = Number(b.year || 0) - Number(a.year || 0);
    if (yearDiff !== 0) return yearDiff;
    return Number(b.events || 0) - Number(a.events || 0);
  }).slice(0, 120);
  sorted.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.year || ""}</td>
      <td>${formatEventCategory(row.category || "")}</td>
      <td class="num">${formatInt(row.events || 0)}</td>
      <td class="num">${formatCurrency(row.value_eur || 0, "EUR")}</td>
      <td class="num">${formatCurrency(row.trading_value_eur || 0, "EUR")}</td>
      <td class="num">${formatValuationCoverage(row)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!sorted.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="6">Keine Event-Kategorien für die aktuelle Auswahl vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function renderYearlySourceBreakdownTable(rows) {
  const tbody = el("yearlySourceBreakdownTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const sorted = [...rows].sort((a, b) => {
    const yearDiff = Number(b.year || 0) - Number(a.year || 0);
    if (yearDiff !== 0) return yearDiff;
    return Number(b.events || 0) - Number(a.events || 0);
  }).slice(0, 120);
  sorted.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.year || ""}</td>
      <td>${row.source || "unknown"}</td>
      <td class="num">${formatInt(row.events || 0)}</td>
      <td class="num">${formatCurrency(row.value_eur || 0, "EUR")}</td>
      <td class="num">${formatCurrency(row.trading_value_eur || 0, "EUR")}</td>
      <td class="num">${formatValuationCoverage(row)}</td>
    `;
    tbody.appendChild(tr);
  });
  if (!sorted.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="6">Keine Quellen-Aufschlüsselung für die aktuelle Auswahl vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function formatValuationCoverage(row) {
  const missing = Number(row?.unpriced_events || 0);
  const required = Number(row?.valuation_required_events || 0);
  if (!required) return "0";
  return missing ? `${formatInt(missing)} / ${formatInt(required)}` : `0 / ${formatInt(required)}`;
}

function formatEventCategory(category) {
  const labels = {
    derivate: "Derivate / Hebel",
    transfer: "Transfers / Deposits / Withdrawals",
    abgleich: "Abgleich / Non-Taxable",
    gebuehr: "Gebühren",
    reward_einkunft: "Rewards / Mining / Interest",
    trade_swap: "Trades / Swaps",
    unbekannt: "Unbekannt",
  };
  return labels[category] || category || "Unbekannt";
}

function renderAssetMix(rows) {
  const topRows = rows.slice(0, 8);
  const labels = topRows.map((item) => item.symbol || item.asset || "?");
  const data = topRows.map((item) => Math.abs(Number(item.quantity_abs || item.quantity || 0)));
  buildChart("chartAssetMix", {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: ["#2f7fd1", "#54a2f0", "#7ac0ff", "#1d5f9f", "#4a86c5", "#8bc9ff", "#285f95", "#6eb1eb"],
        },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });

  const tbody = el("dashAssetTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  topRows.forEach((item) => {
    const qty = toNumber(item.quantity || 0);
    const direction = item.flow_direction === "net_out" ? "↘" : (item.flow_direction === "net_in" ? "↗" : "→");
    const cls = qty < 0 ? "num-neg" : "num-pos";
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${item.symbol || item.asset || ""}</td><td>${item.name || ""}</td><td class="num ${cls}">${direction} ${formatQty(qty)}</td>`;
    tbody.appendChild(tr);
  });
}

function renderWalletGroupsTable(groups) {
  const tbody = el("dashWalletGroupTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  groups.forEach((group) => {
    const wallets = Array.isArray(group.wallet_addresses) ? group.wallet_addresses.length : 0;
    const sources = Array.isArray(group.source_filters) ? group.source_filters.length : 0;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(group.name || "")}</td>
      <td>${escapeHtml(group.group_id || "")}</td>
      <td class="num">${wallets}</td>
      <td class="num">${sources}</td>
      <td class="num">${formatQty(group.source_event_count || 0)}</td>
    `;
    tr.addEventListener("click", () => {
      state.selectedWalletGroupId = group.group_id || "";
      if (el("wgSelect")) el("wgSelect").value = state.selectedWalletGroupId;
      fillWalletGroupForm(selectedWalletGroup());
      refreshPortfolioSetHistory(group.group_id || "");
      switchReviewTab("holdings");
    });
    tbody.appendChild(tr);
  });
  if (!groups.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="5">Keine Wallet-Gruppen vorhanden.</td>';
    tbody.appendChild(tr);
  }
}

function selectedWalletGroupSourceFilters() {
  return Array.from(document.querySelectorAll("#wgSourceFilters input[type='checkbox']:checked"))
    .map((input) => String(input.value || "").trim())
    .filter((value) => value.length > 0);
}

function renderWalletGroupSourceFilters(group) {
  const host = el("wgSourceFilters");
  if (!host) return;
  const selected = new Set(Array.isArray(group?.source_filters) ? group.source_filters : []);
  const rows = Array.isArray(state.integrationRows) ? state.integrationRows : [];
  if (!rows.length) {
    host.innerHTML = '<span class="muted">Noch keine Importquellen erkannt.</span>';
    return;
  }
  host.innerHTML = rows
    .map((row) => {
      const source = String(row.integration_id || "");
      return `
        <label class="source-chip">
          <input type="checkbox" value="${escapeHtml(source)}" ${selected.has(source) ? "checked" : ""} />
          <span>${escapeHtml(source)}</span>
          <small>${formatQty(row.event_count || 0)} Events</small>
        </label>
      `;
    })
    .join("");
}

async function refreshPortfolioSetHistory(groupId) {
  const safeGroupId = String(groupId || "").trim();
  if (!safeGroupId) return;
  const windowDays = Number(el("dashSnapshotWindow")?.value || "365");
  const query = new URLSearchParams({
    group_id: safeGroupId,
    window_days: String(windowDays),
  });
  const res = await callApi(`/api/v1/dashboard/portfolio-set-history?${query.toString()}`, "GET", null, null, true);
  if (res?.status !== "success") return;
  const data = res.data || {};
  const points = data.points || [];
  const labels = points.map((point) => String(point.month || ""));
  const values = points.map((point) => convertUsdForDisplay(point.value_usd || 0));
  renderPnlCards(data.summary || {});
  buildChart("chartWalletSnapshots", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `Portfolio-Set Value (${currencyLabel()})`,
          data: values,
          borderColor: "#f8d15c",
          backgroundColor: "rgba(248,209,92,0.16)",
          fill: true,
          tension: 0.25,
          pointRadius: 1.5,
        },
      ],
    },
    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: false } } },
  });
}

function renderLiveTokenTable(tokens) {
  const tbody = el("dashLiveTokenTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  const showIgnored = !!el("dashShowIgnored")?.checked;
  const search = (el("dashTokenSearch")?.value || "").trim().toLowerCase();
  const statusFilter = (el("dashTokenStatusFilter")?.value || "").trim();
  const sortMode = (el("dashTokenSort")?.value || "usd_desc").trim();
  let visible = (tokens || []).filter((item) => {
    if (showIgnored) return true;
    return String(item?.ignored || "").toLowerCase() !== "true";
  });
  if (search) {
    visible = visible.filter((item) => {
      const hay = `${item.symbol || ""} ${item.name || ""} ${item.asset || ""}`.toLowerCase();
      return hay.includes(search);
    });
  }
  if (statusFilter) {
    visible = visible.filter((item) => {
      const status = tokenStatusKey(item);
      return status === statusFilter;
    });
  }
  visible.sort((a, b) => compareTokenRows(a, b, sortMode));
  renderLiveTokenStats(visible);
  renderTokenValueMix(visible);
  const pageSize = Math.max(1, Number(el("dashTokenPageSize")?.value || "50"));
  const totalPages = Math.max(1, Math.ceil(visible.length / pageSize));
  if (state.paging.tokenPage > totalPages) state.paging.tokenPage = totalPages;
  if (state.paging.tokenPage < 1) state.paging.tokenPage = 1;
  const pageStart = (state.paging.tokenPage - 1) * pageSize;
  const pageRows = visible.slice(pageStart, pageStart + pageSize);
  pageRows.forEach((item) => {
    const status = tokenStatusLabel(item);
    const statusClass = status === "Spam-Kandidat"
      ? "status-badge status-spam"
      : (status === "Alias" ? "status-badge status-alias" : (status === "Ignoriert" ? "status-badge status-ignored" : "status-badge status-default"));
    const qty = toNumber(item.quantity || 0);
    const usd = toNumber(item.usd_value || 0);
    const eur = usdToEur(usd);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="c-asset" title="${item.asset || ""}">${item.symbol || item.asset || ""}<br><small class="muted">${item.asset || ""}</small></td>
      <td class="c-name">${item.name || ""}</td>
      <td class="num c-qty ${qty < 0 ? "num-neg" : "num-pos"}">${formatQty(qty)}</td>
      <td class="num c-usd ${usd < 0 ? "num-neg" : "num-pos"}">${formatMoney(usd)}</td>
      <td class="num c-eur ${eur < 0 ? "num-neg" : "num-pos"}">${formatMoney(eur)}</td>
      <td class="c-status" title="${item.ignored_reason || ""}"><span class="${statusClass}">${status}</span></td>
    `;
    tr.addEventListener("click", () => {
      el("ignoreMint").value = item.asset || "";
      if (item.ignored_reason) el("ignoreReason").value = item.ignored_reason;
      setTokenQuickSelection(item);
    });
    tbody.appendChild(tr);
  });
  if (pageRows.length) {
    const sumUsdPage = pageRows.reduce((acc, row) => acc + toNumber(row.usd_value || 0), 0);
    const sumEurPage = usdToEur(sumUsdPage);
    const sumRow = document.createElement("tr");
    sumRow.className = "sum-row";
    sumRow.innerHTML = `
      <td class="c-asset">Summe (Seite)</td>
      <td class="c-name muted">rows=${pageRows.length}</td>
      <td class="num c-qty">-</td>
      <td class="num c-usd">${formatMoney(sumUsdPage)}</td>
      <td class="num c-eur">${formatMoney(sumEurPage)}</td>
      <td class="c-status muted">${currencyLabel()} aktiv</td>
    `;
    tbody.appendChild(sumRow);
  }
  if (!visible.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="6">Keine Token-Daten (ggf. alle ignoriert).</td>';
    tbody.appendChild(tr);
  }
  const info = el("dashTokenPageInfo");
  if (info) info.textContent = `${state.paging.tokenPage}/${totalPages} · ${visible.length} rows`;
  const prev = el("btnTokenPrev");
  const next = el("btnTokenNext");
  if (prev) prev.disabled = state.paging.tokenPage <= 1;
  if (next) next.disabled = state.paging.tokenPage >= totalPages;
  applyTableColumnVisibility("dashLiveTokenTable");
}

function setTokenQuickSelection(item) {
  if (!item) return;
  const mint = String(item.asset || "");
  const symbol = String(item.symbol || "");
  const name = String(item.name || "");
  const reason = String(item.ignored_reason || "");
  if (el("tokenQuickMint")) el("tokenQuickMint").value = mint;
  if (el("tokenQuickSymbol")) el("tokenQuickSymbol").value = symbol;
  if (el("tokenQuickName")) el("tokenQuickName").value = name;
  if (el("tokenQuickReason") && reason) el("tokenQuickReason").value = reason;
}

function clearTokenQuickSelection() {
  ["tokenQuickMint", "tokenQuickSymbol", "tokenQuickName", "tokenQuickReason"].forEach((id) => {
    if (el(id)) el(id).value = "";
  });
}

function renderTokenValueMix(rows) {
  const topRows = (rows || [])
    .map((row) => ({
      label: row.symbol || row.asset || "?",
      value: convertUsdForDisplay(row.usd_value || 0),
    }))
    .filter((row) => row.value > 0)
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);
  const labels = topRows.map((row) => row.label);
  const data = topRows.map((row) => row.value);
  buildChart("chartTokenValueMix", {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: ["#1f7acb", "#3e95d9", "#62ace6", "#88c1f0", "#b0d8f8", "#2f6699", "#6f9fca", "#9cc2e3"],
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${formatMoney(ctx.parsed)} ${currencyLabel()}`,
          },
        },
      },
    },
  });
}

function tokenStatusKey(item) {
  if (String(item?.ignored || "").toLowerCase() === "true") return "ignored";
  if (String(item?.spam_candidate || "").toLowerCase() === "true") return "spam";
  if ((item?.display_source || "") === "alias") return "alias";
  if ((item?.display_source || "") === "known") return "known";
  return "unknown";
}

function tokenStatusLabel(item) {
  const key = tokenStatusKey(item);
  if (key === "ignored") return "Ignoriert";
  if (key === "spam") return "Spam-Kandidat";
  if (key === "alias") return "Alias";
  if (key === "known") return "Bekannt";
  return "Unbekannt";
}

function compareTokenRows(a, b, mode) {
  const aUsd = toNumber(a.usd_value || 0);
  const bUsd = toNumber(b.usd_value || 0);
  const aEur = usdToEur(aUsd);
  const bEur = usdToEur(bUsd);
  const aQty = toNumber(a.quantity || 0);
  const bQty = toNumber(b.quantity || 0);
  if (mode === "usd_asc") return aUsd - bUsd;
  if (mode === "eur_desc") return bEur - aEur;
  if (mode === "eur_asc") return aEur - bEur;
  if (mode === "qty_desc") return bQty - aQty;
  if (mode === "qty_asc") return aQty - bQty;
  if (mode === "name_asc") {
    const an = String(a.symbol || a.asset || "").toLowerCase();
    const bn = String(b.symbol || b.asset || "").toLowerCase();
    return an.localeCompare(bn);
  }
  return bUsd - aUsd;
}

function renderLiveTokenStats(tokens) {
  const host = el("dashTokenStats");
  if (!host) return;
  const totalUsd = (tokens || []).reduce((acc, row) => acc + toNumber(row.usd_value || 0), 0);
  const totalEur = usdToEur(totalUsd);
  const positive = (tokens || []).filter((row) => toNumber(row.usd_value || 0) > 0).length;
  const spam = (tokens || []).filter((row) => tokenStatusKey(row) === "spam").length;
  const unknown = (tokens || []).filter((row) => tokenStatusKey(row) === "unknown").length;
  host.innerHTML = "";
  [
    { label: "Sichtbare Token", value: String(tokens?.length || 0), sub: "nach Filter" },
    { label: "Gesamtwert USD", value: formatMoney(totalUsd), sub: "sichtbarer Bereich" },
    { label: "Gesamtwert EUR", value: formatMoney(totalEur), sub: `FX ${formatMoney(state.fx.usdToEur)} EUR/USD` },
    { label: "Mit positivem USD", value: String(positive), sub: "größer 0" },
    { label: "Spam-Kandidaten", value: String(spam), sub: "prüfen/ignorieren" },
    { label: "Unbekannt", value: String(unknown), sub: "Alias empfohlen" },
  ].forEach((item) => {
    const card = document.createElement("div");
    card.className = "metric";
    card.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
    host.appendChild(card);
  });
}

function renderLiveSummaryCards(summary) {
  const host = el("dashLiveSummaryCards");
  if (!host) return;
  const totalUsd = toNumber(summary.total_estimated_usd || 0);
  const solUsd = toNumber(summary.sol_usd_value || 0);
  const totalDisplay = convertUsdForDisplay(totalUsd);
  const solDisplay = convertUsdForDisplay(solUsd);
  const items = [
    { label: "Wallet", value: summary.wallet || "-" },
    { label: `Total ${currencyLabel()}`, value: formatMoney(totalDisplay) },
    { label: "Total USD", value: formatMoney(totalUsd) },
    { label: "Total EUR", value: formatMoney(usdToEur(totalUsd)) },
    { label: "SOL", value: formatQty(summary.sol_balance || 0) },
    { label: `SOL ${currencyLabel()}`, value: formatMoney(solDisplay) },
    { label: "SOL USD", value: formatMoney(solUsd) },
    { label: "SOL EUR", value: formatMoney(usdToEur(solUsd)) },
    { label: "FX USD/EUR", value: formatMoney(state.fx.usdToEur) },
    { label: "Token", value: String(summary.token_count ?? 0) },
  ];
  host.innerHTML = "";
  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "metric";
    div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong>`;
    host.appendChild(div);
  });
}

function renderPnlCards(summary) {
  const host = el("dashPnlCards");
  if (!host) return;
  const startUsd = toNumber(summary?.start_value_usd || 0);
  const endUsd = toNumber(summary?.end_value_usd || 0);
  const pnlUsd = toNumber(summary?.pnl_abs_usd || 0);
  const startDisplay = convertUsdForDisplay(startUsd);
  const endDisplay = convertUsdForDisplay(endUsd);
  const pnlDisplay = convertUsdForDisplay(pnlUsd);
  const items = [
    { label: `Start ${currencyLabel()}`, value: formatMoney(startDisplay) },
    { label: `Ende ${currencyLabel()}`, value: formatMoney(endDisplay) },
    { label: `PnL ${currencyLabel()}`, value: formatMoney(pnlDisplay) },
    { label: "PnL %", value: summary?.pnl_pct ? `${summary.pnl_pct}%` : "-" },
  ];
  host.innerHTML = "";
  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "metric";
    div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong>`;
    host.appendChild(div);
  });
}

function renderCockpit() {
  const dashboard = state.dashboard || {};
  const tax = state.taxDomainSummary || {};
  const s = dashboard.summary || {};
  const anlage = tax.anlage_so || {};
  const euer = tax.euer || {};
  const term = tax.termingeschaefte || {};
  const cls = tax.classification_counts || {};

  const host = el("cockpitMainKpis");
  if (!host) return;
  host.innerHTML = "";
  const cards = [
    { label: "Events Gesamt", value: formatQty(s.total_events || 0), sub: "importiert" },
    { label: "Assets", value: formatQty(s.unique_assets || 0), sub: "erkannt" },
    { label: "SO Netto", value: formatMoney(toNumber(anlage.private_veraeusserung_net_taxable_eur || 0)), sub: "Anlage SO" },
    { label: "EÜR Ergebnis", value: formatMoney(toNumber(euer.betriebsergebnis_eur || 0)), sub: "betrieblich" },
    { label: "Termingeschäfte", value: formatMoney(toNumber(term.netto_eur || 0)), sub: "netto" },
    { label: "Unresolved", value: String(cls.unresolved_valuation_events || 0), sub: "Bewertung" },
  ];
  cards.forEach((item) => {
    const div = document.createElement("div");
    div.className = "metric";
    div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
    host.appendChild(div);
  });
  renderCockpitSources();

  buildChart("chartCockpitPortfolioTax", {
    type: "bar",
    data: {
      labels: ["SO Netto", "EÜR Ergebnis", "Termingeschäfte"],
      datasets: [
        {
          data: [
            toNumber(anlage.private_veraeusserung_net_taxable_eur || 0),
            toNumber(euer.betriebsergebnis_eur || 0),
            toNumber(term.netto_eur || 0),
          ],
          backgroundColor: ["#2f7fd1", "#5ca5e6", "#0f4f87"],
        },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderCockpitSources() {
  const cardsHost = el("cockpitSourceCards");
  const timelineHost = el("cockpitImportTimeline");
  if (cardsHost) {
    cardsHost.innerHTML = "";
    const rows = Array.isArray(state.integrationRows) ? state.integrationRows : [];
    const sources = rows.length
      ? rows.slice(0, 6)
      : [
          { integration_id: "solana_rpc", event_count: 0, asset_count: 0, source_file_count: 0 },
          { integration_id: "binance_api", event_count: 0, asset_count: 0, source_file_count: 0 },
          { integration_id: "file_import", event_count: 0, asset_count: 0, source_file_count: 0 },
        ];
    sources.forEach((item) => {
      const count = toNumber(item.event_count || 0);
      const card = document.createElement("button");
      card.className = `source-card ${count > 0 ? "source-card-ok" : "source-card-empty"}`;
      card.type = "button";
      card.innerHTML = `
        <span>${item.integration_id || "Quelle"}</span>
        <strong>${formatQty(count)}</strong>
        <small>${formatQty(item.asset_count || 0)} Assets · ${formatQty(item.source_file_count || 0)} Sources</small>
      `;
      card.addEventListener("click", () => switchStep("1"));
      cardsHost.appendChild(card);
    });
  }
  if (timelineHost) {
    timelineHost.innerHTML = "";
    const rows = Array.isArray(state.importSources) ? state.importSources.slice(0, 5) : [];
    rows.forEach((item) => {
      const li = document.createElement("li");
      const ts = String(item.created_at_utc || "-").replace("T", " ").slice(0, 16);
      li.innerHTML = `<strong>${ts}</strong><span>${item.source_name || "Import"} · ${formatQty(item.imported_event_count || 0)} Events</span>`;
      timelineHost.appendChild(li);
    });
    if (!rows.length) {
      const li = document.createElement("li");
      li.innerHTML = "<strong>Noch leer</strong><span>Verbinde Solana, Binance oder CSV/XLS-Importe.</span>";
      timelineHost.appendChild(li);
    }
  }
}

function applyGlobalSearch() {
  const query = String(el("globalSearch")?.value || "").trim();
  if (!query) return;
  const normalized = query.toUpperCase();
  const tab = currentReviewTab();
  if (tab === "holdings" || tab === "cockpit" || tab === "performance") {
    if (el("dashTokenSearch")) el("dashTokenSearch").value = query;
    state.paging.tokenPage = 1;
    const tokens = state.dashboard?.last_live_tokens ?? [];
    if (Array.isArray(tokens)) renderLiveTokenTable(tokens);
    switchStep("4");
    switchReviewTab("holdings");
    return;
  }
  if (tab === "transfers") {
    if (el("reviewTransferSearch")) el("reviewTransferSearch").value = query;
    state.paging.transferPage = 1;
    renderTransferLedger(state.transferLedger);
    return;
  }
  if (tab === "tax" || tab === "trading" || tab === "mining") {
    if (el("taxFilterAsset")) el("taxFilterAsset").value = normalized;
    state.paging.taxPage = 1;
    renderTaxTable();
    switchStep("4");
    switchReviewTab("tax");
  }
}

function renderTaxDomainSummaryVisual(summary) {
  const anlage = summary?.anlage_so || {};
  const euer = summary?.euer || {};
  const term = summary?.termingeschaefte || {};
  const cls = summary?.classification_counts || {};

  const cards = [
    { label: "SO Leistungen", value: formatMoney(toNumber(anlage.leistungen_income_eur || 0)), sub: "Anlage SO" },
    { label: "SO Veräußerung Netto", value: formatMoney(toNumber(anlage.private_veraeusserung_net_taxable_eur || 0)), sub: "steuerpflichtig" },
    { label: "EÜR Betriebsergebnis", value: formatMoney(toNumber(euer.betriebsergebnis_eur || 0)), sub: "Einnahmen - Ausgaben" },
    { label: "Termingeschäfte Netto", value: formatMoney(toNumber(term.netto_eur || 0)), sub: "Derivate/Liquidationen" },
    { label: "Reward Events", value: String(cls.reward_events || 0), sub: "klassifiziert" },
    { label: "Unresolved Bewertung", value: String(cls.unresolved_valuation_events || 0), sub: "manuell prüfen" },
  ];

  const host = el("taxDomainKpiCards");
  if (host) {
    host.innerHTML = "";
    cards.forEach((item) => {
      const div = document.createElement("div");
      div.className = "metric";
      div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
      host.appendChild(div);
    });
  }

  buildChart("chartTaxDomains", {
    type: "bar",
    data: {
      labels: ["SO Leistungen", "SO Netto", "EÜR Ergebnis", "Termingeschäfte"],
      datasets: [
        {
          data: [
            toNumber(anlage.leistungen_income_eur || 0),
            toNumber(anlage.private_veraeusserung_net_taxable_eur || 0),
            toNumber(euer.betriebsergebnis_eur || 0),
            toNumber(term.netto_eur || 0),
          ],
          backgroundColor: ["#2f7fd1", "#4f9fe8", "#1f6ab4", "#0f4f87"],
          borderColor: "#1f4f79",
          borderWidth: 1,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  });

  buildChart("chartTaxClassification", {
    type: "doughnut",
    data: {
      labels: ["Rewards", "Mining", "Data Credits", "Unresolved"],
      datasets: [
        {
          data: [
            Number(cls.reward_events || 0),
            Number(cls.mining_events || 0),
            Number(cls.data_credit_events || 0),
            Number(cls.unresolved_valuation_events || 0),
          ],
          backgroundColor: ["#2f7fd1", "#66aeea", "#8bc4f5", "#ffd37e"],
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
    },
  });

  renderMiningPanel();
  renderTradingPanel();
}

function renderMiningPanel() {
  const dashboard = state.dashboard || {};
  const tax = state.taxDomainSummary || {};
  const cls = tax.classification_counts || {};
  const anlage = tax.anlage_so || {};
  const euer = tax.euer || {};
  const assets = Array.isArray(dashboard.asset_balances) ? dashboard.asset_balances : [];
  const miningAssets = assets.filter((item) => {
    const symbol = String(item.symbol || item.asset || "").toUpperCase();
    const name = String(item.name || "").toLowerCase();
    return ["HNT", "IOT", "MOBILE", "DC", "MYST"].includes(symbol) ||
      name.includes("helium") ||
      name.includes("mobile") ||
      name.includes("iot");
  }).slice(0, 12);

  const host = el("miningKpiCards");
  if (host) {
    host.innerHTML = "";
    [
      { label: "Reward Events", value: String(cls.reward_events || 0), sub: "Mining/Staking/Rewards" },
      { label: "Mining Events", value: String(cls.mining_events || 0), sub: "Helium/PoC" },
      { label: "Data Credits", value: String(cls.data_credit_events || 0), sub: "Gebühren/Verbrauch" },
      { label: "SO Leistungen EUR", value: formatMoney(anlage.leistungen_income_eur || 0), sub: "privat, falls zutreffend" },
      { label: "EÜR Ergebnis EUR", value: formatMoney(euer.betriebsergebnis_eur || 0), sub: "gewerblich, falls zutreffend" },
      { label: "Unbewertet", value: String(cls.unresolved_valuation_events || 0), sub: "FX/Preis fehlt" },
    ].forEach((item) => {
      const div = document.createElement("div");
      div.className = "metric";
      div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
      host.appendChild(div);
    });
  }

  buildChart("chartMiningRewards", {
    type: "doughnut",
    data: {
      labels: ["Rewards", "Mining", "Data Credits", "Unbewertet"],
      datasets: [
        {
          data: [
            Number(cls.reward_events || 0),
            Number(cls.mining_events || 0),
            Number(cls.data_credit_events || 0),
            Number(cls.unresolved_valuation_events || 0),
          ],
          backgroundColor: ["#f3ba2f", "#4da3ff", "#79e0b7", "#ff7b86"],
        },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "bottom" } } },
  });

  const tbody = el("miningAssetTable")?.querySelector("tbody");
  if (tbody) {
    tbody.innerHTML = "";
    miningAssets.forEach((item) => {
      const qty = toNumber(item.quantity || 0);
      const symbol = item.symbol || item.asset || "";
      const category = String(symbol).toUpperCase() === "DC" ? "Data Credit / Gebühr" : "Mining/Reward prüfen";
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${symbol}</td>
        <td>${item.name || ""}</td>
        <td class="num ${qty < 0 ? "num-neg" : "num-pos"}">${formatQty(qty)}</td>
        <td>${category}</td>
      `;
      tbody.appendChild(tr);
    });
    if (!miningAssets.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="4">Noch keine Mining/Helium-Assets im Dashboard erkannt.</td>';
      tbody.appendChild(tr);
    }
  }
}

function renderTradingPanel() {
  const tax = state.taxDomainSummary || {};
  const anlage = tax.anlage_so || {};
  const term = tax.termingeschaefte || {};
  const lines = Array.isArray(state.taxLines) ? state.taxLines : [];
  const taxableLines = lines.filter((line) => line.tax_status === "taxable").length;
  const exemptLines = lines.filter((line) => line.tax_status === "exempt").length;
  const gain = lines.reduce((acc, line) => acc + toNumber(line.gain_loss_eur || 0), 0);

  const host = el("tradingKpiCards");
  if (host) {
    host.innerHTML = "";
    [
      { label: "Tax Lines", value: String(lines.length), sub: "Spot/FIFO" },
      { label: "Steuerpflichtig", value: String(taxableLines), sub: "unter Haltefrist" },
      { label: "Steuerfrei", value: String(exemptLines), sub: "Haltedauer erfüllt" },
      { label: "PnL Tax Lines EUR", value: formatMoney(gain), sub: "aktuell geladene Lines" },
      { label: "SO Netto EUR", value: formatMoney(anlage.private_veraeusserung_net_taxable_eur || 0), sub: "steuerpflichtig" },
      { label: "Termingeschäfte EUR", value: formatMoney(term.netto_eur || 0), sub: "separater Topf" },
    ].forEach((item) => {
      const div = document.createElement("div");
      div.className = "metric";
      div.innerHTML = `<span>${item.label}</span><strong>${item.value}</strong><small class="sub">${item.sub}</small>`;
      host.appendChild(div);
    });
  }

  buildChart("chartTradingTaxImpact", {
    type: "bar",
    data: {
      labels: ["Tax Lines PnL", "SO Netto", "Termingeschäfte"],
      datasets: [
        {
          data: [
            gain,
            toNumber(anlage.private_veraeusserung_net_taxable_eur || 0),
            toNumber(term.netto_eur || 0),
          ],
          backgroundColor: ["#4da3ff", "#f3ba2f", "#79e0b7"],
        },
      ],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });

  const grouped = new Map();
  lines.forEach((line) => {
    const asset = String(line.asset || "?");
    const current = grouped.get(asset) || { asset, count: 0, qty: 0, gain: 0 };
    current.count += 1;
    current.qty += toNumber(line.qty || 0);
    current.gain += toNumber(line.gain_loss_eur || 0);
    grouped.set(asset, current);
  });
  const rows = Array.from(grouped.values()).sort((a, b) => Math.abs(b.gain) - Math.abs(a.gain)).slice(0, 12);
  const tbody = el("tradingAssetTable")?.querySelector("tbody");
  if (tbody) {
    tbody.innerHTML = "";
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const hint = row.count > 250 ? "Bot-/High-Frequency prüfen" : "normal";
      tr.innerHTML = `
        <td>${row.asset}</td>
        <td class="num">${row.count}</td>
        <td class="num">${formatQty(row.qty)}</td>
        <td class="num ${row.gain < 0 ? "num-neg" : "num-pos"}">${formatMoney(row.gain)}</td>
        <td>${hint}</td>
      `;
      tbody.appendChild(tr);
    });
    if (!rows.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="5">Noch keine Tax Lines geladen. Öffne Steuer-Tab und lade Tax Lines.</td>';
      tbody.appendChild(tr);
    }
  }
}

async function refreshWalletSnapshotChart(scope, entityId) {
  if (!entityId) return;
  const windowDays = Number(el("dashSnapshotWindow")?.value || "30");
  const query = new URLSearchParams({
    scope,
    entity_id: entityId,
    window_days: String(windowDays),
  }).toString();
  const data = await callApi(`/api/v1/dashboard/wallet-snapshots?${query}`, "GET", null, null, true);
  if (!data || data.status !== "success") return;
  state.dashboard = state.dashboard || {};
  state.dashboard.lastSnapshot = {
    scope,
    entity_id: entityId,
    payload: data.data || {},
  };
  rerenderWalletSnapshotFromState();
}

function rerenderWalletSnapshotFromState() {
  const payload = state.dashboard?.lastSnapshot?.payload;
  if (!payload) return;
  const points = payload.performance_points ?? [];
  const labels = points.map((p) => String(p.timestamp_utc || "").replace("T", " ").slice(5, 16));
  const values = points.map((p) => convertUsdForDisplay(p.value_usd || 0));
  renderPnlCards(payload.summary ?? {});
  buildChart("chartWalletSnapshots", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: `Wallet Value (${currencyLabel()})`,
          data: values,
          borderColor: "#1f7acb",
          backgroundColor: "rgba(31,122,203,0.15)",
          fill: true,
          tension: 0.25,
          pointRadius: 1.5,
        },
      ],
    },
    options: { maintainAspectRatio: false, scales: { y: { beginAtZero: false } } },
  });
}

function parseWalletAddresses(raw) {
  const values = String(raw || "")
    .split(/[\n,;]/g)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
  return Array.from(new Set(values));
}

function selectedWalletGroup() {
  const id = el("wgSelect").value;
  return state.walletGroups.find((group) => String(group.group_id) === String(id)) || null;
}

function fillWalletGroupForm(group) {
  if (!group) {
    el("wgName").value = "";
    el("wgDescription").value = "";
    el("wgWallets").value = "";
    renderWalletGroupSourceFilters(null);
    return;
  }
  el("wgName").value = group.name || "";
  el("wgDescription").value = group.description || "";
  el("wgWallets").value = (group.wallet_addresses || []).join("\n");
  renderWalletGroupSourceFilters(group);
}

function renderWalletGroups(groups) {
  state.walletGroups = Array.isArray(groups) ? groups : [];
  const select = el("wgSelect");
  select.innerHTML = "";
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "-- Neue Gruppe --";
  select.appendChild(empty);

  state.walletGroups.forEach((group) => {
    const opt = document.createElement("option");
    opt.value = group.group_id;
    const walletCount = Array.isArray(group.wallet_addresses) ? group.wallet_addresses.length : 0;
    opt.textContent = `${group.name} (${walletCount} Wallets)`;
    select.appendChild(opt);
  });

  if (state.selectedWalletGroupId) {
    select.value = state.selectedWalletGroupId;
  }
  fillWalletGroupForm(selectedWalletGroup());
  renderWalletGroupsTable(state.walletGroups);
  if (state.selectedWalletGroupId) {
    void refreshPortfolioSetHistory(state.selectedWalletGroupId);
  }
  renderConnectorWizard();
}

async function loadWalletGroups() {
  const res = await callApi("/api/v1/wallet-groups", "GET", null, null, true);
  if (res?.status !== "success") return;
  const groups = res.data?.groups ?? [];
  renderWalletGroups(groups);
  el("wgOut").textContent = JSON.stringify(res.data ?? {}, null, 2);
}

function renderAliasTable(aliases) {
  const tbody = el("aliasTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (aliases || []).forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.mint || ""}</td>
      <td>${item.symbol || ""}</td>
      <td>${item.name || ""}</td>
      <td>${item.notes || ""}</td>
    `;
    tr.addEventListener("click", () => {
      el("aliasMint").value = item.mint || "";
      el("aliasSymbol").value = item.symbol || "";
      el("aliasName").value = item.name || "";
      el("aliasNotes").value = item.notes || "";
    });
    tbody.appendChild(tr);
  });
  if (!aliases?.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="4">Keine Alias-Einträge.</td>';
    tbody.appendChild(tr);
  }
}

async function loadTokenAliases() {
  const res = await callApi("/api/v1/admin/token-aliases", "GET", null, null, true);
  if (res?.status !== "success") return;
  state.admin.aliases = res.data?.aliases ?? [];
  renderAliasTable(state.admin.aliases);
}

function renderIgnoreTable(items) {
  const tbody = el("ignoreTable")?.querySelector("tbody");
  if (!tbody) return;
  tbody.innerHTML = "";
  (items || []).forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.mint || ""}</td>
      <td>${item.reason || ""}</td>
      <td>${item.updated_at_utc || ""}</td>
    `;
    tr.addEventListener("click", () => {
      el("ignoreMint").value = item.mint || "";
      el("ignoreReason").value = item.reason || "";
    });
    tbody.appendChild(tr);
  });
  if (!items?.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = '<td colspan="3">Keine Ignore-Einträge.</td>';
    tbody.appendChild(tr);
  }
}

async function loadIgnoredTokens() {
  const res = await callApi("/api/v1/admin/ignored-tokens", "GET", null, null, true);
  if (res?.status !== "success") return;
  state.admin.ignoredTokens = res.data?.ignored_tokens ?? [];
  renderIgnoreTable(state.admin.ignoredTokens);
}

async function loadTaxAudit(lineNo) {
  const jobId = currentJobId();
  if (!jobId) {
    showToast("Bitte zuerst eine job_id eintragen.", "warn");
    return;
  }
  const data = await callApi(`/api/v1/audit/tax-line/${jobId}/${lineNo}`, "GET", null, null, true);
  if (!data) return;
  if (data.status === "error") {
    el("taxAuditOut").textContent = JSON.stringify(data, null, 2);
    showToast(`Audit fehlgeschlagen: ${data.errors?.[0]?.message ?? "unknown"}`, "err");
    return;
  }
  el("taxAuditOut").textContent = JSON.stringify(data.data, null, 2);
  showToast(`Audit geladen für Tax Line ${lineNo}.`, "ok");
}

async function loadTaxDomainSummary(jobId = currentJobId(), silent = true) {
  if (!jobId) return;
  const data = await callApi(`/api/v1/process/tax-domain-summary/${jobId}`, "GET", null, null, silent);
  if (!data) return;
  if (data.status === "success") {
    const summary = data.data?.tax_domain_summary || {};
    state.taxDomainSummary = summary;
    el("taxDomainSummaryOut").textContent = JSON.stringify(summary, null, 2);
    renderTaxDomainSummaryVisual(summary);
    renderCockpit();
  } else if (!silent) {
    el("taxDomainSummaryOut").textContent = JSON.stringify(data, null, 2);
  }
}

async function refreshTaxReviewData(jobId = currentJobId(), silent = true) {
  if (!jobId) return;
  const status = await callApi(`/api/v1/process/status/${jobId}`, "GET", null, null, silent);
  if (status?.data) {
    updateMetrics(status.data);
  }
  const taxData = await callApi(`/api/v1/process/tax-lines/${jobId}`, "GET", null, null, silent);
  if (taxData?.data?.lines) {
    state.taxLines = taxData.data.lines;
    state.paging.taxPage = 1;
    renderTaxTable();
  }
  const derivData = await callApi(`/api/v1/process/derivative-lines/${jobId}`, "GET", null, null, silent);
  if (derivData?.data?.lines) {
    state.derivativeLines = derivData.data.lines;
    state.paging.derivPage = 1;
    renderDerivativeTable();
  }
  await loadTaxDomainSummary(jobId, silent);
  await loadReportFiles(jobId, true);
}

function renderReportFiles() {
  const host = el("reportFilesGrid");
  if (!host) return;
  const rows = state.reportFiles || [];
  host.innerHTML = "";
  rows.forEach((item) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "source-card action-card";
    const partLabel = item.part_count && item.part_count > 1 ? `Teil ${item.part}/${item.part_count}` : "komplett";
    card.innerHTML = `
      <span>${item.label || item.file_id || "Export"}</span>
      <strong>${String(item.format || "").toUpperCase()} · ${item.scope || "-"}</strong>
      <small>${formatInt(item.row_count || 0)} Zeilen · ${partLabel}</small>
    `;
    card.addEventListener("click", () => {
      if (!item.download_url) return;
      window.open(item.download_url, "_blank", "noopener");
    });
    host.appendChild(card);
  });
  if (!rows.length) {
    host.innerHTML = `<div class="muted">Keine Export-Artefakte vorhanden. Starte zuerst einen erfolgreichen Steuerlauf.</div>`;
  }
  const info = el("reportFilesInfo");
  if (info) {
    info.textContent = rows.length ? `${rows.length} Export-Dateien verfügbar.` : "Keine Export-Dateien verfügbar.";
  }
}

async function loadReportFiles(jobId = currentJobId(), silent = true) {
  if (!jobId) {
    if (!silent) showToast("Bitte zuerst eine job_id eintragen.", "warn");
    return;
  }
  const data = await callApi(`/api/v1/report/files/${jobId}`, "GET", null, null, silent);
  if (!data?.data) return;
  state.reportFiles = data.data.files || [];
  renderReportFiles();
}

function renderIntegrityActionResult(items) {
  const host = el("integrityActionResult");
  if (!host) return;
  host.innerHTML = (items || [])
    .map((item) => `<span><strong>${item.label}:</strong> ${item.value}</span>`)
    .join("");
}

async function compareCurrentRuleset(trigger = null) {
  const jobId = currentJobId();
  if (!jobId) {
    showToast("Bitte zuerst eine job_id eintragen.", "warn");
    return;
  }
  const compareRulesetId = (el("compareRulesetId")?.value || "").trim() || rulesetForYear(el("taxYear")?.value || "2026");
  const compareRulesetVersion = (el("compareRulesetVersion")?.value || "").trim() || null;
  const data = await callApi(
    "/api/v1/process/compare-rulesets",
    "POST",
    {
      job_id: jobId,
      compare_ruleset_id: compareRulesetId,
      compare_ruleset_version: compareRulesetVersion,
    },
    trigger
  );
  if (data?.status !== "success") return;
  const baseSo = data.data?.base?.tax_domain_summary?.anlage_so || {};
  const compareSo = data.data?.comparison?.tax_domain_summary?.anlage_so || {};
  renderIntegrityActionResult([
    { label: "Job", value: jobId },
    { label: "Basis", value: `${data.data?.base?.ruleset_id || "-"} ${data.data?.base?.ruleset_version || ""}` },
    { label: "Vergleich", value: `${compareRulesetId} ${compareRulesetVersion || ""}` },
    { label: "SO Basis Netto", value: formatCurrency(baseSo.private_veraeusserung_net_taxable_eur || 0, "EUR") },
    { label: "SO Vergleich Netto", value: formatCurrency(compareSo.private_veraeusserung_net_taxable_eur || 0, "EUR") },
  ]);
  showToast("Ruleset-Vergleich berechnet.", "ok");
}

async function createCurrentSnapshot(trigger = null) {
  const jobId = currentJobId();
  if (!jobId) {
    showToast("Bitte zuerst eine job_id eintragen.", "warn");
    return;
  }
  const notes = (el("snapshotNote")?.value || "").trim() || null;
  const data = await callApi(
    `/api/v1/snapshots/create/${jobId}`,
    "POST",
    { notes },
    trigger
  );
  if (data?.status !== "success") return;
  renderIntegrityActionResult([
    { label: "Snapshot", value: data.data?.snapshot_id || "-" },
    { label: "Job", value: data.data?.job_id || jobId },
    { label: "Erstellt", value: data.data?.created_at_utc || "-" },
    { label: "Notiz", value: data.data?.notes || "-" },
  ]);
  showToast("Snapshot erstellt.", "ok");
}

async function loadTaxEventOverrides(silent = true) {
  const data = await callApi("/api/v1/tax/event-overrides", "GET", null, null, silent);
  if (!data?.data) return;
  state.taxEventOverrides = data.data.rows || [];
  renderTaxEventOverrideTable(state.taxEventOverrides);
}

async function loadLatestProcessJob(silent = true) {
  const data = await callApi("/api/v1/process/latest", "GET", null, null, silent);
  const job = data?.data?.job;
  if (!job || !job.job_id) return;
  el("jobId").value = String(job.job_id);
  updateMetrics(job);
  await refreshTaxReviewData(String(job.job_id), true);
}

function init() {
  el("eventsJson").value = JSON.stringify(defaultEvents, null, 2);
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".guided-action");
    if (!button) return;
    const kind = button.dataset.preflightKind;
    const idx = Number(button.dataset.preflightIndex || "-1");
    const source = state.preflight?.[kind];
    const action = Array.isArray(source) && idx >= 0 ? source[idx]?.action : null;
    applyPreflightAction(action);
  });
  if (el("cexEndDate") && !el("cexEndDate").value) {
    el("cexEndDate").value = new Date().toISOString().slice(0, 10);
  }
  const denseMode = loadPref("denseMode", "0") === "1";
  document.body.classList.toggle("dense-table", denseMode);
  if (el("uiDenseMode")) {
    el("uiDenseMode").checked = denseMode;
  }
  const expertMode = loadPref("expertMode", "0") === "1";
  setExpertMode(expertMode);
  [
    ["uiDisplayCurrency", "eur"],
    ["dashTokenSearch", ""],
    ["dashTokenStatusFilter", ""],
    ["dashTokenSort", "usd_desc"],
    ["dashShowIgnored", "0"],
    ["dashTokenPageSize", "50"],
    ["dashLotAsset", ""],
    ["dashLotAsOf", ""],
    ["taxFilterAsset", ""],
    ["taxFilterStatus", ""],
    ["taxPageSize", "50"],
    ["derivFilterAsset", ""],
    ["derivFilterType", ""],
    ["derivPageSize", "50"],
    ["dashSnapshotWindow", "30"],
    ["reviewTransferSearch", ""],
    ["reviewTransferStatus", ""],
    ["reviewTransferPageSize", "50"],
    ["reviewIssueSearch", ""],
    ["reviewIssueStatus", ""],
    ["reviewIssuePageSize", "50"],
    ["importJobIntegration", ""],
    ["importJobStatus", ""],
    ["processRunMode", "default"],
    ["processJobStatus", ""],
    ["processJobsAutoRefresh", ""],
    ["processJobSearch", ""],
    ["processJobsSort", "updated_at"],
    ["processJobsSortDir", "desc"],
    ["processJobsLimit", "25"],
    ["processJobsOffset", "0"],
    ["taxYear", "2026"],
  ].forEach(([id, fallback]) => {
    const node = el(id);
    if (!node) return;
    const value = loadPref(`field.${id}`, fallback);
    if (node.type === "checkbox") {
      node.checked = value === "1";
    } else {
      node.value = value;
    }
  });
  state.ui.displayCurrency = String(el("uiDisplayCurrency")?.value || "eur").toLowerCase();
  state.processingJobsMode = String(el("processRunMode")?.value || "default");
  state.processingJobsAutoRefreshSec = String(el("processJobsAutoRefresh")?.value || "");
  state.processingJobsLimit = Number(el("processJobsLimit")?.value || 25);
  state.processingJobsOffset = Number(el("processJobsOffset")?.value || 0);
  syncTaxRunSelection();
  let savedStep = "4";
  let savedReview = "cockpit";
  let savedCollapsed = false;
  try {
    savedStep = localStorage.getItem("ui.step") || "4";
    savedReview = localStorage.getItem("ui.reviewTab") || "cockpit";
    savedCollapsed = localStorage.getItem("ui.railCollapsed") === "1";
  } catch (_) {}
  if (!STEP_LABELS[savedStep]) savedStep = "4";
  if (!REVIEW_LABELS[savedReview]) savedReview = "cockpit";
  switchStep(savedStep);
  switchReviewTab(savedReview);
  setRailCollapsed(savedCollapsed);
  setCsvButtonsDisabled(true, "Review-Gates noch nicht geprüft.");
  renderReviewGates(null);
  refreshPresetUi();
  pingApi();
  loadAdminData();
  refreshUsdEurRateBestEffort().then(() => {
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    if (Array.isArray(lastTokens) && lastTokens.length > 0) {
      renderLiveTokenTable(lastTokens);
    }
  });
  loadDashboard();
  loadProcessOptions();
  loadWalletGroups();
  loadReviewGates(true);
  loadIntegrationOverview();
  loadImportSourcesSummary();
  loadTaxEventOverrides(true);
  loadLatestProcessJob(true);

  $$(".step").forEach((btn) => {
    btn.addEventListener("click", () => {
      guardedSwitchStep(btn.dataset.step);
    });
  });
  $$(".admin-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchAdminTab(btn.dataset.adminTab));
  });
  $$(".review-tab").forEach((btn) => {
    btn.addEventListener("click", () => switchReviewTab(btn.dataset.reviewTab));
  });
  $$(".workflow-go").forEach((btn) => {
    btn.addEventListener("click", () => {
      const step = btn.dataset.stepGo || "1";
      const ok = guardedSwitchStep(step);
      if (!ok) return;
      if (step === "4") {
        switchReviewTab("cockpit");
      }
    });
  });
  el("btnNextAction")?.addEventListener("click", runNextAction);
  el("btnNextActionInline")?.addEventListener("click", runNextAction);
  $$(".rail-link").forEach((btn) => {
    btn.addEventListener("click", () => {
      const step = btn.dataset.railStep || "1";
      const review = btn.dataset.railReview || "";
      const ok = guardedSwitchStep(step);
      if (!ok) return;
      if (step === "4" && review) {
        switchReviewTab(review);
      } else if (step === "4") {
        switchReviewTab("cockpit");
      }
    });
  });
  el("btnMiningOpenTax")?.addEventListener("click", () => switchReviewTab("tax"));
  el("btnMiningOpenHoldings")?.addEventListener("click", () => switchReviewTab("holdings"));
  el("btnMiningRefresh")?.addEventListener("click", async () => {
    await loadDashboard();
    if (currentJobId()) await refreshTaxReviewData(currentJobId(), true);
  });
  el("btnTradingOpenTax")?.addEventListener("click", () => switchReviewTab("tax"));
  el("btnTradingRunProcess")?.addEventListener("click", () => switchStep("3"));
  el("btnTradingRefresh")?.addEventListener("click", async () => {
    await loadDashboard();
    if (currentJobId()) await refreshTaxReviewData(currentJobId(), true);
  });
  el("btnRailToggle")?.addEventListener("click", () => {
    const shell = document.querySelector(".app-shell");
    const collapsed = !shell?.classList.contains("rail-collapsed");
    setRailCollapsed(collapsed);
  });
  el("wgSelect").addEventListener("change", () => {
    state.selectedWalletGroupId = el("wgSelect").value || "";
    fillWalletGroupForm(selectedWalletGroup());
    if (state.selectedWalletGroupId) {
      refreshWalletSnapshotChart("group", state.selectedWalletGroupId);
      refreshPortfolioSetHistory(state.selectedWalletGroupId);
    }
  });

  el("btnPing").addEventListener("click", pingApi);
  el("btnLoadSample").addEventListener("click", () => {
    el("eventsJson").value = JSON.stringify(defaultEvents, null, 2);
    showToast("Sample geladen.", "ok");
  });
  el("btnValidateJson").addEventListener("click", () => {
    try {
      const rows = parseEventsJson();
      showToast(`JSON gültig: ${rows.length} Events`, "ok");
    } catch (error) {
      showToast(`JSON ungültig: ${error.message}`, "err");
    }
  });

  el("btnImport").addEventListener("click", async (e) => {
    try {
      const rows = parseEventsJson();
      const sourceName = el("sourceName").value.trim() || "manual-ui.csv";
      const data = await callApi(
        "/api/v1/import/confirm",
        "POST",
        { source_name: sourceName, rows },
        e.currentTarget
      );
      if (data?.status === "success") {
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        switchStep(2);
      }
    } catch (error) {
      showToast(`Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnBulkFolderImport")?.addEventListener("click", async (e) => {
    try {
      const folderPath = (el("bulkFolderPath")?.value || "usertransfer").trim() || "usertransfer";
      const recursive = !!el("bulkFolderRecursive")?.checked;
      const dryRun = !!el("bulkFolderDryRun")?.checked;
      const maxFiles = Number(el("bulkFolderMaxFiles")?.value || "500");
      const data = await callApi(
        "/api/v1/import/bulk-folder",
        "POST",
        {
          folder_path: folderPath,
          recursive,
          dry_run: dryRun,
          max_files: Math.max(1, Math.min(maxFiles, 5000)),
          max_rows_per_file: 200000,
        },
        e.currentTarget
      );
      if (data?.status === "success") {
        if (el("bulkFolderOut")) {
          el("bulkFolderOut").textContent = JSON.stringify(data.data || {}, null, 2);
        }
        await loadDashboard();
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        const inserted = Number(data.data?.inserted_events || 0);
        const duplicates = Number(data.data?.duplicate_events || 0);
        const processed = Number(data.data?.processed_files || 0);
        showToast(`Bulk-Ordnerimport: Dateien=${processed}, inserted=${inserted}, duplicates=${duplicates}`, "ok");
        switchStep(2);
      }
    } catch (error) {
      showToast(`Bulk-Ordnerimport abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnCexVerify").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      await callApi("/api/v1/connectors/cex/verify", "POST", payload, e.currentTarget);
    } catch (error) {
      showToast(`CEX Verify abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnCexLoadSaved").addEventListener("click", async () => {
    const connector = el("cexConnector").value.trim();
    const creds = await loadSavedCexCredentials(connector);
    if (!creds) {
      showToast("Keine gespeicherten Credentials gefunden.", "warn");
      return;
    }
    el("cexApiKey").value = creds.api_key || "";
    el("cexApiSecret").value = creds.api_secret || "";
    el("cexPassphrase").value = creds.passphrase || "";
    showToast("Gespeicherte Credentials geladen.", "ok");
  });

  el("btnCexBalances").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      const data = await callApi("/api/v1/connectors/cex/balances-preview", "POST", payload, e.currentTarget);
      if (data?.data?.rows) {
        el("eventsJson").value = JSON.stringify(data.data.rows, null, 2);
      }
    } catch (error) {
      showToast(`Balances Preview abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnCexTxPreview").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      const data = await callApi("/api/v1/connectors/cex/transactions-preview", "POST", payload, e.currentTarget);
      if (data?.data?.rows) {
        el("eventsJson").value = JSON.stringify(data.data.rows, null, 2);
      }
    } catch (error) {
      showToast(`Transactions Preview abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnCexImport").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      payload.source_name = `${payload.connector_id}_api_import`;
      const data = await callApi("/api/v1/connectors/cex/import-confirm", "POST", payload, e.currentTarget);
      if (data?.status === "success") {
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        switchStep(2);
      }
    } catch (error) {
      showToast(`CEX Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnCexImportFull").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      const data = await callApi(
        "/api/v1/connectors/cex/import-full-history",
        "POST",
        {
          connector_id: payload.connector_id,
          api_key: payload.api_key,
          api_secret: payload.api_secret,
          passphrase: payload.passphrase || null,
          start_time_ms: payload.start_time_ms,
          end_time_ms: payload.end_time_ms,
          window_days: 30,
          max_rows_per_call: Math.max(200, Math.min(payload.max_rows, 1000)),
        },
        e.currentTarget
      );
      if (data?.status === "success" || data?.status === "partial") {
        const summary = {
          connector_id: data.data?.connector_id,
          start_time_ms: data.data?.start_time_ms,
          end_time_ms: data.data?.end_time_ms,
          window_days: data.data?.window_days,
          windows_processed: data.data?.windows_processed,
          total_fetched_rows: data.data?.total_fetched_rows,
          total_inserted_events: data.data?.total_inserted_events,
          total_duplicate_events: data.data?.total_duplicate_events,
        };
        el("cexImportSummary").textContent = JSON.stringify(summary, null, 2);
        if (Number(data.data?.total_fetched_rows || 0) === 0) {
          showToast("Import lief, aber keine historischen Rows gefunden (Zeitraum/API-Restriktion prüfen).", "warn");
        } else {
          showToast(
            `Historie importiert: fetched=${summary.total_fetched_rows}, inserted=${summary.total_inserted_events}, duplicates=${summary.total_duplicate_events}`,
            "ok"
          );
        }
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        switchStep(2);
      }
    } catch (error) {
      showToast(`Full-History Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolPreview").addEventListener("click", async (e) => {
    try {
      const payload = solanaPayload();
      const data = await callApi("/api/v1/connectors/solana/wallet-preview", "POST", payload, e.currentTarget);
      if (data?.data?.rows) {
        el("eventsJson").value = JSON.stringify(data.data.rows, null, 2);
      }
      if (data?.data?.last_signature) {
        el("solBeforeSignature").value = data.data.last_signature;
      }
    } catch (error) {
      showToast(`Solana Preview abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolProbe").addEventListener("click", async (e) => {
    try {
      const payload = solanaPayload();
      const data = await callApi("/api/v1/connectors/solana/rpc-probe", "POST", {
        rpc_url: payload.rpc_url,
        rpc_fallback_urls: payload.rpc_fallback_urls,
      }, e.currentTarget);
      renderSolanaProbe(data?.data ?? null);
    } catch (error) {
      showToast(`RPC Probe abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolImport").addEventListener("click", async (e) => {
    try {
      const payload = solanaPayload();
      payload.source_name = "solana_wallet_api_import";
      const data = await callApi("/api/v1/connectors/solana/import-confirm", "POST", payload, e.currentTarget);
      if (data?.status === "success") {
        if (data?.data?.last_signature) {
          el("solBeforeSignature").value = data.data.last_signature;
        }
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        switchStep(2);
      }
    } catch (error) {
      showToast(`Solana Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolImportFull").addEventListener("click", async (e) => {
    try {
      const payload = solanaFullHistoryPayload();
      payload.source_name = `${payload.wallet_address}_full_import`;
      payload.max_signatures_per_call = Math.max(100, Number(el("solMaxSignatures").value || "1000"));
      const data = await callApi(
        "/api/v1/connectors/solana/import-full-history",
        "POST",
        payload,
        e.currentTarget
      );
      if (data?.status === "success" || data?.status === "partial") {
        const summary = {
          wallet_address: data.data?.wallet_address,
          calls: data.data?.calls,
          chunks_processed: data.data?.chunks_processed,
          scanned_signatures: data.data?.scanned_signatures,
          total_fetched_rows: data.data?.total_fetched_rows,
          total_inserted_events: data.data?.total_inserted_events,
          total_duplicate_events: data.data?.total_duplicate_events,
          reached_start: data.data?.reached_start,
        };
        el("solFullHistoryOut").textContent = JSON.stringify(summary, null, 2);
        if (Number(data.data?.total_fetched_rows || 0) === 0) {
          showToast("Solana Historie importiert, aber keine Transaktionen im Zeitraum gefunden.", "warn");
        } else if (data?.status === "partial") {
          showToast(`Teilweise importiert: fetched=${summary.total_fetched_rows}, duplicates=${summary.total_duplicate_events}`, "warn");
        } else {
          showToast(
            `Solana Historie importiert: fetched=${summary.total_fetched_rows}, inserted=${summary.total_inserted_events}, duplicates=${summary.total_duplicate_events}`,
            "ok"
          );
        }
        await loadIntegrationOverview();
        await loadImportSourcesSummary();
        switchStep(2);
      }
    } catch (error) {
      showToast(`Solana Full-History Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnWgRefresh").addEventListener("click", async () => {
    await loadWalletGroups();
    showToast("Wallet-Gruppen geladen.", "ok");
  });

  el("btnWgSave").addEventListener("click", async (e) => {
    const name = el("wgName").value.trim();
    const description = el("wgDescription").value.trim();
    const walletAddresses = parseWalletAddresses(el("wgWallets").value);
    if (!name) {
      showToast("Gruppenname fehlt.", "warn");
      return;
    }
    if (!walletAddresses.length) {
      showToast("Mindestens eine Wallet-Adresse erforderlich.", "warn");
      return;
    }
    const payload = {
      group_id: state.selectedWalletGroupId || null,
      name,
      description: description || null,
      wallet_addresses: walletAddresses,
      source_filters: selectedWalletGroupSourceFilters(),
    };
    const res = await callApi("/api/v1/wallet-groups/upsert", "POST", payload, e.currentTarget);
    if (res?.status === "success") {
      state.selectedWalletGroupId = res.data?.group_id || "";
      await loadWalletGroups();
      await loadDashboard();
      showToast("Wallet-Gruppe gespeichert.", "ok");
    }
  });

  el("btnWgDelete").addEventListener("click", async (e) => {
    const group = selectedWalletGroup();
    if (!group) {
      showToast("Bitte zuerst eine Gruppe auswählen.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/wallet-groups/delete",
      "POST",
      { group_id: group.group_id },
      e.currentTarget
    );
    if (res?.status === "success") {
      state.selectedWalletGroupId = "";
      await loadWalletGroups();
      await loadDashboard();
      showToast("Wallet-Gruppe gelöscht.", "ok");
    }
  });

  el("btnWgBalance").addEventListener("click", async (e) => {
    const group = selectedWalletGroup();
    const payload = {
      group_id: group?.group_id || null,
      wallet_addresses: group?.wallet_addresses || parseWalletAddresses(el("wgWallets").value),
      rpc_url: el("solRpc").value.trim() || "https://api.mainnet.solana.com",
      rpc_fallback_urls: (el("solRpcFallbacks").value.trim() || "")
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
      timeout_seconds: 25,
      max_tokens: 300,
      include_prices: true,
    };
    const res = await callApi(
      "/api/v1/connectors/solana/group-balance-snapshot",
      "POST",
      payload,
      e.currentTarget
    );
    if (res?.status === "success") {
      el("wgOut").textContent = JSON.stringify(res.data, null, 2);
      state.dashboard = state.dashboard || {};
      state.dashboard.last_live_tokens = res.data?.tokens ?? [];
      renderLiveSummaryCards({
        wallet: group?.name || group?.group_id || "group",
        total_estimated_usd: res.data?.total_estimated_usd || "",
        sol_balance: res.data?.total_sol_balance || "",
        sol_usd_value: "",
        token_count: res.data?.token_count || 0,
      });
      state.paging.tokenPage = 1;
      renderLiveTokenTable(res.data?.tokens ?? []);
      await refreshWalletSnapshotChart("group", group?.group_id || "");
      showToast("Gruppen-Balance geladen.", "ok");
    }
  });

  el("btnWgImport").addEventListener("click", async (e) => {
    const group = selectedWalletGroup();
    const payload = {
      group_id: group?.group_id || null,
      wallet_addresses: group?.wallet_addresses || parseWalletAddresses(el("wgWallets").value),
      rpc_url: el("solRpc").value.trim() || "https://api.mainnet.solana.com",
      rpc_fallback_urls: (el("solRpcFallbacks").value.trim() || "")
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
      timeout_seconds: 25,
      max_signatures: Number(el("solMaxSignatures").value || "1000"),
      max_transactions: Number(el("solMaxTransactions").value || "1000"),
      aggregate_jupiter: el("solAggregateJupiter").value === "true",
      jupiter_window_seconds: Number(el("solJupiterWindow").value || "2"),
      source_name: group?.name ? `solana_group_${group.name.replace(/\s+/g, "_").toLowerCase()}` : null,
    };
    const res = await callApi(
      "/api/v1/connectors/solana/group-import-confirm",
      "POST",
      payload,
      e.currentTarget
    );
    if (res?.status === "success") {
      el("wgOut").textContent = JSON.stringify(res.data, null, 2);
      switchStep(2);
      await loadDashboard();
      await loadIntegrationOverview();
      await loadImportSourcesSummary();
      showToast("Gruppen-Import abgeschlossen.", "ok");
    }
  });

  el("btnSolBulkImport")?.addEventListener("click", async (e) => {
    const wallets = parseWalletAddresses(el("solWalletBulk")?.value || "");
    if (!wallets.length) {
      showToast("Bitte mindestens eine Wallet-Adresse im Bulk-Feld eintragen.", "warn");
      return;
    }
    const payload = solanaPayload();
    const res = await callApi(
      "/api/v1/connectors/solana/group-import-confirm",
      "POST",
      {
        group_id: null,
        wallet_addresses: wallets,
        rpc_url: payload.rpc_url,
        rpc_fallback_urls: payload.rpc_fallback_urls,
        timeout_seconds: 25,
        max_signatures: payload.max_signatures,
        max_transactions: payload.max_transactions,
        aggregate_jupiter: payload.aggregate_jupiter,
        jupiter_window_seconds: payload.jupiter_window_seconds,
        source_name: "solana_bulk_wallet_import",
      },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadDashboard();
      await loadIntegrationOverview();
      await loadImportSourcesSummary();
      showToast(`Bulk-Import abgeschlossen (${wallets.length} Wallets).`, "ok");
      switchStep(2);
    }
  });

  el("btnIntegrationRefresh")?.addEventListener("click", async () => {
    await loadIntegrationOverview();
    showToast("Integrationsübersicht aktualisiert.", "ok");
  });

  el("btnImportSourcesRefresh")?.addEventListener("click", async () => {
    await loadImportSourcesSummary();
    showToast("Importhistorie aktualisiert.", "ok");
  });
  el("btnImportJobsRefresh")?.addEventListener("click", async () => {
    await loadImportJobs(false);
    showToast("Import-Aktivitätsprotokoll aktualisiert.", "ok");
  });
  ["importJobIntegration", "importJobStatus"].forEach((id) => {
    el(id)?.addEventListener("change", async () => {
      savePref(`field.${id}`, el(id).value);
      await loadImportJobs(true);
    });
  });
  el("importJobDetail")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-import-detail-action]");
    if (!button) return;
    handleImportJobDetailAction(button.dataset.importDetailAction || "");
  });

  el("btnAutoMatch").addEventListener("click", async (e) => {
    const body = {
      time_window_seconds: Number(el("timeWindow").value || "600"),
      amount_tolerance_ratio: Number(el("amountTol").value || "0.02"),
      min_confidence: Number(el("minConf").value || "0.75"),
    };
    const data = await callApi("/api/v1/reconcile/auto-match", "POST", body, e.currentTarget);
    if (data?.status === "success") {
      await loadUnmatched();
      await loadTransferLedger();
    }
  });

async function loadUnmatched() {
    const params = new URLSearchParams({
      time_window_seconds: String(Number(el("timeWindow").value || "600")),
      amount_tolerance_ratio: String(Number(el("amountTol").value || "0.02")),
      min_confidence: String(Number(el("minConf").value || "0.75")),
    });
    const data = await callApi(`/api/v1/review/unmatched?${params.toString()}`);
    if (!data?.data) return;
    state.unmatchedOutbound = data.data.unmatched_outbound_ids ?? [];
    state.unmatchedInbound = data.data.unmatched_inbound_ids ?? [];
    renderUnmatchedLists();
    await loadReviewGates(true);
  }

  el("btnUnmatched").addEventListener("click", loadUnmatched);
  async function loadTransferLedger() {
    const data = await callApi("/api/v1/reconcile/ledger?limit=300&offset=0", "GET", null, null, true);
    if (!data?.data) return;
    state.transferLedger = data.data.rows ?? [];
    state.paging.transferPage = 1;
    renderTransferLedger(state.transferLedger);
    await loadLegacyHntTransfers(true);
  }
  el("btnTransferLedger").addEventListener("click", loadTransferLedger);
  el("btnReviewTransferLoad")?.addEventListener("click", loadTransferLedger);
  el("btnLegacyHntTransfers")?.addEventListener("click", () => loadLegacyHntTransfers(false));
  el("btnReviewLegacyHntTransfers")?.addEventListener("click", () => loadLegacyHntTransfers(false));
  ["reviewTransferSearch", "reviewTransferStatus"].forEach((id) => {
    const node = el(id);
    if (!node) return;
    const eventName = id === "reviewTransferSearch" ? "input" : "change";
    node.addEventListener(eventName, () => {
      savePref(`field.${id}`, node.value);
      state.paging.transferPage = 1;
      renderTransferLedger(state.transferLedger);
    });
  });
  el("reviewTransferPageSize")?.addEventListener("change", () => {
    savePref("field.reviewTransferPageSize", el("reviewTransferPageSize").value);
    state.paging.transferPage = 1;
    renderTransferLedger(state.transferLedger);
  });
  el("btnTransferPrev")?.addEventListener("click", () => {
    state.paging.transferPage = Math.max(1, state.paging.transferPage - 1);
    renderTransferLedger(state.transferLedger);
  });
  el("btnTransferNext")?.addEventListener("click", () => {
    state.paging.transferPage += 1;
    renderTransferLedger(state.transferLedger);
  });
  el("btnTransferCsv")?.addEventListener("click", () => {
    const search = (el("reviewTransferSearch")?.value || "").trim().toLowerCase();
    const status = (el("reviewTransferStatus")?.value || "").trim().toLowerCase();
    const rows = (state.transferLedger || []).filter((item) => {
      const itemStatus = String(item.status || "").toLowerCase();
      if (status && itemStatus !== status) return false;
      if (!search) return true;
      const hay = [
        item.asset,
        item.from_platform,
        item.from_wallet,
        item.to_platform,
        item.to_wallet,
        item.method,
        item.match_id,
        item.status,
      ].map((v) => String(v || "").toLowerCase()).join(" ");
      return hay.includes(search);
    });
    if (!rows.length) {
      showToast("Keine Transfer-Daten für Export.", "warn");
      return;
    }
    const csv = toCsv(rows, [
      "timestamp_utc",
      "status",
      "asset",
      "quantity",
      "holding_period_continues",
      "from_platform",
      "from_wallet",
      "to_platform",
      "to_wallet",
      "method",
      "confidence_score",
      "match_id",
    ]);
    downloadCsv("transfer_ledger_filtered.csv", csv);
  });

  async function loadLotAging() {
    const asOf = el("dashLotAsOf").value.trim();
    const asset = el("dashLotAsset").value.trim().toUpperCase();
    const params = new URLSearchParams();
    if (asOf) params.set("as_of_utc", asOf);
    if (asset) params.set("asset", asset);
    const data = await callApi(`/api/v1/portfolio/lot-aging?${params.toString()}`, "GET", null, null, true);
    if (!data?.data) return;
    state.lotRows = data.data.lot_rows ?? [];
    renderLotAging(state.lotRows);
  }
  el("btnLoadLotAging").addEventListener("click", loadLotAging);

  async function loadIssues() {
    const data = await callApi("/api/v1/issues/inbox", "GET", null, null, true);
    if (!data?.data) return;
    state.issues = data.data.issues ?? [];
    state.paging.issuePage = 1;
    renderIssues(state.issues);
    await loadReviewGates(true);
  }
  el("btnIssuesLoad").addEventListener("click", loadIssues);
  loadIssues();
  el("btnReviewGates")?.addEventListener("click", async (e) => {
    await loadReviewGates(false);
    if (state.reviewGates?.allow_export) {
      showToast("Review-Gates erfüllt: Export freigegeben.", "ok");
    } else {
      showToast("Review-Gates blockieren den Export. Details im Panel.", "warn");
    }
  });
  el("btnReportFiles")?.addEventListener("click", async () => {
    await loadReportFiles(currentJobId(), false);
    showToast("Export-Dateien geladen.", "ok");
  });
  el("btnCompareRuleset")?.addEventListener("click", async (e) => {
    await compareCurrentRuleset(e.currentTarget);
  });
  el("btnCreateSnapshot")?.addEventListener("click", async (e) => {
    await createCurrentSnapshot(e.currentTarget);
  });
  ["reviewIssueSearch", "reviewIssueStatus"].forEach((id) => {
    const node = el(id);
    if (!node) return;
    const eventName = id === "reviewIssueSearch" ? "input" : "change";
    node.addEventListener(eventName, () => {
      savePref(`field.${id}`, node.value);
      state.paging.issuePage = 1;
      renderIssues(state.issues);
    });
  });
  el("reviewIssuePageSize")?.addEventListener("change", () => {
    savePref("field.reviewIssuePageSize", el("reviewIssuePageSize").value);
    state.paging.issuePage = 1;
    renderIssues(state.issues);
  });
  el("btnIssuePrev")?.addEventListener("click", () => {
    state.paging.issuePage = Math.max(1, state.paging.issuePage - 1);
    renderIssues(state.issues);
  });
  el("btnIssueNext")?.addEventListener("click", () => {
    state.paging.issuePage += 1;
    renderIssues(state.issues);
  });
  el("btnIssuesCsv")?.addEventListener("click", () => {
    const search = (el("reviewIssueSearch")?.value || "").trim().toLowerCase();
    const statusFilter = (el("reviewIssueStatus")?.value || "").trim().toLowerCase();
    const rows = (state.issues || []).filter((item) => {
      const itemStatus = String(item.status || "").toLowerCase();
      if (statusFilter && itemStatus !== statusFilter) return false;
      if (!search) return true;
      const hay = [
        item.issue_id,
        item.status,
        item.severity,
        item.type,
        item.asset,
        item.detail,
        item.note,
      ].map((v) => String(v || "").toLowerCase()).join(" ");
      return hay.includes(search);
    });
    if (!rows.length) {
      showToast("Keine Issues für Export.", "warn");
      return;
    }
    const csv = toCsv(rows, ["issue_id", "status", "severity", "type", "asset", "detail", "note"]);
    downloadCsv("issues_filtered.csv", csv);
  });

  el("btnIssueUpdate").addEventListener("click", async (e) => {
    const issueId = el("issueId").value.trim();
    const status = el("issueStatus").value;
    const note = el("issueNote").value.trim();
    if (!issueId) {
      showToast("Issue-ID fehlt.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/issues/update-status",
      "POST",
      { issue_id: issueId, status, note: note || null },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadIssues();
      showToast("Issue-Status gespeichert.", "ok");
    }
  });

  el("btnManualMatch").addEventListener("click", async (e) => {
    const outbound = el("manualOut").value;
    const inbound = el("manualIn").value;
    if (!outbound || !inbound) {
      showToast("Bitte Outbound und Inbound auswählen.", "warn");
      return;
    }
    const data = await callApi(
      "/api/v1/reconcile/manual",
      "POST",
      {
        outbound_event_id: outbound,
        inbound_event_id: inbound,
        note: el("manualNote").value || null,
      },
      e.currentTarget
    );
    if (data?.status === "success") {
      await loadUnmatched();
      await loadTransferLedger();
      switchStep(3);
    }
  });

  el("btnPreflight")?.addEventListener("click", async (e) => {
    const result = await runPreflight(e.currentTarget, false);
    if (result?.allow_run) {
      showToast("Preflight bestanden. Steuerlauf kann gestartet werden.", "ok");
    } else if (result) {
      showToast("Preflight blockiert. Bitte Review-Blocker prüfen.", "warn");
    }
  });

  el("btnRun").addEventListener("click", async (e) => {
    const preflight = await runPreflight(e.currentTarget, true);
    if (!preflight?.allow_run) {
      showToast("Steuerlauf nicht gestartet: Preflight blockiert.", "warn");
      switchStep(2);
      return;
    }
    const payload = processRequestPayload();
    const data = await callApi(
      "/api/v1/process/run",
      "POST",
      {
        tax_year: payload.tax_year,
        ruleset_id: payload.ruleset_id,
        config: payload.config,
        dry_run: false,
      },
      e.currentTarget
    );
    if (data?.data?.job_id) {
      el("jobId").value = data.data.job_id;
      await loadProcessJobs(true);
      switchStep(4);
      updateMetrics(data.data);
      await refreshTaxReviewData(data.data.job_id, true);
      await loadReviewGates(true);
    }
  });

  el("btnWorker").addEventListener("click", async (e) => {
    const data = await callApi(
      "/api/v1/process/worker/run-next",
      "POST",
      { simulate_fail: false },
      e.currentTarget
    );
    if (data?.data) {
      updateMetrics(data.data);
      if (data.data.job_id) el("jobId").value = data.data.job_id;
      if (data.data.job_id) await refreshTaxReviewData(data.data.job_id, true);
      await loadReviewGates(true);
    }
  });

  el("btnStatus").addEventListener("click", async (e) => {
    const jobId = el("jobId").value.trim();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/status/${jobId}`, "GET", null, e.currentTarget);
    if (data?.data) {
      updateMetrics(data.data);
      await refreshTaxReviewData(jobId, true);
      await loadReviewGates(true);
    }
  });

  el("btnProcessJobsLoad")?.addEventListener("click", async () => {
    await loadProcessJobs(true);
  });
  el("btnProcessJobsRefreshNow")?.addEventListener("click", async () => {
    await loadProcessJobs(true);
    showToast("Process-Jobs aktualisiert.", "ok");
  });
  el("processJobsAutoRefresh")?.addEventListener("change", () => {
    syncProcessJobsAutoRefresh();
    const value = el("processJobsAutoRefresh")?.value || "";
    savePref("field.processJobsAutoRefresh", value);
  });
  el("processRunMode")?.addEventListener("change", () => {
    state.processingJobsMode = String(el("processRunMode")?.value || "default");
    savePref("field.processRunMode", state.processingJobsMode);
    loadProcessJobs(true);
  });
  el("processJobSearch")?.addEventListener("input", () => {
    savePref("field.processJobSearch", el("processJobSearch").value);
    renderProcessJobs();
  });
  el("processJobStatus")?.addEventListener("change", () => {
    const value = el("processJobStatus")?.value || "";
    savePref("field.processJobStatus", value);
    loadProcessJobs(true);
  });
  ["processJobsSort", "processJobsSortDir"].forEach((id) => {
    const node = el(id);
    if (!node) return;
    node.addEventListener("change", () => {
      savePref(`field.${id}`, node.value);
      if (state.processingJobs.length > 0) {
        renderProcessJobs();
      }
    });
  });
  el("btnProcessJobsCsv")?.addEventListener("click", () => {
    const rows = (state.processingJobs || []).map((row) => {
      const formatted = formatProcessJobRow(row);
      return {
        job_id: formatted.job_id,
        tax_year: formatted.tax_year,
        status: formatted.status,
        progress_percent: formatMoney(formatted.progress),
        ruleset_id: formatted.ruleset_id,
        ruleset_version: formatted.ruleset_version,
        tax_line_count: formatted.tax_line_count,
        derivative_line_count: formatted.derivative_line_count,
        updated_at_utc: formatted.updated_at_utc,
        created_at_utc: formatted.created_at_utc,
      };
    });
    if (!rows.length) {
      showToast("Keine Jobs für Export vorhanden.", "warn");
      return;
    }
    const csv = toCsv(rows, [
      "job_id",
      "tax_year",
      "status",
      "progress_percent",
      "ruleset_id",
      "ruleset_version",
      "tax_line_count",
      "derivative_line_count",
      "created_at_utc",
      "updated_at_utc",
    ]);
    downloadCsv("process_jobs.csv", csv);
  });

  el("btnLoadTaxLines").addEventListener("click", async (e) => {
    const jobId = currentJobId();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/tax-lines/${jobId}`, "GET", null, e.currentTarget);
    state.taxLines = data?.data?.lines ?? [];
    state.paging.taxPage = 1;
    renderTaxTable();
    await loadTaxDomainSummary(jobId, true);
    await loadReviewGates(true);
  });

  el("btnLoadDerivLines").addEventListener("click", async (e) => {
    const jobId = currentJobId();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/derivative-lines/${jobId}`, "GET", null, e.currentTarget);
    state.derivativeLines = data?.data?.lines ?? [];
    state.paging.derivPage = 1;
    renderDerivativeTable();
    await loadReviewGates(true);
  });

  el("taxFilterAsset").addEventListener("input", () => {
    savePref("field.taxFilterAsset", el("taxFilterAsset").value);
    state.paging.taxPage = 1;
    renderTaxTable();
  });
  el("taxFilterStatus").addEventListener("change", () => {
    savePref("field.taxFilterStatus", el("taxFilterStatus").value);
    state.paging.taxPage = 1;
    renderTaxTable();
  });
  el("taxPageSize").addEventListener("change", () => {
    savePref("field.taxPageSize", el("taxPageSize").value);
    state.paging.taxPage = 1;
    renderTaxTable();
  });
  el("btnTaxPrev")?.addEventListener("click", () => {
    state.paging.taxPage = Math.max(1, state.paging.taxPage - 1);
    renderTaxTable();
  });
  el("btnTaxNext")?.addEventListener("click", () => {
    state.paging.taxPage += 1;
    renderTaxTable();
  });
  el("taxTable").addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const classifyBtn = target.closest(".btn-classify");
    if (classifyBtn instanceof HTMLElement) {
      const eventId = classifyBtn.dataset.eventId || "";
      if (!eventId) return;
      el("taxOverrideEventId").value = eventId;
      if (el("taxOverrideCategory")) el("taxOverrideCategory").value = "PRIVATE_SO";
      if (el("taxOverrideReason")) el("taxOverrideReason").value = "";
      el("taxOverrideNote").value = "";
      showToast(`Event ${eventId} für Umklassifizierung übernommen.`, "ok");
      return;
    }
    const btn = target.closest(".btn-audit");
    if (!(btn instanceof HTMLElement)) return;
    const lineNoRaw = btn.dataset.lineNo || "";
    const lineNo = Number(lineNoRaw);
    if (!Number.isFinite(lineNo) || lineNo <= 0) return;
    await loadTaxAudit(lineNo);
  });
  el("derivFilterAsset").addEventListener("input", () => {
    savePref("field.derivFilterAsset", el("derivFilterAsset").value);
    state.paging.derivPage = 1;
    renderDerivativeTable();
  });
  el("derivFilterType").addEventListener("change", () => {
    savePref("field.derivFilterType", el("derivFilterType").value);
    state.paging.derivPage = 1;
    renderDerivativeTable();
  });
  el("derivPageSize")?.addEventListener("change", () => {
    savePref("field.derivPageSize", el("derivPageSize").value);
    state.paging.derivPage = 1;
    renderDerivativeTable();
  });
  el("btnDerivPrev")?.addEventListener("click", () => {
    state.paging.derivPage = Math.max(1, state.paging.derivPage - 1);
    renderDerivativeTable();
  });
  el("btnDerivNext")?.addEventListener("click", () => {
    state.paging.derivPage += 1;
    renderDerivativeTable();
  });

  el("btnTaxCsv").addEventListener("click", () => {
    if (!state.taxLines.length) {
      showToast("Keine Tax Lines geladen.", "warn");
      return;
    }
    const csv = toCsv(state.taxLines, [
      "line_no",
      "asset",
      "qty",
      "buy_timestamp_utc",
      "sell_timestamp_utc",
      "cost_basis_eur",
      "proceeds_eur",
      "gain_loss_eur",
      "hold_days",
      "tax_status",
      "source_event_id",
    ]);
    downloadCsv(`tax_lines_${currentJobId() || "job"}.csv`, csv);
  });

  el("btnTaxOverrideLoad")?.addEventListener("click", async () => {
    await loadTaxEventOverrides(false);
    showToast("Tax-Overrides geladen.", "ok");
  });

  el("btnTaxOverrideSave")?.addEventListener("click", async (e) => {
    const sourceEventId = (el("taxOverrideEventId")?.value || "").trim();
    const taxCategory = (el("taxOverrideCategory")?.value || "").trim();
    const reasonCode = (el("taxOverrideReason")?.value || "").trim();
    const note = (el("taxOverrideNote")?.value || "").trim();
    if (!sourceEventId) {
      showToast("Source Event ID fehlt.", "warn");
      return;
    }
    const data = await callApi(
      "/api/v1/tax/event-override/upsert",
      "POST",
      { source_event_id: sourceEventId, tax_category: taxCategory, reason_code: reasonCode || null, note: note || null },
      e.currentTarget
    );
    if (data?.status === "success") {
      await loadTaxEventOverrides(true);
      showToast("Tax-Override gespeichert. Bitte Process neu ausführen.", "ok");
    }
  });

  el("btnTaxOverrideDelete")?.addEventListener("click", async (e) => {
    const sourceEventId = (el("taxOverrideEventId")?.value || "").trim();
    if (!sourceEventId) {
      showToast("Source Event ID fehlt.", "warn");
      return;
    }
    const data = await callApi(
      "/api/v1/tax/event-override/delete",
      "POST",
      { source_event_id: sourceEventId },
      e.currentTarget
    );
    if (data?.status === "success") {
      await loadTaxEventOverrides(true);
      showToast("Tax-Override gelöscht. Bitte Process neu ausführen.", "ok");
    }
  });

  el("btnDerivCsv").addEventListener("click", () => {
    if (!state.derivativeLines.length) {
      showToast("Keine Derivative Lines geladen.", "warn");
      return;
    }
    const csv = toCsv(state.derivativeLines, [
      "line_no",
      "position_id",
      "asset",
      "event_type",
      "open_timestamp_utc",
      "close_timestamp_utc",
      "collateral_eur",
      "proceeds_eur",
      "fees_eur",
      "funding_eur",
      "gain_loss_eur",
      "loss_bucket",
      "source_event_id",
    ]);
    downloadCsv(`derivative_lines_${currentJobId() || "job"}.csv`, csv);
  });

  el("btnDashRefresh").addEventListener("click", async () => {
    await refreshUsdEurRateBestEffort();
    await loadDashboard();
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    if (Array.isArray(lastTokens) && lastTokens.length > 0) {
      renderLiveTokenTable(lastTokens);
    }
    showToast("Dashboard aktualisiert.", "ok");
  });
  el("btnYearlyRefresh")?.addEventListener("click", () => {
    renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
  });
  el("yearlyScaleMode")?.addEventListener("change", () => {
    renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
  });
  el("yearlyYearFilter")?.addEventListener("change", () => {
    renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
  });
  el("yearlyAssetFilter")?.addEventListener("input", () => {
    renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
  });
  el("yearlySourceFilter")?.addEventListener("change", () => {
    saveYearlySourcePrefs();
    renderYearlyAssetActivity(state.dashboard?.yearly_asset_activity ?? {});
  });
  el("btnYearlySourcesAll")?.addEventListener("click", () => setYearlySourceSelection("all"));
  el("btnYearlySourcesNone")?.addEventListener("click", () => setYearlySourceSelection("none"));
  el("btnYearlySourcesPrimary")?.addEventListener("click", () => setYearlySourceSelection("primary"));
  el("btnCockpitRefresh")?.addEventListener("click", async () => {
    await refreshUsdEurRateBestEffort();
    await loadDashboard();
    if (currentJobId()) {
      await loadTaxDomainSummary(currentJobId(), true);
    }
    showToast("Steuer-Cockpit aktualisiert.", "ok");
  });
  el("btnCockpitOpenImports")?.addEventListener("click", () => switchStep("1"));
  el("btnCockpitOpenTax")?.addEventListener("click", () => switchReviewTab("tax"));
  el("btnCockpitOpenHoldings")?.addEventListener("click", () => switchReviewTab("holdings"));
  el("globalSearch")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      applyGlobalSearch();
    }
  });
  el("globalScopeSelect")?.addEventListener("change", () => {
    const value = el("globalScopeSelect")?.value || "all";
    switchStep("4");
    switchReviewTab(value === "all" ? "cockpit" : "holdings");
  });
  el("taxYear")?.addEventListener("change", () => {
    syncTaxRunSelection();
    savePref("field.taxYear", el("taxYear")?.value || "2026");
  });
  el("cwSolanaFocus")?.addEventListener("click", () => {
    openSettingsPanel("solanaSettings", "solWallet");
  });
  el("cwSolanaImport")?.addEventListener("click", () => el("btnSolImportFull")?.click());
  el("cwCexFocus")?.addEventListener("click", () => {
    openSettingsPanel("cexSettings", "cexConnector");
  });
  el("cwCexImport")?.addEventListener("click", () => el("btnCexImportFull")?.click());
  el("cwFileFocus")?.addEventListener("click", () => {
    openSettingsPanel("bulkSettings", "bulkFolderPath");
  });
  el("cwFileImport")?.addEventListener("click", () => el("btnBulkFolderImport")?.click());
  el("cwWalletFocus")?.addEventListener("click", () => {
    openSettingsPanel("walletGroupSettings", "wgName");
  });

  el("btnDashSaveRole").addEventListener("click", async (e) => {
    const mode = el("dashRoleMode").value;
    const res = await callApi(
      "/api/v1/dashboard/role-override",
      "POST",
      { mode },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadDashboard();
      showToast("Rollenmodus gespeichert.", "ok");
    }
  });

  el("btnDashBalance").addEventListener("click", async (e) => {
    const wallet = el("dashWallet").value.trim() || el("solWallet").value.trim();
    if (!wallet) {
      showToast("Bitte Wallet-Adresse eingeben.", "warn");
      return;
    }
    const payload = {
      wallet_address: wallet,
      rpc_url: el("solRpc").value.trim() || "https://api.mainnet.solana.com",
      rpc_fallback_urls: (el("solRpcFallbacks").value.trim() || "")
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0),
      timeout_seconds: 20,
      max_tokens: 200,
    };
    const data = await callApi(
      "/api/v1/connectors/solana/balance-snapshot",
      "POST",
      payload,
      e.currentTarget
    );
    if (data?.status === "success") {
      state.dashboard = state.dashboard || {};
      state.dashboard.last_live_tokens = data.data?.tokens ?? [];
      const summary = {
        wallet: data.data?.wallet_address ?? wallet,
        total_estimated_usd: data.data?.total_estimated_usd ?? "",
        sol_balance: data.data?.sol_balance ?? "",
        sol_usd_value: data.data?.sol_usd_value ?? "",
        token_count: data.data?.token_count ?? 0,
        priced_token_count: data.data?.priced_token_count ?? 0,
        price_source: data.data?.price_source ?? "none",
      };
      renderLiveSummaryCards(summary);
      state.paging.tokenPage = 1;
      renderLiveTokenTable(data.data?.tokens ?? []);
      await refreshWalletSnapshotChart("wallet", summary.wallet);
    }
  });

  el("btnSnapshotRefresh").addEventListener("click", async () => {
    const selectedGroupId = state.selectedWalletGroupId || "";
    if (selectedGroupId) {
      const group = selectedWalletGroup();
      if (Array.isArray(group?.source_filters) && group.source_filters.length > 0) {
        await refreshPortfolioSetHistory(selectedGroupId);
        showToast("Portfolio-Set-Verlauf aktualisiert.", "ok");
      } else {
        await refreshWalletSnapshotChart("group", selectedGroupId);
        showToast("Gruppen-Verlauf aktualisiert.", "ok");
      }
      return;
    }
    const wallet = el("dashWallet").value.trim() || el("solWallet").value.trim();
    if (!wallet) {
      showToast("Bitte Wallet oder Gruppe auswählen.", "warn");
      return;
    }
    await refreshWalletSnapshotChart("wallet", wallet);
    showToast("Wallet-Verlauf aktualisiert.", "ok");
  });
  el("dashSnapshotWindow")?.addEventListener("change", () => {
    savePref("field.dashSnapshotWindow", el("dashSnapshotWindow").value);
    const selectedGroupId = state.selectedWalletGroupId || "";
    if (selectedGroupId) {
      void refreshPortfolioSetHistory(selectedGroupId);
    }
  });
  el("dashShowIgnored").addEventListener("change", () => {
    savePref("field.dashShowIgnored", el("dashShowIgnored").checked ? "1" : "0");
    state.paging.tokenPage = 1;
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    if (Array.isArray(lastTokens) && lastTokens.length > 0) {
      renderLiveTokenTable(lastTokens);
    }
  });
  const debouncedTokenRerender = debounce(() => {
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    renderLiveTokenTable(lastTokens);
  }, 140);
  ["dashTokenSearch", "dashTokenStatusFilter", "dashTokenSort"].forEach((id) => {
    const control = el(id);
    if (!control) return;
    const eventName = id === "dashTokenSearch" ? "input" : "change";
    control.addEventListener(eventName, () => {
      savePref(`field.${id}`, control.value);
      state.paging.tokenPage = 1;
      if (id === "dashTokenSearch") {
        debouncedTokenRerender();
      } else {
        const lastTokens = state.dashboard?.last_live_tokens ?? [];
        renderLiveTokenTable(lastTokens);
      }
    });
  });
  el("dashTokenPageSize")?.addEventListener("change", () => {
    savePref("field.dashTokenPageSize", el("dashTokenPageSize").value);
    state.paging.tokenPage = 1;
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    renderLiveTokenTable(lastTokens);
  });
  el("btnTokenPrev")?.addEventListener("click", () => {
    state.paging.tokenPage = Math.max(1, state.paging.tokenPage - 1);
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    renderLiveTokenTable(lastTokens);
  });
  el("btnTokenNext")?.addEventListener("click", () => {
    state.paging.tokenPage += 1;
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    renderLiveTokenTable(lastTokens);
  });
  el("btnTokenQuickClear")?.addEventListener("click", () => {
    clearTokenQuickSelection();
    showToast("Token-Auswahl geleert.", "ok");
  });
  el("btnTokenQuickAlias")?.addEventListener("click", async (e) => {
    const mint = (el("tokenQuickMint")?.value || "").trim();
    const symbol = (el("tokenQuickSymbol")?.value || "").trim();
    const name = (el("tokenQuickName")?.value || "").trim();
    if (!mint || !symbol || !name) {
      showToast("Mint, Symbol und Name sind erforderlich.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/token-aliases/upsert",
      "POST",
      { mint, symbol: symbol.toUpperCase(), name, notes: "saved_from_dashboard_quick_action" },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadTokenAliases();
      const tokens = state.dashboard?.last_live_tokens ?? [];
      tokens.forEach((row) => {
        if (String(row.asset || "").toUpperCase() === mint.toUpperCase()) {
          row.symbol = symbol.toUpperCase();
          row.name = name;
          row.display_source = "alias";
        }
      });
      renderLiveTokenTable(tokens);
      showToast("Alias gespeichert.", "ok");
    }
  });
  el("btnTokenQuickIgnore")?.addEventListener("click", async (e) => {
    const mint = (el("tokenQuickMint")?.value || "").trim();
    const reason = (el("tokenQuickReason")?.value || "").trim();
    if (!mint || !reason) {
      showToast("Mint und Ignore-Begründung sind erforderlich.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/ignored-tokens/upsert",
      "POST",
      { mint, reason },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadIgnoredTokens();
      const tokens = state.dashboard?.last_live_tokens ?? [];
      tokens.forEach((row) => {
        if (String(row.asset || "").toUpperCase() === mint.toUpperCase()) {
          row.ignored = true;
          row.ignored_reason = reason;
        }
      });
      renderLiveTokenTable(tokens);
      showToast("Ignore-Regel gespeichert.", "ok");
    }
  });
  el("dashLotAsset")?.addEventListener("input", () => {
    savePref("field.dashLotAsset", el("dashLotAsset").value);
  });
  el("dashLotAsOf")?.addEventListener("input", () => {
    savePref("field.dashLotAsOf", el("dashLotAsOf").value);
  });
  el("uiDenseMode")?.addEventListener("change", () => {
    const on = !!el("uiDenseMode").checked;
    document.body.classList.toggle("dense-table", on);
    savePref("denseMode", on ? "1" : "0");
  });
  el("uiExpertMode")?.addEventListener("change", () => {
    setExpertMode(!!el("uiExpertMode").checked);
  });
  el("uiDisplayCurrency")?.addEventListener("change", () => {
    const currency = String(el("uiDisplayCurrency").value || "eur").toLowerCase();
    state.ui.displayCurrency = currency === "usd" ? "usd" : "eur";
    savePref("field.uiDisplayCurrency", state.ui.displayCurrency);
    rerenderWalletSnapshotFromState();
    const lastTokens = state.dashboard?.last_live_tokens ?? [];
    if (Array.isArray(lastTokens) && lastTokens.length > 0) {
      renderLiveTokenTable(lastTokens);
    }
    const assetRows = state.dashboard?.asset_balances ?? [];
    if (Array.isArray(assetRows) && assetRows.length > 0) {
      renderAssetMix(assetRows);
    }
    const summaryCards = document.querySelector("#dashLiveSummaryCards");
    if (summaryCards && summaryCards.children.length > 0) {
      // Trigger refresh to apply currency choice to latest visible wallet summary.
      // If no snapshot is loaded, cards keep existing values until next balance refresh.
      const wallet = el("dashWallet")?.value?.trim() || "";
      if (wallet) {
        void refreshWalletSnapshotChart("wallet", wallet);
      }
    }
  });
  el("btnResetViewPrefs")?.addEventListener("click", () => {
    try {
      Object.keys(localStorage)
        .filter((key) => key.startsWith("ui.pref.field.") || key.startsWith("ui.pref.cols.") || key === "ui.pref.denseMode" || key === "ui.pref.expertMode")
        .forEach((key) => localStorage.removeItem(key));
    } catch (_) {}
    showToast("Ansicht zurückgesetzt. Bitte Seite neu laden.", "ok");
  });
  el("btnPresetSave")?.addEventListener("click", () => {
    const scope = currentScopeKey();
    const name = (el("uiPresetName")?.value || "").trim();
    if (!name) {
      showToast("Bitte Preset-Name eingeben.", "warn");
      return;
    }
    const presets = listPresets(scope);
    presets[name] = collectCurrentViewState();
    savePresets(scope, presets);
    refreshPresetUi();
    el("uiPresetSelect").value = name;
    showToast(`Preset gespeichert: ${name}`, "ok");
  });
  el("btnPresetLoad")?.addEventListener("click", () => {
    const scope = currentScopeKey();
    const name = (el("uiPresetSelect")?.value || "").trim();
    if (!name) {
      showToast("Bitte Preset auswählen.", "warn");
      return;
    }
    const presets = listPresets(scope);
    const view = presets[name];
    if (!view) {
      showToast("Preset nicht gefunden.", "warn");
      return;
    }
    applyViewState(view);
    showToast(`Preset geladen: ${name}`, "ok");
  });
  el("btnPresetDelete")?.addEventListener("click", () => {
    const scope = currentScopeKey();
    const name = (el("uiPresetSelect")?.value || "").trim();
    if (!name) {
      showToast("Bitte Preset auswählen.", "warn");
      return;
    }
    const presets = listPresets(scope);
    delete presets[name];
    savePresets(scope, presets);
    refreshPresetUi();
    showToast(`Preset gelöscht: ${name}`, "ok");
  });
  document.querySelectorAll(".col-toggle").forEach((input) => {
    const tableId = input.dataset.tableId || "";
    const colKey = input.dataset.colKey || "";
    const prefs = loadColumnPrefs(tableId);
    if (Object.prototype.hasOwnProperty.call(prefs, colKey)) {
      input.checked = !!prefs[colKey];
    }
    input.addEventListener("change", () => {
      saveColumnPrefs(tableId);
      applyTableColumnVisibility(tableId);
    });
  });
  applyTableColumnVisibility("dashLiveTokenTable");
  applyTableColumnVisibility("taxTable");

  el("btnAdminRefresh").addEventListener("click", async () => {
    await loadAdminData();
  });

  el("btnBackfillRefresh").addEventListener("click", async () => {
    await loadBackfillService();
  });

  el("btnBackfillStart").addEventListener("click", async (e) => {
    await controlBackfillService("start", e.currentTarget);
  });

  el("btnBackfillStop").addEventListener("click", async (e) => {
    await controlBackfillService("stop", e.currentTarget);
  });

  el("btnBackfillRestart").addEventListener("click", async (e) => {
    await controlBackfillService("restart", e.currentTarget);
  });

  el("btnAdminSaveRuntime").addEventListener("click", async (e) => {
    const rpcUrl = el("adminRpcUrl").value.trim();
    const fallbackRaw = el("adminRpcFallbacks").value.trim();
    const usdToEurRaw = el("adminUsdToEur").value.trim();
    const usdToEur = Number(usdToEurRaw || "0");
    const fallbackUrls = fallbackRaw
      ? fallbackRaw.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
      : [];

    if (!rpcUrl) {
      showToast("Runtime RPC URL fehlt.", "warn");
      return;
    }

    const savePrimary = await callApi(
      "/api/v1/admin/settings",
      "POST",
      {
        setting_key: "runtime.solana.rpc_url",
        value: rpcUrl,
        is_secret: false,
      },
      e.currentTarget
    );
    if (!savePrimary || savePrimary.status === "error") return;

    const saveFallbacks = await callApi("/api/v1/admin/settings", "POST", {
      setting_key: "runtime.solana.rpc_fallback_urls",
      value: fallbackUrls,
      is_secret: false,
    });
    if (!saveFallbacks || saveFallbacks.status === "error") return;
    if (Number.isFinite(usdToEur) && usdToEur > 0) {
      const saveFx = await callApi("/api/v1/admin/settings", "POST", {
        setting_key: "runtime.fx.usd_to_eur",
        value: usdToEur,
        is_secret: false,
      });
      if (!saveFx || saveFx.status === "error") return;
      state.fx.usdToEur = usdToEur;
      state.fx.source = "runtime";
    }

    const dashWallet = el("dashWallet").value.trim() || el("solWallet").value.trim();
    if (dashWallet) {
      await callApi("/api/v1/admin/settings", "POST", {
        setting_key: "runtime.solana.default_wallet",
        value: dashWallet,
        is_secret: false,
      }, null, true);
    }

    await loadAdminData();
    await loadDashboard();
    showToast("Runtime gespeichert.", "ok");
  });

  el("btnAdminSaveAlchemy").addEventListener("click", async (e) => {
    const apiKey = el("adminAlchemyKey").value.trim();
    if (!apiKey) {
      showToast("Alchemy API Key fehlt.", "warn");
      return;
    }
    const data = await callApi(
      "/api/v1/admin/settings",
      "POST",
      {
        setting_key: "secret.alchemy.api_key",
        value: apiKey,
        is_secret: true,
      },
      e.currentTarget
    );
    if (data?.status === "success") {
      el("adminAlchemyKey").value = "";
      await loadAdminData();
      showToast("Alchemy Key verschlüsselt gespeichert.", "ok");
    }
  });

  el("btnAdminSaveCoinGecko").addEventListener("click", async (e) => {
    const apiKey = el("adminCoinGeckoKey").value.trim();
    if (!apiKey) {
      showToast("CoinGecko API Key fehlt.", "warn");
      return;
    }
    const data = await callApi(
      "/api/v1/admin/settings",
      "POST",
      {
        setting_key: "secret.coingecko.api_key",
        value: apiKey,
        is_secret: true,
      },
      e.currentTarget
    );
    if (data?.status === "success") {
      el("adminCoinGeckoKey").value = "";
      await loadAdminData();
      showToast("CoinGecko Key verschlüsselt gespeichert.", "ok");
    }
  });

  el("btnAdminSaveCex").addEventListener("click", async (e) => {
    const connector = el("adminCexConnector").value.trim().toLowerCase();
    const apiKey = el("adminCexApiKey").value.trim();
    const apiSecret = el("adminCexApiSecret").value.trim();
    const passphrase = el("adminCexPassphrase").value.trim();
    if (!connector || !apiKey || !apiSecret) {
      showToast("Connector, API Key und API Secret sind erforderlich.", "warn");
      return;
    }
    const keys = [
      { setting_key: `secret.cex.${connector}.api_key`, value: apiKey },
      { setting_key: `secret.cex.${connector}.api_secret`, value: apiSecret },
      { setting_key: `secret.cex.${connector}.passphrase`, value: passphrase || "" },
    ];
    for (const item of keys) {
      const res = await callApi(
        "/api/v1/admin/settings",
        "POST",
        { setting_key: item.setting_key, value: item.value, is_secret: true },
        e.currentTarget,
        true
      );
      if (!res || res.status === "error") {
        showToast("CEX Credentials konnten nicht gespeichert werden.", "err");
        return;
      }
    }
    el("adminCexApiKey").value = "";
    el("adminCexApiSecret").value = "";
    el("adminCexPassphrase").value = "";
    await loadAdminData();
    showToast(`CEX Credentials für ${connector} gespeichert.`, "ok");
  });

  el("btnAdminLoadCex").addEventListener("click", async () => {
    const connector = el("adminCexConnector").value.trim().toLowerCase();
    const creds = await loadSavedCexCredentials(connector);
    if (!creds) {
      showToast("Keine gespeicherten Credentials vorhanden.", "warn");
      return;
    }
    el("adminCexApiKey").value = creds.api_key || "";
    el("adminCexApiSecret").value = creds.api_secret || "";
    el("adminCexPassphrase").value = creds.passphrase || "";
    showToast(`CEX Credentials für ${connector} geladen.`, "ok");
  });

  el("btnAliasRefresh").addEventListener("click", async () => {
    await loadTokenAliases();
    showToast("Alias-Liste aktualisiert.", "ok");
  });

  el("btnAliasSave").addEventListener("click", async (e) => {
    const mint = el("aliasMint").value.trim();
    const symbol = el("aliasSymbol").value.trim();
    const name = el("aliasName").value.trim();
    const notes = el("aliasNotes").value.trim();
    if (!mint || !symbol || !name) {
      showToast("Mint, Symbol und Name sind erforderlich.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/token-aliases/upsert",
      "POST",
      { mint, symbol, name, notes: notes || null },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadTokenAliases();
      showToast("Alias gespeichert.", "ok");
    }
  });

  el("btnAliasDelete").addEventListener("click", async (e) => {
    const mint = el("aliasMint").value.trim();
    if (!mint) {
      showToast("Mint fehlt.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/token-aliases/delete",
      "POST",
      { mint },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadTokenAliases();
      showToast("Alias gelöscht.", "ok");
    }
  });

  el("btnIgnoreRefresh").addEventListener("click", async () => {
    await loadIgnoredTokens();
    showToast("Ignore-Liste aktualisiert.", "ok");
  });

  el("btnIgnoreSave").addEventListener("click", async (e) => {
    const mint = el("ignoreMint").value.trim();
    const reason = el("ignoreReason").value.trim();
    if (!mint || !reason) {
      showToast("Mint und Begründung sind erforderlich.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/ignored-tokens/upsert",
      "POST",
      { mint, reason },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadIgnoredTokens();
      showToast("Ignore-Regel gespeichert.", "ok");
    }
  });

  el("btnIgnoreDelete").addEventListener("click", async (e) => {
    const mint = el("ignoreMint").value.trim();
    if (!mint) {
      showToast("Mint fehlt.", "warn");
      return;
    }
    const res = await callApi(
      "/api/v1/admin/ignored-tokens/delete",
      "POST",
      { mint },
      e.currentTarget
    );
    if (res?.status === "success") {
      await loadIgnoredTokens();
      showToast("Ignore-Regel gelöscht.", "ok");
    }
  });
}

function formatProcessJobRow(row) {
  return {
    job_id: String(row.job_id || ""),
    tax_year: row.tax_year ?? "",
    status: String(row.status || "").toLowerCase(),
    progress: toNumber(row.progress || 0),
    ruleset_id: row.ruleset_id || "",
    ruleset_version: row.ruleset_version || "",
    tax_line_count: toNumber(row.tax_line_count || 0),
    derivative_line_count: toNumber(row.derivative_line_count || 0),
    updated_at_utc: row.updated_at_utc || "",
    created_at_utc: row.created_at_utc || "",
  };
}

function processJobStatusClass(status) {
  const value = String(status || "").toLowerCase();
  if (value === "completed") return "status-badge status-ok";
  if (value === "running") return "status-badge status-running";
  if (value === "failed") return "status-badge status-fail";
  return "status-badge status-default";
}

function renderProcessJobsMetrics() {
  const host = el("processJobsMetrics");
  if (!host) return;
  const filter = String(el("processJobStatus")?.value || "").trim();
  const selected = (state.processingJobs || []).length;
  const total = state.processingJobsCount || selected;
  const offset = state.processingJobsOffset || 0;
  const limit = state.processingJobsLimit || 0;
  const sort = state.processingJobsSort || "updated_at";
  const sortDir = state.processingJobsSortDir || "desc";
  const filterLabel = filter || "alle";
  host.innerHTML = `
    <div class="metric"><span>Status</span><strong>${filterLabel}</strong></div>
    <div class="metric"><span>Gefundene Jobs</span><strong>${total}</strong></div>
    <div class="metric"><span>Angezeigt</span><strong>${selected} (Offset: ${offset}, Limit: ${limit})</strong></div>
    <div class="metric"><span>Sortierung</span><strong>${sort} ${sortDir}</strong></div>
  `;
}

function sortProcessJobsRows(rows) {
  const sort = String(el("processJobsSort")?.value || state.processingJobsSort || "updated_at");
  const dir = String(el("processJobsSortDir")?.value || state.processingJobsSortDir || "desc");
  state.processingJobsSort = sort;
  state.processingJobsSortDir = dir;
  const reverse = dir === "desc" ? -1 : 1;
  const getValue = (row, key) => {
    if (key === "updated_at") return row.updated_at_utc || "";
    if (key === "created_at") return row.created_at_utc || "";
    if (key === "status") return row.status || "";
    if (key === "progress") return toNumber(row.progress || 0);
    return row[key] || "";
  };
  return [...rows].sort((a, b) => {
    const av = getValue(a, sort);
    const bv = getValue(b, sort);
    if (typeof av === "number" && typeof bv === "number") {
      return (av - bv) * reverse;
    }
    return String(av).localeCompare(String(bv)) * reverse;
  });
}

function renderProcessJobs() {
  const tbody = el("processJobsTable")?.querySelector("tbody");
  if (!tbody) return;
  const rawRows = state.processingJobs || [];
  const q = String(el("processJobSearch")?.value || "").trim().toLowerCase();
  const rows = sortProcessJobsRows(rawRows.filter((row) => {
    if (!q) return true;
    const hay = [
      row.job_id,
      row.status,
      row.ruleset_id,
      row.ruleset_version,
      String(row.tax_year || ""),
      row.updated_at_utc,
      row.created_at_utc,
    ].map((v) => String(v || "").toLowerCase()).join(" ");
    return hay.includes(q);
  }));
  tbody.innerHTML = "";

  rows.forEach((row) => {
    const job = formatProcessJobRow(row);
    const tr = document.createElement("tr");
    tr.className = "hoverable";
    tr.innerHTML = `
      <td>${job.job_id}</td>
      <td>${job.tax_year}</td>
      <td><span class="${processJobStatusClass(job.status)}">${job.status || "-"}</span></td>
      <td class="num">${formatMoney(job.progress)}%</td>
      <td>${job.ruleset_id}</td>
      <td>${job.ruleset_version}</td>
      <td class="num">${formatQty(job.tax_line_count)}</td>
      <td class="num">${formatQty(job.derivative_line_count)}</td>
      <td>${job.updated_at_utc || ""}</td>
    `;
    tr.addEventListener("click", async () => {
      if (!job.job_id) return;
      el("jobId").value = job.job_id;
      const data = await callApi(`/api/v1/process/status/${job.job_id}`, "GET", null, null, true);
      if (data?.data) {
        updateMetrics(data.data);
        await refreshTaxReviewData(job.job_id, true);
        await loadReviewGates(true);
        showToast(`Job ${job.job_id} geladen.`, "ok");
      }
    });
    tbody.appendChild(tr);
  });

  if (!rows.length) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="9">Keine Processing-Jobs vorhanden.</td>`;
    tbody.appendChild(tr);
  }
  const info = el("processJobsInfo");
  if (info) {
    info.textContent = `${rows.length} von ${state.processingJobs.length} aktuell geladenen Jobs (${state.processingJobsCount || state.processingJobs.length} Datensätze).`;
  }
  renderProcessJobsMetrics();
}

function syncProcessJobsAutoRefresh() {
  if (state.processingJobsAutoRefreshTimer) {
    window.clearInterval(state.processingJobsAutoRefreshTimer);
    state.processingJobsAutoRefreshTimer = null;
  }
  const secRaw = String(el("processJobsAutoRefresh")?.value || "").trim();
  state.processingJobsAutoRefreshSec = secRaw;
  const sec = Number(secRaw);
  if (!Number.isFinite(sec) || sec <= 0) return;
  state.processingJobsAutoRefreshTimer = window.setInterval(() => {
    if (String(currentStep()) === "3") {
      void loadProcessJobs(true);
    }
  }, sec * 1000);
}

async function loadProcessJobs(force = false) {
  const mode = String(el("processRunMode")?.value || state.processingJobsMode || "default");
  const selectedStatus = String(el("processJobStatus")?.value || "").trim().toLowerCase();
  const limit = Number(el("processJobsLimit")?.value || state.processingJobsLimit || 25);
  const offset = Number(el("processJobsOffset")?.value || state.processingJobsOffset || 0);

  const status = selectedStatus || (mode === "queued" ? "queued" : "");
  const params = new URLSearchParams({
    limit: String(Math.max(1, Math.min(limit, 200))),
    offset: String(Math.max(0, offset)),
  });
  if (status) {
    params.set("status", status);
  }

  if (mode === "latest") {
    if (!state.processingJobsSort || state.processingJobsSort === "status") {
      state.processingJobsSort = "updated_at";
    }
    state.processingJobsSortDir = "desc";
    const runModeSort = el("processJobsSort");
    const runModeSortDir = el("processJobsSortDir");
    if (runModeSort) runModeSort.value = "updated_at";
    if (runModeSortDir) runModeSortDir.value = "desc";
  }

  savePref("field.processRunMode", mode);
  state.processingJobsMode = mode;
  savePref("field.processJobsLimit", String(limit));
  savePref("field.processJobsOffset", String(offset));
  const data = await callApi(`/api/v1/process/jobs?${params.toString()}`, "GET", null, null, !force);
  if (!data?.data) return;
  state.processingJobs = data.data.rows || [];
  state.processingJobsCount = Number(data.data.count || (state.processingJobs ? state.processingJobs.length : 0));
  state.processingJobsLimit = limit;
  state.processingJobsOffset = offset;
  renderProcessJobs();
  if (state.processingJobsAutoRefreshSec) {
    renderProcessJobsMetrics();
  }
}

function getSelectedJobStatus() {
  return String(el("processJobStatus")?.value || "").trim();
}

init();
