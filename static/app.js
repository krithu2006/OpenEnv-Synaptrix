const initialPage = (() => {
  const queryPage = new URLSearchParams(window.location.search).get("page");
  if (queryPage && ["summary", "automation", "tasks", "reply", "analytics", "history", "health", "composer", "settings"].includes(queryPage)) {
    return queryPage;
  }
  return document.body.dataset.page || "summary";
})();
const PAGES = {
  summary: {
    label: "Summary",
    title: "Decision Summary",
    description: "See how the Synaptrix agents classify, score, and prioritize the current email.",
    path: "/",
  },
  automation: {
    label: "Automation",
    title: "Automation Center",
    description: "Track Gmail-style labels, folder routing, urgent highlighting, and inbox lane placement.",
    path: "/?page=automation",
  },
  tasks: {
    label: "Tasks",
    title: "Tasks And Alerts",
    description: "Review extracted tasks, action signals, and follow-through prompts generated from email content.",
    path: "/?page=tasks",
  },
  reply: {
    label: "Reply",
    title: "Reply Studio",
    description: "Polish AI-generated drafts, review response guidance, and simulate one-click sending.",
    path: "/?page=reply",
  },
  analytics: {
    label: "Analytics",
    title: "Analytics View",
    description: "Measure productivity, risk trends, inbox routing, and reward performance across processed emails.",
    path: "/?page=analytics",
  },
  history: {
    label: "History",
    title: "Processing History",
    description: "Audit how each email was handled, what reward it earned, and which decision path was chosen.",
    path: "/?page=history",
  },
  health: {
    label: "AI Health",
    title: "AI Health Monitor",
    description: "Inspect confidence, threat indicators, response windows, and overall decision quality signals.",
    path: "/?page=health",
  },
  composer: {
    label: "Composer",
    title: "Composer Sandbox",
    description: "Paste or type a fresh email and run it through the full Synaptrix intelligence workflow.",
    path: "/?page=composer",
  },
  settings: {
    label: "Settings",
    title: "Workspace Settings",
    description: "Personalize the workspace mood, density, workflow routing, and alerts to match your style.",
    path: "/?page=settings",
  },
};

const SETTINGS_KEY = "synaptrix-mailos-settings-v3";

function defaultSettings() {
  return {
    theme: "system",
    colorTheme: "teal",
    surface: "glass",
    density: "cozy",
    motion: "rich",
    focusPage: "automation",
    defaultLane: "Urgent",
    alertMode: "balanced",
  };
}

const state = {
  page: initialPage,
  snapshot: null,
  activeLane: "Urgent",
  loading: false,
  error: "",
  replyStatus: "No simulated reply sent yet.",
  settings: defaultSettings(),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function loadSettings() {
  const raw = window.localStorage.getItem(SETTINGS_KEY);
  if (!raw) {
    state.settings = defaultSettings();
    state.activeLane = state.settings.defaultLane;
    return;
  }
  try {
    state.settings = { ...defaultSettings(), ...JSON.parse(raw) };
    state.activeLane = state.settings.defaultLane;
  } catch (error) {
    console.error("Failed to parse settings", error);
    state.settings = defaultSettings();
    state.activeLane = state.settings.defaultLane;
  }
}

function saveSettings() {
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(state.settings));
}

