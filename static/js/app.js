// ── Elements ──────────────────────────────────────────────────────────────
const analyzeBtn   = document.getElementById("analyzeBtn");
const repoUrlInput = document.getElementById("repoUrl");
const loading      = document.getElementById("loading");
const repoResults  = document.getElementById("repoResults");
const errorBox     = document.getElementById("errorBox");
const errorMsg     = document.getElementById("errorMsg");

// ── Auto-fill repo URL from query param ───────────────────────────────────
const urlParams     = new URLSearchParams(window.location.search);
const prefilledRepo = urlParams.get("repo");
if (prefilledRepo && repoUrlInput) {
  repoUrlInput.value = prefilledRepo;
}

// ── Loading helpers ───────────────────────────────────────────────────────
function buildStepsHtml(steps) {
  return steps.map((s, i) => `
    <div class="flex items-center gap-3 text-xs text-slate-400">
      <span class="w-5 h-5 rounded-md bg-slate-800 border border-white/8 flex items-center
        justify-center text-slate-500 shrink-0 mono">${i + 1}</span>
      <span class="w-36 shrink-0">${s.label}</span>
      <div class="progress-bar">
        <div class="progress-fill ${s.color}" id="p${i + 1}"></div>
      </div>
    </div>`).join("");
}

function animateSteps(timings) {
  timings.forEach(({ id, delay, dur }) => {
    setTimeout(() => {
      const el = document.getElementById(id);
      if (el) { el.style.transition = `width ${dur}ms linear`; el.style.width = "92%"; }
    }, delay);
  });
}

function finishSteps() {
  ["p1","p2","p3","p4"].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.style.transition = "width 0.4s ease"; el.style.width = "100%"; }
  });
}

function showRepoLoading() {
  document.getElementById("loadingIcon").textContent     = "⚙️";
  document.getElementById("loadingTitle").textContent    = "Analyzing repository...";
  document.getElementById("loadingSubtitle").textContent = "This takes 30–90 seconds depending on repo size";
  document.getElementById("loadingSteps").innerHTML = buildStepsHtml([
    { label: "Cloning repository",  color: "bg-emerald-500" },
    { label: "Complexity scan",     color: "bg-blue-500"    },
    { label: "GPT-4o review",       color: "bg-violet-500"  },
    { label: "Security + ML score", color: "bg-amber-500"   }
  ]);
  loading.classList.remove("hidden");
  animateSteps([
    { id: "p1", delay: 0,     dur: 3000  },
    { id: "p2", delay: 3500,  dur: 6000  },
    { id: "p3", delay: 10000, dur: 55000 },
    { id: "p4", delay: 65000, dur: 12000 }
  ]);
}

// ── Score + label helpers ─────────────────────────────────────────────────
function scoreColor(s) {
  if (s >= 70) return "#ef4444";
  if (s >= 40) return "#eab308";
  return "#10b981";
}

