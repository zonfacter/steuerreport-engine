const el = (id) => document.getElementById(id);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const state = {
  unmatchedOutbound: [],
  unmatchedInbound: [],
  taxLines: [],
  derivativeLines: [],
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

  rows.forEach((line) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${line.line_no}</td>
      <td>${line.asset}</td>
      <td class="num">${line.qty}</td>
      <td>${line.buy_timestamp_utc}</td>
      <td>${line.sell_timestamp_utc}</td>
      <td class="num">${line.cost_basis_eur}</td>
      <td class="num">${line.proceeds_eur}</td>
      <td class="num">${line.gain_loss_eur}</td>
      <td class="num">${line.hold_days}</td>
      <td>${line.tax_status}</td>
    `;
    tbody.appendChild(tr);
  });
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

  rows.forEach((line) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${line.line_no}</td>
      <td>${line.position_id}</td>
      <td>${line.asset}</td>
      <td>${line.event_type}</td>
      <td>${line.open_timestamp_utc}</td>
      <td>${line.close_timestamp_utc}</td>
      <td class="num">${line.collateral_eur}</td>
      <td class="num">${line.proceeds_eur}</td>
      <td class="num">${line.fees_eur}</td>
      <td class="num">${line.funding_eur}</td>
      <td class="num">${line.gain_loss_eur}</td>
    `;
    tbody.appendChild(tr);
  });
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

function cexPayload() {
  const connectorId = el("cexConnector").value.trim();
  const apiKey = el("cexApiKey").value.trim();
  const apiSecret = el("cexApiSecret").value.trim();
  const passphrase = el("cexPassphrase").value.trim();
  const startRaw = el("cexStartMs").value.trim();
  const endRaw = el("cexEndMs").value.trim();
  const maxRows = Number(el("cexMaxRows").value || "200");
  if (!connectorId || !apiKey || !apiSecret) {
    throw new Error("Connector, API Key und API Secret sind erforderlich.");
  }
  return {
    connector_id: connectorId,
    api_key: apiKey,
    api_secret: apiSecret,
    passphrase: passphrase || null,
    max_rows: maxRows,
    start_time_ms: startRaw ? Number(startRaw) : null,
    end_time_ms: endRaw ? Number(endRaw) : null,
  };
}

function solanaPayload() {
  const walletAddress = el("solWallet").value.trim();
  const rpcUrl = el("solRpc").value.trim() || "https://api.mainnet-beta.solana.com";
  const fallbackRaw = el("solRpcFallbacks").value.trim();
  const fallbackUrls = fallbackRaw
    ? fallbackRaw.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
    : [];
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
    max_signatures: maxSignatures,
    max_transactions: maxTransactions,
    aggregate_jupiter: aggregateJupiter,
    jupiter_window_seconds: jupiterWindowSeconds,
  };
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

  el("btnCexVerify").addEventListener("click", async (e) => {
    try {
      const payload = cexPayload();
      await callApi("/api/v1/connectors/cex/verify", "POST", payload, e.currentTarget);
    } catch (error) {
      showToast(`CEX Verify abgebrochen: ${error.message}`, "err");
    }
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
        switchStep(2);
      }
    } catch (error) {
      showToast(`CEX Import abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolPreview").addEventListener("click", async (e) => {
    try {
      const payload = solanaPayload();
      const data = await callApi("/api/v1/connectors/solana/wallet-preview", "POST", payload, e.currentTarget);
      if (data?.data?.rows) {
        el("eventsJson").value = JSON.stringify(data.data.rows, null, 2);
      }
    } catch (error) {
      showToast(`Solana Preview abgebrochen: ${error.message}`, "err");
    }
  });

  el("btnSolImport").addEventListener("click", async (e) => {
    try {
      const payload = solanaPayload();
      payload.source_name = "solana_wallet_api_import";
      const data = await callApi("/api/v1/connectors/solana/import-confirm", "POST", payload, e.currentTarget);
      if (data?.status === "success") {
        switchStep(2);
      }
    } catch (error) {
      showToast(`Solana Import abgebrochen: ${error.message}`, "err");
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

  el("btnLoadTaxLines").addEventListener("click", async (e) => {
    const jobId = currentJobId();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/tax-lines/${jobId}`, "GET", null, e.currentTarget);
    state.taxLines = data?.data?.lines ?? [];
    renderTaxTable();
  });

  el("btnLoadDerivLines").addEventListener("click", async (e) => {
    const jobId = currentJobId();
    if (!jobId) {
      showToast("Bitte zuerst eine job_id eintragen.", "warn");
      return;
    }
    const data = await callApi(`/api/v1/process/derivative-lines/${jobId}`, "GET", null, e.currentTarget);
    state.derivativeLines = data?.data?.lines ?? [];
    renderDerivativeTable();
  });

  el("taxFilterAsset").addEventListener("input", renderTaxTable);
  el("taxFilterStatus").addEventListener("change", renderTaxTable);
  el("derivFilterAsset").addEventListener("input", renderDerivativeTable);
  el("derivFilterType").addEventListener("change", renderDerivativeTable);

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
}

init();