function resolvedTheme() {
  if (state.settings.theme === "light" || state.settings.theme === "dark") {
    return state.settings.theme;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyPreferences() {
  const root = document.documentElement;
  root.setAttribute("data-theme", resolvedTheme());
  root.setAttribute("data-color-theme", state.settings.colorTheme);
  root.setAttribute("data-surface", state.settings.surface);
  root.setAttribute("data-density", state.settings.density);
  root.setAttribute("data-motion", state.settings.motion);
}

function updateSetting(key, value) {
  state.settings[key] = value;
  if (key === "defaultLane") {
    state.activeLane = value;
  }
  saveSettings();
  applyPreferences();
  render();
}

function toggleTheme() {
  state.settings.theme = resolvedTheme() === "dark" ? "light" : "dark";
  saveSettings();
  applyPreferences();
  render();
}

function resetSettings() {
  state.settings = defaultSettings();
  state.activeLane = state.settings.defaultLane;
  saveSettings();
  applyPreferences();
  render();
}

function currentEmail() {
  return state.snapshot?.current_email || null;
}

function currentAnalysis() {
  return state.snapshot?.current_analysis || null;
}

function analytics() {
  return state.snapshot?.analytics || {};
}

function smartInbox() {
  return analytics().smart_inbox || {};
}

function historyRecords() {
  return state.snapshot?.history || [];
}

function pageConfig() {
  return PAGES[state.page] || PAGES.summary;
}

function pagePath(key) {
  return (PAGES[key] || PAGES.summary).path;
}

function labelFor(email) {
  return email?.gmail_label || email?.label || "Unprocessed";
}

function folderFor(email) {
  return email?.mailbox_folder || email?.folder || "Inbox";
}

function sourceFor(email) {
  return email?.source === "custom" ? "Custom" : "Sample";
}

function previewFor(email) {
  const text = email?.preview || email?.body || "";
  return text.length > 180 ? `${text.slice(0, 177)}...` : text;
}

function numberOrZero(value) {
  return value ?? 0;
}

function percent(value) {
  return `${numberOrZero(value)}%`;
}

function updateLaneFromSnapshot(snapshot) {
  const lane = snapshot?.current_analysis?.automation?.inbox_lane;
  if (lane) {
    state.activeLane = lane;
  }
}

function topAlerts(items) {
  const alerts = items || [];
  const limit = state.settings.alertMode === "quiet"
    ? 1
    : state.settings.alertMode === "watchtower"
      ? 4
      : 2;
  return alerts.slice(0, limit);
}

function metricCard(label, value, note = "") {
  return `
    <article class="sx-metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
      <small>${escapeHtml(note)}</small>
    </article>
  `;
}

function emptyState(message) {
  return `<div class="sx-empty">${escapeHtml(message)}</div>`;
}

function chip(text) {
  return `<span class="sx-chip">${escapeHtml(text)}</span>`;
}

function barChart(data, emptyMessage) {
  const entries = Object.entries(data || {});
  if (!entries.length) {
    return emptyState(emptyMessage);
  }
  const maxValue = Math.max(...entries.map(([, value]) => value), 1);
  return `
    <div class="sx-bar-list">
      ${entries.map(([label, value]) => {
        const width = value > 0 ? Math.max((value / maxValue) * 100, 8) : 0;
        return `
          <div class="sx-bar-row">
            <span>${escapeHtml(label)}</span>
            <div class="sx-bar-track"><div class="sx-bar-fill" style="width:${width}%"></div></div>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function rewardChart(trend) {
  if (!trend?.length) {
    return emptyState("Reward trend appears after the system processes emails.");
  }
  const maxMagnitude = Math.max(...trend.map((entry) => Math.abs(entry.reward)), 10);
  return `
    <div class="sx-reward-chart">
      ${trend.map((entry) => {
        const height = Math.max((Math.abs(entry.reward) / maxMagnitude) * 136, 14);
        const tone = entry.reward >= 0 ? "sx-positive" : "sx-negative";
        return `
          <div class="sx-reward-column">
            <small>${escapeHtml(entry.label)}</small>
            <div class="sx-reward-bar-shell">
              <div class="sx-reward-bar ${tone}" style="height:${height}px"></div>
            </div>
            <span>${escapeHtml(entry.reward)}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function scoreRows(items) {
  return `
    <div class="sx-score-list">
      ${items.map((item) => `
        <div class="sx-score-row">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function alertList(items, emptyMessage) {
  if (!items?.length) {
    return emptyState(emptyMessage);
  }
  return `
    <div class="sx-alert-list">
      ${items.map((item) => `<article class="sx-alert">${escapeHtml(item)}</article>`).join("")}
    </div>
  `;
}

function historyList(records) {
  if (!records?.length) {
    return emptyState("No email decisions have been recorded yet.");
  }
  return `
    <div class="sx-feed">
      ${records.map((record) => `
        <article class="sx-feed-item">
          <div class="sx-feed-head">
            <strong>${escapeHtml(record.email.subject)}</strong>
            <span class="sx-chip">${escapeHtml(record.chosen_action)}</span>
          </div>
          <div class="sx-feed-meta">
            <span>${escapeHtml(record.analysis.classification.category)} | ${escapeHtml(record.analysis.risk.priority)} | ${escapeHtml(record.analysis.automation.inbox_lane)}</span>
            <span>Reward ${escapeHtml(record.reward_score)} | ${escapeHtml(record.mailbox_folder)}</span>
          </div>
          <p>${escapeHtml(record.notes)}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function taskList(tasks) {
  if (!tasks?.length) {
    return emptyState("No tasks extracted from email content yet.");
  }
  return `
    <div class="sx-feed">
      ${tasks.map((task) => `
        <article class="sx-feed-item">
          <div class="sx-feed-head">
            <strong>${escapeHtml(task.title)}</strong>
            <span class="sx-chip">${escapeHtml(task.due_hint)}</span>
          </div>
          <p>${escapeHtml(task.rationale)}</p>
        </article>
      `).join("")}
    </div>
  `;
}

function replyLog(items) {
  if (!items?.length) {
    return emptyState("No simulated replies have been sent yet.");
  }
  return `
    <div class="sx-feed">
      ${items.map((item) => `
        <article class="sx-feed-item">
          <div class="sx-feed-head">
            <strong>${escapeHtml(item.subject)}</strong>
            <span class="sx-chip">${escapeHtml(item.status)}</span>
          </div>
          <div class="sx-feed-meta">
            <span>${escapeHtml(item.recipient)}</span>
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function mailList(items, activeId) {
  if (!items?.length) {
    return emptyState(`No emails are currently in the ${state.activeLane} lane.`);
  }
  return `
    <div class="sx-mail-list">
      ${items.map((item) => `
        <button class="sx-mail-item ${item.email_id === activeId ? "is-active" : ""}" type="button" data-open-email="${escapeHtml(item.email_id)}">
          <div class="sx-mail-head">
            <strong>${escapeHtml(item.subject)}</strong>
            <span class="sx-chip">${escapeHtml(item.label)}</span>
          </div>
          <div class="sx-feed-meta">
            <span>${escapeHtml(item.sender)}</span>
            <span>${escapeHtml(item.received_at)}</span>
          </div>
          <p>${escapeHtml(item.preview)}</p>
          <div class="sx-feed-meta">
            <span>${escapeHtml(item.priority)} | ${escapeHtml(item.folder)}</span>
            <span>${item.processed ? "Processed" : "Current"} | ${escapeHtml(item.action)}</span>
          </div>
        </button>
      `).join("")}
    </div>
  `;
}

function optionButtons(setting, options, activeValue) {
  return `
    <div class="sx-option-wrap">
      ${options.map((option) => `
        <button class="sx-option ${option.value === activeValue ? "is-active" : ""}" type="button" data-setting="${escapeHtml(setting)}" data-value="${escapeHtml(option.value)}">
          <span>${escapeHtml(option.label)}</span>
          <small>${escapeHtml(option.note)}</small>
        </button>
      `).join("")}
    </div>
  `;
}

function paletteButtons(activeValue) {
  const options = [
    { value: "teal", label: "Teal Calm", note: "Balanced and focused" },
    { value: "sunset", label: "Sunset Glow", note: "Warm and energetic" },
    { value: "ocean", label: "Ocean Blue", note: "Cool and crisp" },
    { value: "forest", label: "Forest Focus", note: "Grounded and calm" },
    { value: "rose", label: "Rose Pulse", note: "Bold and expressive" },
  ];
  return `
    <div class="sx-palette-grid">
      ${options.map((option) => `
        <button class="sx-palette ${option.value === activeValue ? "is-active" : ""}" type="button" data-setting="colorTheme" data-value="${escapeHtml(option.value)}">
          <span class="sx-swatch sx-swatch-${escapeHtml(option.value)}"></span>
          <span>
            <strong>${escapeHtml(option.label)}</strong>
            <small>${escapeHtml(option.note)}</small>
          </span>
        </button>
      `).join("")}
    </div>
  `;
}
function shellMarkup() {
  const page = pageConfig();
  const email = currentEmail();
  const analysis = currentAnalysis();
  const analyticsData = analytics();
  const inbox = smartInbox();
  const activeItems = inbox[state.activeLane] || [];
  const themeLabel = resolvedTheme() === "dark" ? "Dark" : "Light";
  const themeModeLabel = state.settings.theme === "system" ? "System" : "Manual";

  return `
    <div class="sx-app">
      <header class="sx-topbar">
        <a class="sx-brand" href="/">
          <span class="sx-brand-mark">SX</span>
          <span class="sx-brand-copy">
            <small>Synaptrix OpenEnv Workspace</small>
            <strong>Synaptrix MailOS</strong>
          </span>
        </a>
        <nav class="sx-nav">
          ${Object.entries(PAGES)
            .filter(([key]) => key !== "settings")
            .map(([key, item]) => `
              <a class="sx-nav-link ${key === state.page ? "is-active" : ""}" href="${item.path}">
                ${escapeHtml(item.label)}
              </a>
            `)
            .join("")}
        </nav>
        <div class="sx-top-actions">
          <button class="sx-theme-toggle ${resolvedTheme() === "dark" ? "is-dark" : ""}" id="theme-toggle" type="button" aria-label="Toggle theme" aria-pressed="${resolvedTheme() === "dark"}">
            <span class="sx-theme-track"><span class="sx-theme-thumb"></span></span>
            <span class="sx-theme-copy">
              <small>${escapeHtml(themeModeLabel)}</small>
              <strong>${escapeHtml(themeLabel)} Mode</strong>
            </span>
          </button>
          <a class="sx-settings-link ${state.page === "settings" ? "is-active" : ""}" href="${pagePath("settings")}">Settings</a>
        </div>
      </header>

      <div class="sx-shell">
        <aside class="sx-sidebar">
          <section class="sx-card sx-current-card">
            <div class="sx-card-head">
              <div>
                <p class="sx-kicker">Current Email</p>
                <h2>${escapeHtml(email?.subject || "Loading email...")}</h2>
              </div>
              <span class="sx-chip">${escapeHtml(sourceFor(email))}</span>
            </div>
            <p class="sx-detail-line">From ${escapeHtml(email?.sender || "Waiting for email data")}</p>
            <div class="sx-chip-row">
              ${chip(`Label ${labelFor(email)}`)}
              ${chip(`Folder ${folderFor(email)}`)}
              ${analysis ? chip(`Lane ${analysis.automation.inbox_lane}`) : chip(`Lane ${state.activeLane}`)}
            </div>
            <p class="sx-preview">${escapeHtml(previewFor(email) || "The message preview will appear here once the email is loaded.")}</p>
            ${scoreRows([
              { label: "Priority", value: analysis?.risk.priority || "Waiting" },
              { label: "Decision", value: analysis?.decision.action || "Waiting" },
              { label: "Response SLA", value: analysis?.decision.response_window || "Waiting" },
            ])}
          </section>

          <section class="sx-card">
            <div class="sx-card-head">
              <div>
                <p class="sx-kicker">Action Center</p>
                <h3>Run Email Workflow</h3>
              </div>
              <button class="sx-btn sx-btn-ghost" id="next-btn" type="button" ${state.loading ? "disabled" : ""}>Next Email</button>
            </div>
            <div class="sx-action-grid">
              <button class="sx-btn sx-btn-primary" id="analyze-btn" type="button" ${state.loading ? "disabled" : ""}>Analyze Email</button>
              <button class="sx-btn sx-btn-secondary" id="auto-btn" type="button" ${state.loading ? "disabled" : ""}>Apply AI Decision</button>
              <button class="sx-btn sx-btn-ghost" type="button" data-action="Ignore" ${state.loading ? "disabled" : ""}>Ignore</button>
              <button class="sx-btn sx-btn-ghost" type="button" data-action="Respond" ${state.loading ? "disabled" : ""}>Respond</button>
              <button class="sx-btn sx-btn-ghost" type="button" data-action="Urgent Action" ${state.loading ? "disabled" : ""}>Urgent Action</button>
              <a class="sx-btn sx-btn-link" href="${pagePath("composer")}">Open Composer</a>
            </div>
            <p class="sx-note">${escapeHtml(state.loading ? "Synaptrix is processing the current email..." : analyticsData.last_event || "System ready.")}</p>
          </section>

          <section class="sx-card">
            <div class="sx-card-head">
              <div>
                <p class="sx-kicker">Smart Inbox</p>
                <h3>Lane Queue</h3>
              </div>
            </div>
            <div class="sx-lane-tabs">
              ${["Urgent", "Important", "Others"].map((lane) => `
                <button class="sx-lane-btn ${lane === state.activeLane ? "is-active" : ""}" type="button" data-lane="${lane}">
                  <span>${lane}</span>
                  <strong>${escapeHtml((inbox[lane] || []).length)}</strong>
                </button>
              `).join("")}
            </div>
            ${mailList(activeItems, email?.email_id)}
          </section>

          <section class="sx-card">
            <div class="sx-card-head">
              <div>
                <p class="sx-kicker">Live Alerts</p>
                <h3>Notification Snapshot</h3>
              </div>
            </div>
            ${alertList(topAlerts(analyticsData.notifications || []), "No active alerts. The notification feed will light up when action is needed.")}
          </section>
        </aside>

        <main class="sx-main">
          <section class="sx-page-hero">
            <div>
              <p class="sx-kicker">Synaptrix Workspace</p>
              <h1>${escapeHtml(page.title)}</h1>
              <p>${escapeHtml(page.description)}</p>
            </div>
          </section>

          ${state.error ? `<div class="sx-banner sx-banner-error">${escapeHtml(state.error)}</div>` : ""}

          <section class="sx-metrics-row">
            ${metricCard("Emails Handled Today", numberOrZero(analyticsData.emails_handled_today), "Realtime processing volume")}
            ${metricCard("Urgent Rate", percent(analyticsData.urgent_rate), "Share of urgent detections")}
            ${metricCard("Spam Rate", percent(analyticsData.spam_rate), "Messages routed as spam")}
            ${metricCard("Average Reward", numberOrZero(analyticsData.average_reward), "Environment performance score")}
          </section>

          <section class="sx-banner">
            ${escapeHtml(analyticsData.last_event || "System ready. Analyze an email to activate the multi-agent flow.")}
          </section>

          ${renderPageBody()}
        </main>
      </div>
    </div>
  `;
}

function renderSummaryPage(email, analysis) {
  if (!analysis) {
    return `
      <section class="sx-grid sx-grid-2">
        <article class="sx-panel sx-span-2">${emptyState("Analyze the current email to unlock the decision summary, risk scoring, and reply guidance.")}</article>
      </section>
    `;
  }

  return `
    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Decision Brief</p>
        <h3>${escapeHtml(analysis.decision.action)}</h3>
        <p>${escapeHtml(analysis.decision.rationale)}</p>
        ${scoreRows([
          { label: "Category", value: analysis.classification.category },
          { label: "Priority", value: analysis.risk.priority },
          { label: "Risk Level", value: analysis.risk.risk_level },
          { label: "Response SLA", value: analysis.decision.response_window },
          { label: "Confidence", value: `${analysis.decision.confidence_score}%` },
        ])}
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Risk And Tone</p>
        <h3>${escapeHtml(analysis.risk.priority)} Priority</h3>
        <p>${escapeHtml(analysis.risk.rationale)}</p>
        ${scoreRows([
          { label: "Importance Score", value: analysis.risk.importance_score },
          { label: "Urgency Score", value: analysis.risk.urgency_score },
          { label: "Spam Risk Score", value: analysis.risk.spam_risk_score },
          { label: "Tone", value: analysis.risk.tone },
        ])}
      </article>

      <article class="sx-panel sx-span-2">
        <div class="sx-card-head">
          <div>
            <p class="sx-kicker">Full Message</p>
            <h3>${escapeHtml(email?.subject || "Current Email")}</h3>
          </div>
          <span class="sx-chip">${escapeHtml(email?.received_at || "Live")}</span>
        </div>
        <div class="sx-message-body">${escapeHtml(email?.body || "")}</div>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Reply Guidance</p>
        <h3>${escapeHtml(analysis.decision.draft_subject)}</h3>
        <pre class="sx-pre">${escapeHtml(analysis.decision.draft_body)}</pre>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Threat Indicators</p>
        <h3>Security And Risk Flags</h3>
        ${alertList(analysis.risk.threat_indicators, "No threat indicators were detected for the current email.")}
      </article>
    </section>
  `;
}

function renderAutomationPage(analysis, analyticsData) {
  if (!analysis) {
    return `
      <section class="sx-grid sx-grid-2">
        <article class="sx-panel sx-span-2">${emptyState("Run analysis to see labels, folder routing, lane placement, and automation actions.")}</article>
      </section>
    `;
  }

  return `
    <section class="sx-grid sx-grid-4">
      <article class="sx-panel">${scoreRows([{ label: "Label Applied", value: analysis.automation.applied_label }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Folder Route", value: analysis.automation.destination_folder }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Inbox Lane", value: analysis.automation.inbox_lane }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Highlight State", value: analysis.automation.highlight }])}</article>
    </section>

    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Automation Narrative</p>
        <h3>Why Synaptrix Routed It This Way</h3>
        <p>${escapeHtml(analysis.automation.rationale)}</p>
        <div class="sx-chip-row">
          ${analysis.automation.auto_actions.map((item) => chip(item)).join("")}
        </div>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Routing Flow</p>
        <h3>Mailbox Progression</h3>
        <div class="sx-timeline">
          <article class="sx-step"><span>1</span><div><strong>Classify</strong><small>${escapeHtml(analysis.classification.category)}</small></div></article>
          <article class="sx-step"><span>2</span><div><strong>Label</strong><small>${escapeHtml(analysis.automation.applied_label)}</small></div></article>
          <article class="sx-step"><span>3</span><div><strong>Route</strong><small>${escapeHtml(analysis.automation.destination_folder)}</small></div></article>
          <article class="sx-step"><span>4</span><div><strong>Prioritize</strong><small>${escapeHtml(analysis.automation.inbox_lane)}</small></div></article>
        </div>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Notification System</p>
        <h3>Triggered Alerts</h3>
        ${alertList(analyticsData.notifications, "No alerts are active for the current mailbox state.")}
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Mailbox Snapshot</p>
        <h3>Automation State</h3>
        ${scoreRows([
          { label: "Decision", value: analysis.decision.action },
          { label: "Priority", value: analysis.risk.priority },
          { label: "Response Window", value: analysis.decision.response_window },
          { label: "Reward Ready", value: "Environment synced" },
        ])}
      </article>
    </section>
  `;
}

function renderTasksPage(analysis, analyticsData) {
  return `
    <section class="sx-grid sx-grid-3">
      <article class="sx-panel">
        <p class="sx-kicker">Task Generator</p>
        <h3>${escapeHtml(numberOrZero(analyticsData.tasks_created))}</h3>
        <p>Tasks extracted from meetings, deadlines, and commitments mentioned inside emails.</p>
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Action Required</p>
        <h3>${escapeHtml(numberOrZero((analyticsData.notifications || []).length))}</h3>
        <p>Notification prompts currently active in the workspace.</p>
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Current Decision</p>
        <h3>${escapeHtml(analysis?.decision.action || "Waiting")}</h3>
        <p>${escapeHtml(analysis?.decision.rationale || "Analyze an email to generate action logic.")}</p>
      </article>
    </section>

    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Generated Tasks</p>
        <h3>Smart Task Queue</h3>
        ${taskList(analyticsData.tasks || [])}
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Notification Feed</p>
        <h3>Productivity Alerts</h3>
        ${alertList(analyticsData.notifications, "No productivity alerts yet.")}
      </article>

      <article class="sx-panel sx-span-2">
        <p class="sx-kicker">Decision Mix</p>
        <h3>Action Distribution</h3>
        ${barChart(analyticsData.action_distribution, "Action distribution appears after decisions are processed.")}
      </article>
    </section>
  `;
}
function renderReplyPage(analysis, analyticsData) {
  if (!analysis) {
    return `
      <section class="sx-grid sx-grid-2">
        <article class="sx-panel sx-span-2">${emptyState("Analyze the current email to generate a reply subject, draft, and response guidance.")}</article>
      </section>
    `;
  }

  return `
    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <div class="sx-card-head">
          <div>
            <p class="sx-kicker">Auto Reply System</p>
            <h3>${escapeHtml(analysis.decision.draft_subject)}</h3>
          </div>
          <button class="sx-btn sx-btn-primary" id="send-reply-btn" type="button" ${state.loading ? "disabled" : ""}>Send Reply</button>
        </div>
        <pre class="sx-pre">${escapeHtml(analysis.decision.draft_body)}</pre>
        <p class="sx-note">${escapeHtml(state.replyStatus)}</p>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Response Guidance</p>
        <h3>Recommended Handling</h3>
        <p>${escapeHtml(analysis.decision.reply_suggestion)}</p>
        ${scoreRows([
          { label: "Decision", value: analysis.decision.action },
          { label: "Tone", value: analysis.risk.tone },
          { label: "Response Window", value: analysis.decision.response_window },
          { label: "Priority", value: analysis.risk.priority },
        ])}
      </article>

      <article class="sx-panel sx-span-2">
        <p class="sx-kicker">Recent Reply Activity</p>
        <h3>Reply Log</h3>
        ${replyLog(analyticsData.recent_replies || [])}
      </article>
    </section>
  `;
}

function renderAnalyticsPage(analyticsData) {
  return `
    <section class="sx-grid sx-grid-3">
      <article class="sx-panel">
        <p class="sx-kicker">Total Processed</p>
        <h3>${escapeHtml(numberOrZero(analyticsData.total_processed))}</h3>
        <p>Total emails processed by the environment.</p>
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Success Rate</p>
        <h3>${escapeHtml(percent(analyticsData.success_rate))}</h3>
        <p>How often the environment earned a successful reward outcome.</p>
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Auto Replies</p>
        <h3>${escapeHtml(numberOrZero(analyticsData.auto_replies_sent))}</h3>
        <p>Simulated reply sends completed through Reply Studio.</p>
      </article>
    </section>

    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Category Distribution</p>
        <h3>Email Types</h3>
        ${barChart(analyticsData.category_distribution, "Category distribution will appear after processing emails.")}
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Risk Distribution</p>
        <h3>Risk Levels</h3>
        ${barChart(analyticsData.risk_distribution, "Risk distribution will appear after processing emails.")}
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Inbox Lanes</p>
        <h3>Smart Inbox Organizer</h3>
        ${barChart(analyticsData.lane_distribution, "Lane counts appear after the automation system routes emails.")}
      </article>
      <article class="sx-panel">
        <p class="sx-kicker">Folder Routing</p>
        <h3>Mailbox Flow</h3>
        ${barChart(analyticsData.folder_distribution, "Folder routing appears after automation moves emails.")}
      </article>
      <article class="sx-panel sx-span-2">
        <p class="sx-kicker">Reward Trend</p>
        <h3>OpenEnv Reward Tracking</h3>
        ${rewardChart(analyticsData.reward_trend || [])}
      </article>
    </section>
  `;
}

function renderHistoryPage() {
  return `
    <section class="sx-grid sx-grid-1">
      <article class="sx-panel">
        <p class="sx-kicker">Email History Tracking</p>
        <h3>Decision Timeline</h3>
        ${historyList(historyRecords())}
      </article>
    </section>
  `;
}

function renderHealthPage(analysis) {
  if (!analysis) {
    return `
      <section class="sx-grid sx-grid-2">
        <article class="sx-panel sx-span-2">${emptyState("Analyze the current email to inspect confidence, threats, and health signals.")}</article>
      </section>
    `;
  }

  return `
    <section class="sx-grid sx-grid-4">
      <article class="sx-panel">${scoreRows([{ label: "Classification Confidence", value: `${Math.round((analysis.classification.confidence || 0) * 100)}%` }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Decision Confidence", value: `${analysis.decision.confidence_score}%` }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Response Window", value: analysis.decision.response_window }])}</article>
      <article class="sx-panel">${scoreRows([{ label: "Risk Level", value: analysis.risk.risk_level }])}</article>
    </section>

    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Threat Indicator Feed</p>
        <h3>Security Signals</h3>
        ${alertList(analysis.risk.threat_indicators, "No threat indicators detected.")}
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Decision Integrity</p>
        <h3>Agent Health Snapshot</h3>
        ${scoreRows([
          { label: "Category", value: analysis.classification.category },
          { label: "Priority", value: analysis.risk.priority },
          { label: "Tone", value: analysis.risk.tone },
          { label: "Suggested Action", value: analysis.decision.action },
        ])}
      </article>
    </section>
  `;
}

function renderComposerPage() {
  return `
    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Email Composer Sandbox</p>
        <h3>Load A Custom Email</h3>
        <form id="custom-email-form" class="sx-form">
          <label>
            <span>Sender</span>
            <input name="sender" type="text" placeholder="sender@example.com">
          </label>
          <label>
            <span>Subject</span>
            <input name="subject" type="text" placeholder="Project update or urgent request">
          </label>
          <label>
            <span>Body</span>
            <textarea name="body" rows="10" placeholder="Paste the full email body here"></textarea>
          </label>
          <button class="sx-btn sx-btn-primary" type="submit" ${state.loading ? "disabled" : ""}>Load And Analyze Email</button>
        </form>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">How It Works</p>
        <h3>Sandbox Flow</h3>
        <div class="sx-timeline">
          <article class="sx-step"><span>1</span><div><strong>Compose</strong><small>Paste a custom email into the sandbox.</small></div></article>
          <article class="sx-step"><span>2</span><div><strong>Analyze</strong><small>Classification, risk, and decision agents run automatically.</small></div></article>
          <article class="sx-step"><span>3</span><div><strong>Route</strong><small>Gmail simulation applies labels, folders, and inbox lanes.</small></div></article>
          <article class="sx-step"><span>4</span><div><strong>Act</strong><small>Open Automation, Reply, or Tasks based on your personal setting.</small></div></article>
        </div>
      </article>
    </section>
  `;
}

function renderSettingsPage() {
  return `
    <section class="sx-grid sx-grid-2">
      <article class="sx-panel">
        <p class="sx-kicker">Appearance</p>
        <h3>Theme And Vibe</h3>
        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Theme Mode</strong>
            <small>Use manual light or dark mode, or follow the system.</small>
          </div>
          ${optionButtons("theme", [
            { value: "system", label: "System", note: "Follow device preference" },
            { value: "light", label: "Light", note: "Bright workspace surfaces" },
            { value: "dark", label: "Dark", note: "Low-glare focus mode" },
          ], state.settings.theme)}
        </div>

        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Color Theme</strong>
            <small>Pick the background vibe that feels best for your team.</small>
          </div>
          ${paletteButtons(state.settings.colorTheme)}
        </div>

        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Surface Style</strong>
            <small>Choose how polished or grounded the workspace cards should feel.</small>
          </div>
          ${optionButtons("surface", [
            { value: "glass", label: "Glass", note: "Soft and layered" },
            { value: "paper", label: "Paper", note: "Warm and clean" },
            { value: "carbon", label: "Carbon", note: "Sharper and denser" },
          ], state.settings.surface)}
        </div>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Workflow</p>
        <h3>Behavior Preferences</h3>
        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>After Analyze Or Apply</strong>
            <small>Automatically land on the workspace you use most.</small>
          </div>
          ${optionButtons("focusPage", [
            { value: "summary", label: "Summary", note: "Stay in the decision overview" },
            { value: "automation", label: "Automation", note: "Jump to Gmail routing instantly" },
            { value: "tasks", label: "Tasks", note: "Review task extraction first" },
            { value: "reply", label: "Reply", note: "Open the response draft right away" },
          ], state.settings.focusPage)}
        </div>

        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Default Inbox Lane</strong>
            <small>Open the mailbox view on your preferred lane every time.</small>
          </div>
          ${optionButtons("defaultLane", [
            { value: "Urgent", label: "Urgent", note: "See critical mail first" },
            { value: "Important", label: "Important", note: "Focus on meaningful follow-up" },
            { value: "Others", label: "Others", note: "Start from the general queue" },
          ], state.settings.defaultLane)}
        </div>

        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Alert Density</strong>
            <small>Control how many live alerts appear in the sidebar snapshot.</small>
          </div>
          ${optionButtons("alertMode", [
            { value: "quiet", label: "Quiet", note: "Only the top alert" },
            { value: "balanced", label: "Balanced", note: "A small live snapshot" },
            { value: "watchtower", label: "Watchtower", note: "Show a broader alert view" },
          ], state.settings.alertMode)}
        </div>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Comfort</p>
        <h3>Readability Controls</h3>
        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Inbox Density</strong>
            <small>Switch between roomy cards and compact scanning.</small>
          </div>
          ${optionButtons("density", [
            { value: "cozy", label: "Cozy", note: "More space, more breathing room" },
            { value: "compact", label: "Compact", note: "Tighter layout for dense work" },
          ], state.settings.density)}
        </div>

        <div class="sx-setting-group">
          <div class="sx-setting-head">
            <strong>Motion Style</strong>
            <small>Tone down transitions if you want a calmer interface.</small>
          </div>
          ${optionButtons("motion", [
            { value: "rich", label: "Rich", note: "Full transitions and hover polish" },
            { value: "minimal", label: "Minimal", note: "Reduced motion and simpler feedback" },
          ], state.settings.motion)}
        </div>

        <button class="sx-btn sx-btn-secondary" id="reset-settings" type="button">Reset Personalization</button>
      </article>

      <article class="sx-panel">
        <p class="sx-kicker">Live Preview</p>
        <h3>Your Synaptrix Profile</h3>
        <div class="sx-preview-box">
          <div class="sx-preview-head">
            <strong>${escapeHtml(resolvedTheme() === "dark" ? "Dark" : "Light")} ${escapeHtml(state.settings.surface)}</strong>
            <span class="sx-chip">${escapeHtml(state.settings.colorTheme)}</span>
          </div>
          <p>After analysis, Synaptrix will open <strong>${escapeHtml(state.settings.focusPage)}</strong> and start the mailbox on the <strong>${escapeHtml(state.settings.defaultLane)}</strong> lane.</p>
          <div class="sx-chip-row">
            ${chip(`Alert ${state.settings.alertMode}`)}
            ${chip(`Density ${state.settings.density}`)}
            ${chip(`Motion ${state.settings.motion}`)}
          </div>
        </div>
      </article>
    </section>
  `;
}

function renderPageBody() {
  const analysis = currentAnalysis();
  const analyticsData = analytics();
  const email = currentEmail();

  if (state.page === "automation") {
    return renderAutomationPage(analysis, analyticsData);
  }
  if (state.page === "tasks") {
    return renderTasksPage(analysis, analyticsData);
  }
  if (state.page === "reply") {
    return renderReplyPage(analysis, analyticsData);
  }
  if (state.page === "analytics") {
    return renderAnalyticsPage(analyticsData);
  }
  if (state.page === "history") {
    return renderHistoryPage();
  }
  if (state.page === "health") {
    return renderHealthPage(analysis);
  }
  if (state.page === "composer") {
    return renderComposerPage();
  }
  if (state.page === "settings") {
    return renderSettingsPage();
  }
  return renderSummaryPage(email, analysis);
}

function render() {
  const root = document.getElementById("app-root");
  if (!root) {
    return;
  }
  document.title = `Synaptrix MailOS - ${pageConfig().title}`;
  root.innerHTML = shellMarkup();
  bindEvents();
}

function bindEvents() {
  document.getElementById("theme-toggle")?.addEventListener("click", toggleTheme);
  document.getElementById("analyze-btn")?.addEventListener("click", () => analyzeCurrent(true));
  document.getElementById("auto-btn")?.addEventListener("click", () => processAction(null, true));
  document.getElementById("next-btn")?.addEventListener("click", () => resetEmail({}, true));
  document.getElementById("send-reply-btn")?.addEventListener("click", sendReply);
  document.getElementById("reset-settings")?.addEventListener("click", resetSettings);

  document.querySelectorAll("[data-lane]").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeLane = button.dataset.lane;
      render();
    });
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => processAction(button.dataset.action, false));
  });

  document.querySelectorAll("[data-open-email]").forEach((button) => {
    button.addEventListener("click", () => openEmail(button.dataset.openEmail));
  });

  document.querySelectorAll("[data-setting]").forEach((button) => {
    button.addEventListener("click", () => updateSetting(button.dataset.setting, button.dataset.value));
  });

  document.getElementById("custom-email-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    await resetEmail({
      sender: formData.get("sender"),
      subject: formData.get("subject"),
      body: formData.get("body"),
    }, true, true);
    event.currentTarget.reset();
  });
}

