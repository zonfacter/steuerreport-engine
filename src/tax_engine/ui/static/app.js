const el = (id) => document.getElementById(id);

const responseOut = el("responseOut");
const statusOut = el("statusOut");
const unmatchedOut = el("unmatchedOut");

const defaultEvents = [
  {
    timestamp: "2026-01-01T12:00:00Z",
    asset: "SOL",
    event_type: "withdrawal",
    amount: "10.00",
  },
  {
    timestamp: "2026-01-01T12:03:00Z",
    asset: "SOL",
    event_type: "deposit",
    amount: "9.99",
  },
  {
    timestamp: "2026-02-01T12:00:00Z",
    asset: "BTC",
    side: "buy",
    amount: "1",
    price_eur: "100",
    fee_eur: "1",
  },
  {
    timestamp: "2026-02-10T12:00:00Z",
    asset: "BTC",
    side: "sell",
    amount: "0.4",
    price_eur: "125",
    fee_eur: "0.5",
  },
];

el("eventsJson").value = JSON.stringify(defaultEvents, null, 2);

async function callApi(path, method = "GET", body = null) {
  const init = { method, headers: {} };
  if (body !== null) {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(path, init);
  const json = await res.json();
  responseOut.textContent = JSON.stringify(json, null, 2);
  return json;
}

el("btnImport").addEventListener("click", async () => {
  const sourceName = el("sourceName").value || "manual-ui.csv";
  const rows = JSON.parse(el("eventsJson").value);
  await callApi("/api/v1/import/confirm", "POST", { source_name: sourceName, rows });
});

el("btnAutoMatch").addEventListener("click", async () => {
  await callApi("/api/v1/reconcile/auto-match", "POST", {
    time_window_seconds: 600,
    amount_tolerance_ratio: 0.02,
    min_confidence: 0.75,
  });
});

el("btnUnmatched").addEventListener("click", async () => {
  const data = await callApi("/api/v1/review/unmatched");
  unmatchedOut.textContent = JSON.stringify(data.data, null, 2);
});

el("btnManualMatch").addEventListener("click", async () => {
  await callApi("/api/v1/reconcile/manual", "POST", {
    outbound_event_id: el("manualOut").value,
    inbound_event_id: el("manualIn").value,
    note: el("manualNote").value || null,
  });
});

el("btnRun").addEventListener("click", async () => {
  const data = await callApi("/api/v1/process/run", "POST", {
    tax_year: Number(el("taxYear").value || "2026"),
    ruleset_id: el("rulesetId").value || "DE-2026-v1.0",
    config: {},
    dry_run: false,
  });
  if (data?.data?.job_id) {
    el("jobId").value = data.data.job_id;
  }
});

el("btnWorker").addEventListener("click", async () => {
  await callApi("/api/v1/process/worker/run-next", "POST", { simulate_fail: false });
});

el("btnStatus").addEventListener("click", async () => {
  const jobId = el("jobId").value.trim();
  if (!jobId) {
    statusOut.textContent = "Bitte job_id eingeben.";
    return;
  }
  const data = await callApi(`/api/v1/process/status/${jobId}`);
  statusOut.textContent = JSON.stringify(data.data ?? data, null, 2);
});

