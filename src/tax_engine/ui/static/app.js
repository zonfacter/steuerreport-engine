const el = (id) => document.getElementById(id);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = {
  unmatchedOutbound: [],
  unmatchedInbound: [],
};

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
}

function setApiState(ok) {
  const pill = el("apiState");
  pill.className = ok ? "pill pill-ok" : "pill pill-err";
  pill.textContent = ok ? "API: erreichbar" : "API: nicht erreichbar";
}

function setResponse(json) {
  el("responseOut").textContent = JSON.stringify(json, null, 2);
}

function updateMetrics(data) {
  if (!data) return;
  el("mStatus").textContent = data.status ?? "-";
  el("mProgress").textContent = data.progress != null ? `${data.progress}%` : "-";
  el("mTaxLines").textContent = String(data.tax_line_count ?? "-");
  el("mDerivLines").textContent = String(data.derivative_line_count ?? "-");
  el("summaryOut").textContent = JSON.stringify(data.result_summary ?? {}, null, 2);
}

async function callApi(path, method = "GET", body = null, btn = null) {
  try {
    if (btn) btn.disabled = true;
    const init = { method, headers: {} };
    if (body !== null) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const res = await fetch(path, init);
    const json = await res.json();
    setResponse(json);
    if (!res.ok || json.status === "error") {
      showToast(`Fehler: ${json.errors?.[0]?.message ?? res.statusText}`, "err");
    } else if (json.warnings?.length) {
      showToast(`Hinweis: ${json.warnings[0].message}`, "warn");
    } else {
      showToast("Aktion erfolgreich.", "ok");
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

function parseEventsJson() {
  const text = el("eventsJson").value;
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) {
    throw new Error("Das JSON muss ein Array sein.");
  }
  return parsed;
}

async function pingApi() {
  const res = await callApi("/api/v1/health");
  setApiState(!!(res && res.status === "success"));
}

function init() {
  el("eventsJson").value = JSON.stringify(defaultEvents, null, 2);
  switchStep(1);
  pingApi();

  $$(".step").forEach((btn) => {
    btn.addEventListener("click", () => switchStep(btn.dataset.step));
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
      if (data?.status === "success") switchStep(2);
    } catch (error) {
      showToast(`Import abgebrochen: ${error.message}`, "err");
    }
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
  }

  el("btnUnmatched").addEventListener("click", loadUnmatched);

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
      switchStep(3);
    }
  });

  el("btnRun").addEventListener("click", async (e) => {
    const data = await callApi(
      "/api/v1/process/run",
      "POST",
      {
        tax_year: Number(el("taxYear").value || "2026"),
        ruleset_id: el("rulesetId").value.trim() || "DE-2026-v1.0",
        config: {},
        dry_run: false,
      },
      e.currentTarget
    );
    if (data?.data?.job_id) {
      el("jobId").value = data.data.job_id;
      switchStep(4);
      updateMetrics(data.data);
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
    }
  });

  el("btnStatus").addEventListener("click", async (e) => {
    const jobId = el("jobId").value.trim();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/status/${jobId}`, "GET", null, e.currentTarget);
    if (data?.data) updateMetrics(data.data);
  });
}

init();