function navigateToFocusPage() {
  if (state.settings.focusPage !== state.page && PAGES[state.settings.focusPage]) {
    window.location.assign(pagePath(state.settings.focusPage));
    return true;
  }
  return false;
}

async function loadState() {
  loadSettings();
  applyPreferences();
  render();
  try {
    const snapshot = await api("/api/state");
    state.snapshot = snapshot;
    state.error = "";
    state.replyStatus = "No simulated reply sent yet.";
    updateLaneFromSnapshot(snapshot);
    render();
    if (!snapshot.current_analysis) {
      await analyzeCurrent(false);
    }
  } catch (error) {
    state.error = error.message;
    render();
  }
}

async function analyzeCurrent(navigateAfter = true) {
  state.loading = true;
  render();
  try {
    const response = await api("/api/analyze", {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.snapshot = response.snapshot;
    state.error = "";
    state.replyStatus = "Draft refreshed from the latest analysis.";
    updateLaneFromSnapshot(response.snapshot);
    state.loading = false;
    if (navigateAfter && navigateToFocusPage()) {
      return;
    }
    render();
  } catch (error) {
    state.loading = false;
    state.error = error.message;
    render();
  }
}

async function processAction(action = null, useRecommended = false) {
  state.loading = true;
  render();
  try {
    const response = await api("/api/step", {
      method: "POST",
      body: JSON.stringify({ action, use_recommended: useRecommended }),
    });
    state.snapshot = response.snapshot;
    state.error = "";
    updateLaneFromSnapshot(response.snapshot);
    state.loading = false;
    if (navigateToFocusPage()) {
      return;
    }
    render();
  } catch (error) {
    state.loading = false;
    state.error = error.message;
    render();
  }
}

async function resetEmail(payload = {}, autoAnalyze = true, navigateAfter = false) {
  state.loading = true;
  render();
  try {
    const snapshot = await api("/api/reset", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.snapshot = snapshot;
    state.error = "";
    state.replyStatus = "No simulated reply sent yet.";
    state.activeLane = state.settings.defaultLane;

    if (autoAnalyze) {
      const analysisResponse = await api("/api/analyze", {
        method: "POST",
        body: JSON.stringify({}),
      });
      state.snapshot = analysisResponse.snapshot;
      updateLaneFromSnapshot(analysisResponse.snapshot);
    }

    state.loading = false;
    if (navigateAfter && navigateToFocusPage()) {
      return;
    }
    render();
  } catch (error) {
    state.loading = false;
    state.error = error.message;
    render();
  }
}

async function openEmail(emailId) {
  state.loading = true;
  render();
  try {
    const snapshot = await api("/api/open-email", {
      method: "POST",
      body: JSON.stringify({ email_id: emailId }),
    });
    state.snapshot = snapshot;
    state.error = "";
    updateLaneFromSnapshot(snapshot);
    state.loading = false;
    render();
  } catch (error) {
    state.loading = false;
    state.error = error.message;
    render();
  }
}

async function sendReply() {
  state.loading = true;
  render();
  try {
    const response = await api("/api/send-reply", {
      method: "POST",
      body: JSON.stringify({}),
    });
    state.snapshot = response.snapshot;
    state.replyStatus = response.message;
    state.error = "";
    state.loading = false;
    render();
  } catch (error) {
    state.loading = false;
    state.error = error.message;
    render();
  }
}

const themeQuery = window.matchMedia("(prefers-color-scheme: dark)");
if (themeQuery?.addEventListener) {
  themeQuery.addEventListener("change", () => {
    if (state.settings.theme === "system") {
      applyPreferences();
      render();
    }
  });
}

loadState().catch((error) => {
  state.error = error.message;
  render();
});


