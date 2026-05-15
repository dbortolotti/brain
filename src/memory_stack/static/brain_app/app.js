const state = {
  previewArgs: null,
  token: localStorage.getItem("brainBearerToken") || "",
};

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const status = $("status");
  status.textContent = message || "";
  status.classList.toggle("error", isError);
}

function tokenHeader() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function mcpCall(name, args = {}) {
  const response = await fetch("/app/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...tokenHeader(),
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method: "tools/call",
      params: { name, arguments: args },
    }),
  });
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error?.message || payload.detail?.error || `HTTP ${response.status}`);
  }
  return payload.result.structuredContent;
}

function renderList(target, rows, emptyText, formatter) {
  target.innerHTML = "";
  if (!rows || rows.length === 0) {
    target.innerHTML = `<div class="item"><div class="item-meta">${emptyText}</div></div>`;
    return;
  }
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "item";
    item.innerHTML = formatter(row);
    target.appendChild(item);
  });
}

function safe(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function refreshReview() {
  setStatus("Loading recent memory...");
  const [session, recent, loops] = await Promise.all([
    mcpCall("brain_session"),
    mcpCall("brain_review_recent", { limit: 12, include_sources: true }),
    mcpCall("brain_list_open_loops", { limit: 12 }),
  ]);
  $("sessionLine").textContent = `${session.profile_full_name || session.profile_name} - ${session.session_id}`;
  renderList($("recentCards"), recent.memory_cards, "No recent cards.", (card) => {
    const title = card.summary || card.content || card.id;
    return `<div class="item-title">${safe(title)}</div><div class="item-meta">${safe(card.kind || card.memory_kind || "memory")} - ${safe(card.id)}</div>`;
  });
  renderList($("openLoops"), loops.open_loops, "No open loops.", (loop) => {
    const title = loop.question || loop.summary || loop.content || loop.id;
    return `<div class="item-title">${safe(title)}</div><div class="item-meta">${safe(loop.status || "open")} - ${safe(loop.id)}</div>`;
  });
  setStatus("Review loaded.");
}

async function refreshProfile() {
  setStatus("Loading profile context...");
  const payload = await mcpCall("brain_profile_context_list");
  renderList($("profileItems"), payload.profile_context, "No profile context.", (item) => {
    return `<div class="item-title">${safe(item.statement)}</div><div class="item-meta">${safe(item.scope)} - ${safe(item.id)}</div><button class="danger" type="button" data-forget="${safe(item.id)}">Forget</button>`;
  });
  setStatus("Profile context loaded.");
}

function showTab(tabName) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabName);
  });
}

function wireEvents() {
  $("tokenInput").value = state.token;
  $("saveToken").addEventListener("click", async () => {
    state.token = $("tokenInput").value.trim();
    localStorage.setItem("brainBearerToken", state.token);
    await refreshReview().catch((error) => setStatus(error.message, true));
  });
  $("clearToken").addEventListener("click", () => {
    state.token = "";
    localStorage.removeItem("brainBearerToken");
    $("tokenInput").value = "";
    setStatus("Token cleared.");
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => showTab(tab.dataset.tab));
  });
  $("refreshReview").addEventListener("click", () => refreshReview().catch((error) => setStatus(error.message, true)));
  $("refreshProfile").addEventListener("click", () => refreshProfile().catch((error) => setStatus(error.message, true)));
  $("recallForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setStatus("Searching...");
    const payload = await mcpCall("brain_recall", {
      query: $("recallQuery").value,
      limit: Number($("recallLimit").value || 10),
    }).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    if (payload) {
      $("recallResult").textContent = payload.answer || JSON.stringify(payload, null, 2);
      setStatus("Recall complete.");
    }
  });
  $("rememberForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setStatus("Preparing preview...");
    state.previewArgs = {
      input: $("rememberInput").value,
      input_type: $("rememberType").value,
      context: { source: "brain_app_ui" },
    };
    const payload = await mcpCall("brain_remember", state.previewArgs).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    if (payload) {
      $("rememberPreview").textContent = JSON.stringify(payload, null, 2);
      $("confirmRemember").classList.remove("hidden");
      setStatus("Preview ready. Confirm before saving.");
    }
  });
  $("confirmRemember").addEventListener("click", async () => {
    if (!state.previewArgs) return;
    setStatus("Saving confirmed memory...");
    const payload = await mcpCall("brain_remember", {
      ...state.previewArgs,
      dry_run: false,
      context: {
        ...(state.previewArgs.context || {}),
        confirmed_by_user: true,
      },
    }).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    if (payload) {
      $("rememberPreview").textContent = JSON.stringify(payload, null, 2);
      $("confirmRemember").classList.add("hidden");
      setStatus("Memory saved.");
      refreshReview().catch(() => {});
    }
  });
  $("profileForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setStatus("Adding profile context...");
    await mcpCall("brain_profile_context_remember", {
      statement: $("profileStatement").value,
      scope: $("profileScope").value || "answer_tailoring",
      source: "brain_app_ui",
    }).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    $("profileStatement").value = "";
    await refreshProfile().catch((error) => setStatus(error.message, true));
  });
  $("profileItems").addEventListener("click", async (event) => {
    const id = event.target?.dataset?.forget;
    if (!id) return;
    setStatus("Removing profile context...");
    await mcpCall("brain_profile_context_forget", { context_id: id }).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    await refreshProfile().catch((error) => setStatus(error.message, true));
  });
}

wireEvents();
if (state.token) {
  refreshReview().catch((error) => setStatus(error.message, true));
} else {
  setStatus("Enter a Brain bearer token to load memory.");
}
