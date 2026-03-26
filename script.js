const TYPE_CLASS = {
  KEYWORD:"t-keyword", IDENTIFIER:"t-identifier",
  INTEGER_LITERAL:"t-integer", FLOAT_LITERAL:"t-float",
  STRING_LITERAL:"t-string", CHAR_LITERAL:"t-char",
  OPERATOR:"t-operator", PUNCTUATION:"t-punctuation", UNKNOWN:"t-unknown"
};

let history = JSON.parse(localStorage.getItem("ed-history") || "[]");

// ── ANALYZE (calls Flask backend) ─────────────────────────────
async function runAnalysis() {
  const code = document.getElementById("code-input").value;
  if (!code.trim()) return;

  const btn = document.querySelector(".btn-analyze");
  btn.textContent = "Analyzing…";
  btn.classList.add("loading");
  btn.disabled = true;

  try {
    const res    = await fetch("/analyze", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ code }),
    });
    const result = await res.json();

    history.unshift({
      summary:   result.summary,
      has_errors: result.has_errors,
      snippet:   code.slice(0, 100),
      time:      new Date().toLocaleString("en-US", { month:"short", day:"numeric", hour:"numeric", minute:"2-digit" }),
    });
    history = history.slice(0, 20);
    localStorage.setItem("ed-history", JSON.stringify(history));

    renderResults(result);
    renderTokens(result.tokens);
    renderHistory();
  } catch (err) {
    document.getElementById("results-empty").style.display = "none";
    const el = document.getElementById("results-content");
    el.style.display = "block";
    el.innerHTML = `<div class="summary-banner error"><div class="summary-icon">✕</div><div><div class="summary-title">Server error</div><div class="summary-sub">${err.message}</div></div></div>`;
  } finally {
    btn.textContent = "▶ Analyze Code";
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

// ── RENDER RESULTS ────────────────────────────────────────────
function renderResults(result) {
  document.getElementById("results-empty").style.display = "none";
  const el = document.getElementById("results-content");
  el.style.display = "block";

  const counts = { lexical: 0, syntax: 0, semantic: 0 };
  result.errors.forEach(e => counts[e.phase]++);

  const pillClass = p => counts[p] > 0 ? `${p}-err` : "ok";
  const pillLabel = p => counts[p] > 0 ? `${p} (${counts[p]})` : `${p} ✓`;

  const errCards = result.errors.map(e => `
    <div class="error-card">
      <div class="error-card-header">
        <span class="phase-badge ${e.phase}">${e.phase}</span>
        <span class="error-location">Ln ${e.line}, Col ${e.column}</span>
      </div>
      <div class="error-message">${e.message}</div>
      ${e.token ? `<div class="error-token">Token: <code>${escHtml(e.token)}</code></div>` : ""}
    </div>`).join("");

  el.innerHTML = `
    <div class="summary-banner ${result.has_errors ? "error" : "success"}">
      <div class="summary-icon">${result.has_errors ? "✕" : "✓"}</div>
      <div>
        <div class="summary-title">${result.summary}</div>
        <div class="summary-sub">${result.tokens.length} tokens analyzed</div>
      </div>
    </div>
    <div class="pipeline">
      <span class="phase-pill ${pillClass("lexical")}">${pillLabel("lexical")}</span>
      <span class="arrow">→</span>
      <span class="phase-pill ${pillClass("syntax")}">${pillLabel("syntax")}</span>
      <span class="arrow">→</span>
      <span class="phase-pill ${pillClass("semantic")}">${pillLabel("semantic")}</span>
    </div>
    ${result.has_errors ? errCards : ""}`;
}

// ── RENDER TOKENS ─────────────────────────────────────────────
function renderTokens(tokens) {
  document.getElementById("tokens-empty").style.display = "none";
  const el = document.getElementById("tokens-content");
  el.style.display = "block";

  const rows = tokens.map(t => `
    <div class="token-row">
      <span class="t-pos">${t.line}:${t.column}</span>
      <span class="${TYPE_CLASS[t.type] || "t-unknown"}">${t.type}</span>
      <span class="t-val">${escHtml(t.value === " " ? "SPACE" : t.value)}</span>
    </div>`).join("");

  el.innerHTML = `
    <div style="margin-bottom:6px;font-size:11px;color:#8b949e;">${tokens.length} tokens total</div>
    <div class="token-header"><span>Ln:Col</span><span>Type</span><span>Value</span></div>
    <div class="token-list">${rows}</div>`;
}

// ── RENDER HISTORY ────────────────────────────────────────────
function renderHistory() {
  const el = document.getElementById("history-content");
  if (!history.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-icon">🕐</div><p>No history yet.</p></div>`;
    return;
  }
  const items = history.map(item => `
    <div class="history-item">
      <div class="history-item-header">
        <div class="history-status ${item.has_errors ? "err" : "ok"}">${item.has_errors ? "✕" : "✓"} ${item.summary}</div>
        <span class="history-time">${item.time}</span>
      </div>
      <div class="history-snippet">${escHtml(item.snippet)}</div>
    </div>`).join("");

  el.innerHTML = `
    <div class="history-bar">
      <span class="history-label">Last ${history.length} sessions</span>
      <button class="clear-btn" onclick="clearHistory()">🗑 Clear</button>
    </div>
    ${items}`;
}

function clearHistory() {
  history = [];
  localStorage.removeItem("ed-history");
  renderHistory();
}

// ── TABS ──────────────────────────────────────────────────────
function switchTab(name, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  document.getElementById("tab-" + name).classList.add("active");
}

// ── EDITOR ───────────────────────────────────────────────────
function updateLineNumbers() {
  const lines = document.getElementById("code-input").value.split("\n").length;
  document.getElementById("line-numbers").innerHTML =
    Array.from({ length: Math.max(lines, 1) }, (_, i) =>
      `<div style="height:22px;line-height:22px;">${i + 1}</div>`).join("");
}

function syncScroll() {
  const ta = document.getElementById("code-input");
  document.getElementById("line-numbers").scrollTop = ta.scrollTop;
}

function loadSample() {
  document.getElementById("code-input").value =
`int main() {
    int x = 10;
    int y = 20
    float z = 3.14;

    total = x + y;

    int bad = 9.99;

    int w = x @ y;

    return 0;
}`;
  updateLineNumbers();
  document.getElementById("results-empty").style.display = "flex";
  document.getElementById("results-content").style.display = "none";
}

// ── UTILS ─────────────────────────────────────────────────────
function escHtml(str) {
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── INIT ──────────────────────────────────────────────────────
renderHistory();
updateLineNumbers();