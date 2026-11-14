(function () {
  "use strict";

  /* ─────────────────────────────────────────
     DOM refs
  ───────────────────────────────────────── */
  const shell       = document.querySelector(".app-shell");
  const testForm    = document.getElementById("testForm");
  const targetUrl   = document.getElementById("targetUrl");
  const runBtn      = document.getElementById("runAgentsBtn");

  // Stat cards
  const statTotal    = document.getElementById("statTotal");
  const statPassed   = document.getElementById("statPassed");
  const statFail     = document.getElementById("statFail");
  const statPassRate = document.getElementById("statPassRate");

  // Dashboard panel
  const runDuration    = document.getElementById("runDuration");
  const runProgressText= document.getElementById("runProgressText");
  const passRateBar    = document.getElementById("passRateBar");
  const categoryGrid   = document.getElementById("categoryGrid");
  const categoryStatus = document.getElementById("categoryStatus");
  const failureList    = document.getElementById("failureList");
  const runStatus      = document.getElementById("runStatus");

  // Sidebar pills
  const wsSiteName       = document.getElementById("wsSiteName");
  const wsLastRun        = document.getElementById("wsLastRun");
  const wsPillPassedCount= document.getElementById("wsPillPassedCount");
  const wsPillFailedCount= document.getElementById("wsPillFailedCount");
  const wsPillTotalCount = document.getElementById("wsPillTotalCount");

  // Test results panel
  const testResultsBody  = document.getElementById("testResultsBody");
  const testResultsSub   = document.getElementById("testResultsSub");
  const trPillPassed     = document.getElementById("trPillPassed");
  const trPillFailed     = document.getElementById("trPillFailed");
  const trPillTotal      = document.getElementById("trPillTotal");

  // Failure analysis
  const failureAnalysisList = document.getElementById("failureAnalysisList");

  // Solutions
  const solutionsList = document.getElementById("solutionsList");

  // Reports
  const reportFileList = document.getElementById("reportFileList");
  const reportGenDate  = document.getElementById("reportGenDate");
  const execSummary    = document.getElementById("execSummary");
  const execTags       = document.getElementById("execTags");
  const reportLink     = document.getElementById("reportLink");

  // Sidebar & toggle
  const sidebar     = document.getElementById("wsSidebar");
  const menuToggle  = document.getElementById("wsMenuToggle");
  const themeToggle = document.getElementById("themeToggle");

  /* ─────────────────────────────────────────
     Dark / Light Mode
  ───────────────────────────────────────── */
  function applyTheme(dark) {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    const moon = themeToggle?.querySelector(".icon-moon");
    const sun  = themeToggle?.querySelector(".icon-sun");
    if (moon) moon.style.display = dark ? "none" : "";
    if (sun)  sun.style.display  = dark ? "" : "none";
    localStorage.setItem("qa-theme", dark ? "dark" : "light");
  }

  // Restore saved theme on load
  const savedTheme = localStorage.getItem("qa-theme");
  applyTheme(savedTheme === "dark");

  themeToggle?.addEventListener("click", () => {
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    applyTheme(!isDark);
  });

  /* ─────────────────────────────────────────
     View switching
  ───────────────────────────────────────── */
  function switchView(view) {
    shell?.setAttribute("data-view", view);
    if (view === "workspace") {
      targetUrl?.focus();
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  document.addEventListener("click", (e) => {
    const trigger = e.target.closest("[data-action]");
    if (!trigger) return;
    e.preventDefault();
    const action = trigger.dataset.action;
    if (action === "open-workspace") switchView("workspace");
    if (action === "landing") switchView("landing");
  });

  /* ─────────────────────────────────────────
     Sidebar panel navigation
  ───────────────────────────────────────── */
  const panelMap = {
    "dashboard":       "panelDashboard",
    "test-results":    "panelTestResults",
    "failure-analysis":"panelFailureAnalysis",
    "solutions":       "panelSolutions",
    "reports":         "panelReports",
  };

  function activatePanel(panelKey) {
    // Update nav items
    document.querySelectorAll(".ws-nav-item").forEach(a => {
      a.classList.toggle("active", a.dataset.panel === panelKey);
    });
    // Update panels
    Object.keys(panelMap).forEach(key => {
      const el = document.getElementById(panelMap[key]);
      if (!el) return;
      if (key === panelKey) {
        el.removeAttribute("hidden");
        el.classList.add("active");
      } else {
        el.setAttribute("hidden", "");
        el.classList.remove("active");
      }
    });
    // Close mobile sidebar
    sidebar?.classList.remove("open");
  }

  document.querySelectorAll(".ws-nav-item[data-panel]").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      activatePanel(link.dataset.panel);
    });
  });

  // Mobile menu toggle
  menuToggle?.addEventListener("click", () => {
    sidebar?.classList.toggle("open");
  });

  // Close sidebar on outside click (mobile)
  document.addEventListener("click", e => {
    if (sidebar?.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        e.target !== menuToggle) {
      sidebar.classList.remove("open");
    }
  });

  /* ─────────────────────────────────────────
     Landing smooth scroll
  ───────────────────────────────────────── */
  document.querySelectorAll('.nav-links a, a[href^="#"]').forEach(link => {
    link.addEventListener("click", e => {
      const href = link.getAttribute("href");
      if (!href || !href.startsWith("#") || href.length <= 1) return;
      const target = document.getElementById(href.slice(1));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  /* ─────────────────────────────────────────
     Utilities
  ───────────────────────────────────────── */
  function setText(el, val) { if (el) el.textContent = val; }

  function escHtml(text) {
    const d = document.createElement("div");
    d.textContent = text || "";
    return d.innerHTML;
  }

  function truncateUrl(url) {
    if (!url) return "No URL";
    try {
      const p = new URL(url);
      const path = p.pathname && p.pathname !== "/" ? p.pathname : "";
      return p.hostname + path;
    } catch {
      return url.length > 52 ? url.slice(0, 52) + "…" : url;
    }
  }

  function formatDate(value) {
    if (!value) return "Unknown time";
    const d = new Date(value);
    if (isNaN(d)) return value;
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function getPassRate(pass, total) {
    return total > 0 ? Math.round((pass / total) * 100) : 0;
  }

  function categoryPillClass(name) {
    const map = {
      ui: "ws-pill-ui",
      navigation: "ws-pill-nav",
      auth: "ws-pill-auth",
      forms: "ws-pill-forms",
      validation: "ws-pill-validation",
      "edge cases": "ws-pill-edge",
      "website description": "ws-pill-total",
    };
    return map[(name || "").toLowerCase()] || "ws-pill-total";
  }

  /* ─────────────────────────────────────────
     Summary update
  ───────────────────────────────────────── */
  function updateSummary(summary, opts = {}) {
    const total = Number(summary?.total ?? 0);
    const pass  = Number(summary?.pass  ?? 0);
    const fail  = Number(summary?.fail  ?? 0);
    const rate  = getPassRate(pass, total);
    const ms    = Number(summary?.duration_ms ?? 0);

    setText(statTotal,    total.toString());
    setText(statPassed,   pass.toString());
    setText(statFail,     fail.toString());
    setText(statPassRate, `${rate}%`);

    setText(runProgressText, `${pass} / ${total} tests passed`);
    setText(runDuration, ms > 0 ? `Duration: ${(ms / 1000).toFixed(1)}s` : "Duration: --");
    if (passRateBar) passRateBar.style.width = `${rate}%`;

    // Sidebar pills
    setText(wsPillPassedCount, pass.toString());
    setText(wsPillFailedCount, fail.toString());
    setText(wsPillTotalCount,  total.toString());

    // Test results pills
    setText(trPillPassed, `${pass} passed`);
    setText(trPillFailed, `${fail} failed`);
    setText(trPillTotal,  `${total} total`);
    setText(testResultsSub, total > 0
      ? `${total} test cases · ${pass} passed · ${fail} failed`
      : "Run a test to see individual test case results.");

    if (opts.url) {
      setText(wsSiteName, truncateUrl(opts.url));
      setText(wsLastRun,  opts.lastRun || "Just now");
    }
    if (opts.statusText) setText(runStatus, opts.statusText);
  }

  /* ─────────────────────────────────────────
     Category rendering
  ───────────────────────────────────────── */
  function renderCategories(categories) {
    if (!categoryGrid) return;
    const ordered = ["UI", "Navigation", "Forms", "Auth"];
    const byName  = new Map((categories || []).map(c => [c.name, c]));

    categoryGrid.innerHTML = ordered.map(name => {
      const item = byName.get(name) || { pass: 0, total: 0, fail: 0 };
      const hasFail = Number(item.fail || 0) > 0;
      return `<div class="ws-cat-item${hasFail ? " has-failures" : ""}">
        <strong>${Number(item.pass || 0)}/${Number(item.total || 0)}</strong>
        <span>${escHtml(name)}</span>
      </div>`;
    }).join("");

    setText(categoryStatus, categories?.length ? "Completed" : "Waiting for test");
  }

  /* ─────────────────────────────────────────
     Top failures (dashboard card)
  ───────────────────────────────────────── */
  function renderTopFailures(failures) {
    if (!failureList) return;
    if (!failures?.length) {
      failureList.innerHTML = '<p class="ws-empty">No failures yet.</p>';
      return;
    }
    failureList.innerHTML = failures.slice(0, 5).map(f => {
      const sev = f.severity || "high";
      const sevClass = sev === "critical" ? "ws-pill-critical" : "ws-pill-high";
      return `<article class="ws-failure-item">
        <div class="ws-failure-title">
          <span>${escHtml(f.test_name || "Failed check")}</span>
          <span class="ws-pill ${sevClass}">${escHtml(sev)}</span>
        </div>
        <p>${escHtml(f.detail || "No detail provided.")}</p>
      </article>`;
    }).join("");
  }

  /* ─────────────────────────────────────────
     Test Results table
  ───────────────────────────────────────── */
  function renderTestResults(tests) {
    if (!testResultsBody) return;
    if (!tests?.length) {
      testResultsBody.innerHTML = '<tr class="ws-empty-row"><td colspan="5"><p class="ws-empty">No test results yet. Run a test first.</p></td></tr>';
      return;
    }
    testResultsBody.innerHTML = tests.map((t, i) => {
      const id   = t.id || `TC_${String(i + 1).padStart(3, "0")}`;
      const name = t.test_name || t.name || "Unnamed test";
      const cat  = t.category || "general";
      const status = String(t.status || "").toUpperCase();
      const pass = status === "PASS" || status === "INFO";
      const dur  = t.duration_ms != null ? `${(t.duration_ms / 1000).toFixed(1)}s` : (t.duration || "--");
      const statusHtml = pass
        ? `<span class="ws-status-passed">✓ passed</span>`
        : `<span class="ws-status-failed">✗ failed</span>`;
      return `<tr>
        <td><span class="ws-tc-id">${escHtml(id)}</span></td>
        <td><span class="ws-tc-name">${escHtml(name)}</span></td>
        <td><span class="ws-pill ${categoryPillClass(cat)}">${escHtml(cat)}</span></td>
        <td>${statusHtml}</td>
        <td><span class="ws-tc-duration">${escHtml(dur)}</span></td>
      </tr>`;
    }).join("");

    testResultsBody.querySelectorAll("tr").forEach((row, index) => {
      const status = String(tests[index]?.status || "INFO").toUpperCase();
      const cell = row.children[3];
      if (!cell) return;

      const badge = document.createElement("span");
      badge.textContent = status;
      badge.className = status === "PASS"
        ? "ws-status-passed"
        : status === "FAIL" || status === "ERROR"
          ? "ws-status-failed"
          : "ws-status-info";
      cell.replaceChildren(badge);
    });
  }

  /* ─────────────────────────────────────────
     Failure Analysis panel
  ───────────────────────────────────────── */
  function renderFailureAnalysis(failures) {
    if (!failureAnalysisList) return;
    if (!failures?.length) {
      failureAnalysisList.innerHTML = '<p class="ws-empty ws-empty-pad">No failures to analyze. Run a test first.</p>';
      return;
    }
    failureAnalysisList.innerHTML = failures.map(f => {
      const sev = f.severity || "high";
      const sevClass = sev === "critical" ? "ws-pill-critical" : "ws-pill-high";
      const bars = (f.root_causes || []).map(rc => `
        <div class="ws-analysis-bar-row">
          <span class="ws-analysis-bar-label">${escHtml(rc.label)}</span>
          <div class="ws-analysis-bar-track">
            <div class="ws-analysis-bar-fill" style="width:${Number(rc.confidence || 0)}%"></div>
          </div>
          <span class="ws-analysis-bar-pct">${Number(rc.confidence || 0)}%</span>
        </div>`).join("");
      return `<article class="ws-analysis-item">
        <div class="ws-analysis-head">
          <span class="ws-analysis-title">${escHtml(f.test_name || "Failed check")}</span>
          <span class="ws-pill ${sevClass}">${escHtml(sev)}</span>
        </div>
        <p class="ws-analysis-desc">${escHtml(f.detail || f.description || "No description.")}</p>
        ${bars ? `<div class="ws-analysis-bars">${bars}</div>` : ""}
      </article>`;
    }).join("");
  }

  /* ─────────────────────────────────────────
     Solutions panel
  ───────────────────────────────────────── */
  function renderSolutions(solutions) {
    if (!solutionsList) return;
    if (!solutions?.length) {
      solutionsList.innerHTML = '<p class="ws-empty ws-empty-pad">No solutions yet. Run a test first.</p>';
      return;
    }
    solutionsList.innerHTML = solutions.map(s => {
      const codeBlock = s.code_snippet
        ? `<div class="ws-code-block"><code>${escHtml(s.code_snippet)}</code></div>` : "";
      const effort = s.effort ? `<span class="ws-effort-tag">Effort: ${escHtml(s.effort)}</span>` : "";
      const impact = s.impact ? `<span class="ws-effort-tag">Impact: ${escHtml(s.impact)}</span>` : "";
      const tcRef  = s.test_id
        ? `<span class="ws-pill ws-pill-total" style="font-size:10px">${escHtml(s.test_id)}</span>` : "";
      return `<article class="ws-analysis-item">
        <div class="ws-analysis-head">
          <span class="ws-analysis-title">${escHtml(s.title || "Recommended fix")}</span>
          ${tcRef}
        </div>
        <p class="ws-analysis-desc">${escHtml(s.description || "")}</p>
        ${codeBlock}
        <div class="ws-solution-tags">${effort}${impact}</div>
      </article>`;
    }).join("");
  }

  /* ─────────────────────────────────────────
     Reports panel
  ───────────────────────────────────────── */
  function renderReports(result) {
    const now = new Date().toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
    setText(reportGenDate, now);

    // File list
    if (reportFileList) {
      const files = result?.report_files || [];
      if (!files.length && result?.report_url) {
        files.push({ name: "qa_report.html", type: "html", url: result.report_url, size: "Self-contained" });
      }
      if (!files.length) {
        reportFileList.innerHTML = '<p class="ws-empty">No reports generated yet.</p>';
      } else {
        reportFileList.innerHTML = files.map(f => {
          const ext = (f.type || f.name || "").toLowerCase().includes("pdf") ? "pdf" : "html";
          const action = ext === "pdf" ? "Download ↗" : "Open ↗";
          return `<div class="ws-report-file">
            <div class="ws-report-icon ${ext}">${ext.toUpperCase()}</div>
            <div class="ws-report-info">
              <strong>${escHtml(f.name || "report." + ext)}</strong>
              <small>${escHtml(f.size || "")} · Generated ${now}</small>
            </div>
            <a class="ws-report-btn" href="${escHtml(f.url || "#")}" target="_blank" rel="noreferrer">${action}</a>
          </div>`;
        }).join("");
      }
    }

    // Executive summary
    const total = Number(result?.summary?.total ?? 0);
    const pass  = Number(result?.summary?.pass  ?? 0);
    const fail  = Number(result?.summary?.fail  ?? 0);
    const rate  = getPassRate(pass, total);
    const url   = result?.target_url || "";

    if (execSummary) {
      if (total > 0) {
        execSummary.textContent = `Testing of ${truncateUrl(url)} completed with a ${rate}% pass rate (${pass}/${total} tests). ${fail > 0 ? `${fail} issue${fail !== 1 ? "s" : ""} were identified. Review the Failure analysis and Solutions tabs for details.` : "All tests passed successfully."}`;
      } else {
        execSummary.textContent = "Run a test to generate an executive summary of the results.";
      }
    }

    // Exec tags
    if (execTags) {
      const failures = result?.failures || [];
      const tags = failures.slice(0, 4).map(f => f.test_name || "issue");
      execTags.innerHTML = tags.map(t => `<span class="ws-exec-tag">${escHtml(t)}</span>`).join("");
    }
  }

  /* ─────────────────────────────────────────
     Button loading state
  ───────────────────────────────────────── */
  function setLoading(loading) {
    if (!runBtn) return;
    const textEl = runBtn.querySelector("span");
    const iconEl = runBtn.querySelector("svg");
    if (loading) {
      runBtn.dataset.prev = textEl?.textContent || "Test";
      if (textEl) textEl.textContent = "Running…";
      if (iconEl) iconEl.style.display = "none";
      const sp = document.createElement("span");
      sp.className = "spinner";
      sp.dataset.spinner = "true";
      runBtn.prepend(sp);
      runBtn.classList.add("loading");
      runBtn.disabled = true;
    } else {
      runBtn.querySelector("[data-spinner]")?.remove();
      if (textEl) textEl.textContent = runBtn.dataset.prev || "Test";
      if (iconEl) iconEl.style.display = "";
      runBtn.classList.remove("loading");
      runBtn.disabled = false;
    }
  }

  /* ─────────────────────────────────────────
     Form submit — run test
  ───────────────────────────────────────── */
  testForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = targetUrl?.value.trim();
    if (!url) return;

    setLoading(true);
    setText(runStatus, `Testing ${truncateUrl(url)}…`);

    try {
      const res = await fetch("/api/test-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
        throw new Error(err.detail || `Request failed ${res.status}`);
      }

      const result = await res.json();
      const summary = result.summary || {};

      updateSummary(summary, {
        url,
        lastRun: "Just now",
        statusText: `Completed — ${summary.pass || 0} passed, ${summary.fail || 0} failed`,
      });

      const failures  = result.failures  || [];
      const tests     = result.tests     || result.test_results || [];
      const solutions = result.solutions || result.fixes || [];
      const categories= result.categories|| [];

      renderCategories(categories);
      renderTopFailures(failures);
      renderTestResults(tests);
      renderFailureAnalysis(failures);
      renderSolutions(solutions);
      renderReports(result);

      if (reportLink) {
        if (result.report_url) {
          reportLink.href = result.report_url;
          reportLink.classList.remove("disabled");
        }
      }
    } catch (err) {
      setText(runStatus, `Run failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  });

  /* ─────────────────────────────────────────
     Hero counter animation
  ───────────────────────────────────────── */
  function animateCounter(el, target, fmt) {
    const dur = 1500;
    const start = performance.now();
    (function step(now) {
      const p = Math.min((now - start) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(target * e);
      if (p < 1) requestAnimationFrame(step);
    })(performance.now());
  }

  const heroVisual = document.querySelector(".hero-visual");
  if (heroVisual) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(en => {
        if (!en.isIntersecting) return;
        const t = document.getElementById("heroTotal");
        const b = document.getElementById("heroBroken");
        const i = document.getElementById("heroIntegrity");
        if (t) animateCounter(t, 12482, v => Math.round(v).toLocaleString());
        if (b) animateCounter(b, 42, v => Math.round(v).toString());
        if (i) animateCounter(i, 98.2, v => `${v.toFixed(1)}%`);
        obs.unobserve(en.target);
      });
    }, { threshold: 0.3 });
    obs.observe(heroVisual);
  }

  /* ─────────────────────────────────────────
     Landing nav highlight
  ───────────────────────────────────────── */
  const navLinks = document.querySelectorAll(".nav-links a");
  const sections = ["dashboard", "features", "reports"];

  function highlightNav() {
    const scrollY = window.scrollY + 100;
    let current = "";
    sections.forEach(id => {
      const sec = document.getElementById(id);
      if (sec && sec.offsetTop <= scrollY) current = id;
    });
    navLinks.forEach(a => {
      a.classList.toggle("active", a.getAttribute("href") === `#${current}`);
    });
  }
  window.addEventListener("scroll", highlightNav);

  /* ─────────────────────────────────────────
     Init
  ───────────────────────────────────────── */
  renderCategories([]);
  renderTopFailures([]);
  activatePanel("dashboard");
})();