function scoreLabel(s) {
  if (s >= 70) return { text: "Critical", cls: "bg-red-500/10 text-red-400 border-red-500/20" };
  if (s >= 40) return { text: "Moderate", cls: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" };
  return { text: "Healthy", cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" };
}

function sevStyle(sev) {
  if (!sev) return { color: "#475569", cls: "bg-slate-700/40 text-slate-400 border-slate-600/30" };
  if (sev.includes("Critical")) return { color: "#ef4444", cls: "bg-red-500/10 text-red-400 border-red-500/20" };
  if (sev.includes("Moderate")) return { color: "#eab308", cls: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" };
  return { color: "#475569", cls: "bg-slate-700/40 text-slate-400 border-slate-600/30" };
}

function factorBarColor(status) {
  if (status === "high")   return "#ef4444";
  if (status === "medium") return "#eab308";
  return "#10b981";
}

// ── Score breakdown ───────────────────────────────────────────────────────
function buildBreakdown(breakdown) {
  if (!breakdown) return "";

  const verdictBorder = breakdown.score >= 70
    ? "border-red-500/20 bg-red-500/5"
    : breakdown.score >= 40
    ? "border-yellow-500/20 bg-yellow-500/5"
    : "border-emerald-500/20 bg-emerald-500/5";

  const verdictText = breakdown.score >= 70
    ? "text-red-400" : breakdown.score >= 40
    ? "text-yellow-400" : "text-emerald-400";

  const factorsHtml = (breakdown.factors || []).map(f => {
    const barColor = factorBarColor(f.status);
    const barPct   = Math.round((f.points / f.max) * 100);
    const dotColor = f.status === "high"
      ? "bg-red-500" : f.status === "medium"
      ? "bg-yellow-500" : "bg-emerald-500";
    return `
      <div class="p-3 rounded-xl bg-white/2 border border-white/5 space-y-2">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-1.5 h-1.5 rounded-full ${dotColor} shrink-0"></span>
            <span class="text-slate-300 text-xs font-medium">${f.label}</span>
          </div>
          <span class="mono text-xs" style="color:${barColor}">${f.points}/${f.max} pts</span>
        </div>
        <div class="w-full h-1 rounded-full bg-white/5 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-1000"
            style="width:${barPct}%; background:${barColor}"></div>
        </div>
        <p class="text-slate-500 text-xs leading-5">${f.explanation}</p>
        <div class="flex items-start gap-1.5">
          <span class="text-sky-500 text-xs shrink-0">→</span>
          <p class="text-sky-400/80 text-xs leading-5">${f.fix}</p>
        </div>
      </div>`;
  }).join("");

  const stepsHtml = (breakdown.next_steps || []).map((step, i) => `
    <li class="flex items-start gap-3 text-xs text-slate-400 leading-5">
      <span class="w-4 h-4 rounded-md bg-slate-800 border border-white/8 text-slate-500
        flex items-center justify-center shrink-0 font-mono mt-0.5">${i + 1}</span>
      ${step}
    </li>`).join("");

  return `
    <div class="mt-4 pt-4 border-t border-white/5 space-y-4">
      <div class="rounded-xl border ${verdictBorder} p-3 flex items-start gap-3">
        <span class="text-base shrink-0">🔎</span>
        <div>
          <p class="text-xs font-semibold ${verdictText} mb-0.5">Score Explanation</p>
          <p class="text-slate-400 text-xs leading-5">${breakdown.verdict}</p>
        </div>
      </div>
      <div>
        <p class="text-xs text-slate-600 uppercase tracking-widest mb-2 font-semibold">Score Factors</p>
        <div class="space-y-2">${factorsHtml}</div>
      </div>
      <div>
        <p class="text-xs text-slate-600 uppercase tracking-widest mb-2 font-semibold">How to Improve</p>
        <ul class="space-y-2">${stepsHtml}</ul>
      </div>
    </div>`;
}

// ── Issue row ─────────────────────────────────────────────────────────────
function buildIssueRow(issue) {
  const s = sevStyle(issue.severity);
  return `
    <div class="issue-card pl-4 py-3 rounded-r-xl space-y-2" style="--ic: ${s.color}">
      <div class="flex flex-wrap items-center gap-2">
        <span class="tag border ${s.cls}">${issue.severity || "Info"}</span>
        <span class="tag bg-slate-800 text-slate-500 border border-white/5">${issue.issue_type || ""}</span>
        ${issue.line_range    ? `<span class="mono text-xs text-slate-600">${issue.line_range}</span>` : ""}
        ${issue.function_name ? `<span class="mono text-xs text-sky-500">${issue.function_name}()</span>` : ""}
      </div>
      <p class="text-slate-300 text-sm leading-6">${issue.description || ""}</p>
      <div class="flex items-start gap-2">
        <span class="text-emerald-500 text-xs shrink-0 mt-0.5">→</span>
        <p class="text-emerald-400/80 text-xs leading-5">${issue.suggestion || ""}</p>
      </div>
    </div>`;
}

// ── File card ─────────────────────────────────────────────────────────────
function buildFileCard(file) {
  const color = scoreColor(file.debt_score);
  const label = scoreLabel(file.debt_score);
  const pct   = Math.min(file.debt_score, 100);

  const issuesHtml = file.issues?.length
    ? file.issues.map(buildIssueRow).join("")
    : `<p class="text-slate-700 text-xs italic py-1">No line-level issues detected</p>`;

  return `
    <div class="glass glass-hover rounded-2xl overflow-hidden">
      <div class="px-5 py-4 border-b border-white/5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-8 h-8 rounded-lg bg-slate-800 border border-white/5 flex items-center justify-center text-xs shrink-0">📄</div>
          <div class="min-w-0">
            <p class="mono text-sm font-medium text-slate-200 truncate">${file.file_path}</p>
            <div class="flex flex-wrap gap-4 mt-1 text-xs text-slate-700">
              <span>Churn <span class="text-slate-500">${file.churn_rate}</span></span>
              <span>Complexity <span class="text-slate-500">${file.complexity}</span></span>
              <span>Issues <span class="text-slate-500">${file.issues?.length || 0}</span></span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <div class="score-bar rotate-180">
            <div class="score-bar-fill" style="height:${pct}%; background:${color}"></div>
          </div>
          <div class="text-right">
            <div class="flex items-end gap-0.5 justify-end">
              <span class="text-4xl font-black leading-none" style="color:${color}">${file.debt_score}</span>
              <span class="text-slate-700 text-xs mb-1">/100</span>
            </div>
            <span class="tag border ${label.cls} mt-1 inline-block">${label.text}</span>
          </div>
        </div>
      </div>
      <div class="px-5 py-4 space-y-3">
        ${issuesHtml}
        ${buildBreakdown(file.breakdown)}
      </div>
    </div>`;
}

function emptyCard(msg) {
  return `<div class="glass rounded-2xl p-6 text-center text-slate-600 text-sm">${msg}</div>`;
}

function renderRecommendations(elId, items) {
  document.getElementById(elId).innerHTML = items?.length
    ? items.map((r, i) => `
        <li class="flex items-start gap-4 p-3 rounded-xl hover:bg-white/3 transition group cursor-default">
          <span class="w-6 h-6 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs
            flex items-center justify-center shrink-0 font-bold mt-0.5">${i + 1}</span>
          <span class="text-slate-400 text-sm leading-7 group-hover:text-slate-300 transition">${r}</span>
        </li>`).join("")
    : `<li class="text-slate-600 text-sm p-3">No recommendations at this time</li>`;
}

// ── Repo analysis ─────────────────────────────────────────────────────────
async function runRepoAnalysis() {
  const repoUrl = repoUrlInput.value.trim();
  if (!repoUrl || !repoUrl.startsWith("https://github.com/")) {
    errorMsg.textContent = "Please enter a valid GitHub URL — https://github.com/username/repo";
    errorBox.classList.remove("hidden");
    return;
  }

  errorBox.classList.add("hidden");
  repoResults.classList.add("hidden");
  showRepoLoading();
  analyzeBtn.disabled    = true;
  analyzeBtn.textContent = "Analyzing...";
  analyzeBtn.classList.add("opacity-60", "cursor-not-allowed");

  try {
    const res  = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl })
    });
    const data = await res.json();
    finishSteps();

    if (data.error) {
      errorMsg.textContent = data.error;
      errorBox.classList.remove("hidden");
      return;
    }

    const allFiles    = [...(data.critical_files||[]), ...(data.moderate_files||[]), ...(data.healthy_files||[])];
    const totalIssues = allFiles.reduce((a, f) => a + (f.issues?.length || 0), 0);

    document.getElementById("statTotal").textContent    = data.total_files_analyzed ?? 0;
    document.getElementById("statCritical").textContent = data.critical_files?.length ?? 0;
    document.getElementById("statModerate").textContent = data.moderate_files?.length ?? 0;
    document.getElementById("statIssues").textContent   = totalIssues;
    document.getElementById("summaryText").textContent  = data.summary || "";

    const rl       = document.getElementById("repoLink");
    rl.textContent = data.repo_url;
    rl.href        = data.repo_url;

    document.getElementById("criticalCount").textContent = `${data.critical_files?.length || 0} files`;
    document.getElementById("criticalFiles").innerHTML   = data.critical_files?.length
      ? data.critical_files.map(buildFileCard).join("")
      : emptyCard("🎉 No critical hotspots found — great work!");

    document.getElementById("moderateCount").textContent = `${data.moderate_files?.length || 0} files`;
    document.getElementById("moderateFiles").innerHTML   = data.moderate_files?.length
      ? data.moderate_files.map(buildFileCard).join("")
      : emptyCard("No moderate risk files found");

    document.getElementById("healthyCount").textContent = `${data.healthy_files?.length || 0} files`;
    document.getElementById("healthyFiles").innerHTML   = data.healthy_files?.length
      ? data.healthy_files.map(buildFileCard).join("")
      : emptyCard("No healthy-scored files to display");

    renderRecommendations("recommendationsList", data.recommendations);

    repoResults.classList.remove("hidden");
    setTimeout(() => repoResults.scrollIntoView({ behavior: "smooth", block: "start" }), 100);

  } catch (err) {
    errorMsg.textContent = "Network error — " + err.message;
    errorBox.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
    analyzeBtn.disabled    = false;
    analyzeBtn.textContent = "Analyze Repo →";
    analyzeBtn.classList.remove("opacity-60", "cursor-not-allowed");
  }
}

// ── Event listeners ───────────────────────────────────────────────────────
analyzeBtn?.addEventListener("click", runRepoAnalysis);
repoUrlInput?.addEventListener("keydown", e => { if (e.key === "Enter") runRepoAnalysis(); });

document.getElementById("themeToggle")?.addEventListener("click", () => {
  document.documentElement.classList.toggle("dark");
  localStorage.setItem("theme",
    document.documentElement.classList.contains("dark") ? "dark" : "light"
  );
});

if (localStorage.getItem("theme") === "dark") {
  document.documentElement.classList.add("dark");
}