const state = {
  previewArgs: null,
  latestSession: null,
  token: localStorage.getItem("brainBearerToken") || "",
};
const OAUTH_STORAGE_KEY = "brainOAuthPkce";

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const status = $("status");
  status.textContent = message || "";
  status.classList.toggle("error", isError);
}

function tokenHeader() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

function randomBase64Url(bytes = 32) {
  const data = new Uint8Array(bytes);
  crypto.getRandomValues(data);
  return base64UrlEncode(data);
}

function base64UrlEncode(data) {
  const binary = Array.from(data, (byte) => String.fromCharCode(byte)).join("");
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

async function sha256Base64Url(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return base64UrlEncode(new Uint8Array(digest));
}

async function startOAuth() {
  setStatus("Starting Brain authorization...");
  const redirectUri = `${window.location.origin}/app/oauth/callback`;
  const clientResponse = await fetch("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_name: "Brain Dashboard",
      redirect_uris: [redirectUri],
      token_endpoint_auth_method: "none",
      grant_types: ["authorization_code", "refresh_token"],
      response_types: ["code"],
      scope: "brain.memory.read brain.memory.write",
    }),
  });
  const client = await clientResponse.json();
  if (!clientResponse.ok) {
    throw new Error(client.error_description || client.detail || `Registration failed: HTTP ${clientResponse.status}`);
  }
  const verifier = randomBase64Url(48);
  const oauthState = randomBase64Url(24);
  sessionStorage.setItem(
    OAUTH_STORAGE_KEY,
    JSON.stringify({
      client_id: client.client_id,
      code_verifier: verifier,
      redirect_uri: redirectUri,
      state: oauthState,
    }),
  );
  const params = new URLSearchParams({
    response_type: "code",
    client_id: client.client_id,
    redirect_uri: redirectUri,
    scope: "brain.memory.read brain.memory.write",
    state: oauthState,
    code_challenge: await sha256Base64Url(verifier),
    code_challenge_method: "S256",
  });
  window.location.assign(`/authorize?${params.toString()}`);
}

async function finishOAuthIfPresent() {
  const url = new URL(window.location.href);
  const code = url.searchParams.get("code");
  const returnedState = url.searchParams.get("state");
  if (!code) return false;

  const stored = JSON.parse(sessionStorage.getItem(OAUTH_STORAGE_KEY) || "{}");
  sessionStorage.removeItem(OAUTH_STORAGE_KEY);
  window.history.replaceState({}, document.title, "/app");
  if (!stored.client_id || !stored.code_verifier || stored.state !== returnedState) {
    throw new Error("OAuth state did not match. Start authorization again.");
  }

  setStatus("Completing Brain authorization...");
  const form = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: stored.client_id,
    code,
    redirect_uri: stored.redirect_uri,
    code_verifier: stored.code_verifier,
  });
  const tokenResponse = await fetch("/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  const token = await tokenResponse.json();
  if (!tokenResponse.ok) {
    throw new Error(token.error_description || token.error || `Token exchange failed: HTTP ${tokenResponse.status}`);
  }
  state.token = token.access_token;
  localStorage.setItem("brainBearerToken", state.token);
  $("tokenInput").value = state.token;
  setStatus("Brain authorized.");
  await refreshReview();
  return true;
}

async function mcpCall(name, args = {}) {
  const payload = await mcpRequest("tools/call", { name, arguments: args });
  return payload.result.structuredContent;
}

async function mcpPrompt(name, args = {}) {
  const payload = await mcpRequest("prompts/get", { name, arguments: args });
  return payload.result;
}

async function mcpRequest(method, params = {}) {
  const response = await fetch("/app/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...tokenHeader(),
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: Date.now(),
      method,
      params,
    }),
  });
  const payload = await response.json();
  if (!response.ok || payload.error) {
    throw new Error(payload.error?.message || payload.detail?.error || `HTTP ${response.status}`);
  }
  return payload;
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
  state.latestSession = session;
  $("sessionLine").textContent = `${session.profile_full_name || session.profile_name} - ${session.session_id}`;
  renderMemoryCards(recent.memory_cards);
  renderList($("openLoops"), loops.open_loops, "No open loops.", (loop) => {
    const title = loop.question || loop.summary || loop.content || loop.id;
    return `<div class="item-title">${safe(title)}</div><div class="item-meta">${safe(loop.status || "open")} - ${safe(loop.id)}</div>`;
  });
  setStatus("Review loaded.");
}

function renderMemoryCards(cards) {
  const target = $("recentCards");
  target.innerHTML = "";
  if (!cards || cards.length === 0) {
    target.innerHTML = '<div class="item"><div class="item-meta">No recent cards.</div></div>';
    return;
  }
  cards.forEach((card) => {
    const title = card.summary || card.content || card.statement || card.id;
    const item = document.createElement("button");
    item.className = "item memory-card";
    item.type = "button";
    item.dataset.memoryId = card.id;
    item.innerHTML = `<span class="item-title">${safe(title)}</span><span class="item-meta">${safe(card.kind || card.memory_kind || "memory")} - ${safe(card.id)}</span>`;
    target.appendChild(item);
  });
}

async function showMemoryDetails(memoryId) {
  if (!memoryId) return;
  setStatus("Loading memory contents...");
  const payload = await mcpCall("brain_get_memory", { memory_id: memoryId });
  $("memoryDetails").textContent = JSON.stringify(payload.memory, null, 2);
  setStatus("Memory loaded.");
}

async function refreshProfile() {
  setStatus("Loading profile context...");
  const payload = await mcpCall("brain_profile_context_list");
  renderEditableProfileItems(
    $("profileItems"),
    payload.profile_context.filter((item) => item.scope !== "brain_preprompt"),
    "No personal info.",
  );
  setStatus("Profile context loaded.");
}

async function refreshPrompt() {
  setStatus("Loading Brain prompt data...");
  const session = await mcpCall("brain_session");
  state.latestSession = session;
  $("sessionLine").textContent = `${session.profile_full_name || session.profile_name} - ${session.session_id}`;
  $("sessionData").textContent = JSON.stringify(session, null, 2);

  const [profileContext, biasPrompt, agentPrompt] = await Promise.all([
    mcpCall("brain_profile_context_list"),
    mcpPrompt("brain_bias_protocol", { profile_name: session.profile_name }),
    mcpPrompt("brain_agent_memory_protocol", { session_id: session.session_id }),
  ]);
  const records = profileContext.profile_context || [];
  renderList(
    $("promptProfileItems"),
    records.filter((item) => item.scope !== "brain_preprompt"),
    "No personal info in session.",
    (item) => `<div class="item-title">${safe(item.statement)}</div><div class="item-meta">${safe(item.scope)} - ${safe(item.id)}</div>`,
  );
  renderEditableProfileItems(
    $("prepromptItems"),
    records.filter((item) => item.scope === "brain_preprompt"),
    "No custom preprompt instructions.",
  );
  $("biasPrompt").textContent = promptText(biasPrompt);
  $("agentPrompt").textContent = promptText(agentPrompt);
  setStatus("Brain prompt data loaded.");
}

function promptText(promptPayload) {
  return promptPayload?.messages?.[0]?.content?.text || JSON.stringify(promptPayload, null, 2);
}

function renderEditableProfileItems(target, rows, emptyText) {
  target.innerHTML = "";
  if (!rows || rows.length === 0) {
    target.innerHTML = `<div class="item"><div class="item-meta">${emptyText}</div></div>`;
    return;
  }
  rows.forEach((item) => {
    const wrapper = document.createElement("article");
    wrapper.className = "item edit-item";
    wrapper.dataset.contextId = item.id;
    wrapper.innerHTML = `
      <label>Statement</label>
      <textarea rows="3" data-field="statement">${safe(item.statement)}</textarea>
      <label>Scope</label>
      <input data-field="scope" value="${safe(item.scope || "answer_tailoring")}" />
      <div class="item-meta">${safe(item.id)}${item.memory_id ? ` - ${safe(item.memory_id)}` : ""}</div>
      <div class="form-row">
        <button type="button" data-action="save-profile">Save</button>
        <button class="danger" type="button" data-action="forget-profile">Forget</button>
      </div>
    `;
    target.appendChild(wrapper);
  });
}

async function saveProfileItem(container) {
  const oldId = container.dataset.contextId;
  const statement = container.querySelector('[data-field="statement"]').value;
  const scope = container.querySelector('[data-field="scope"]').value || "answer_tailoring";
  setStatus("Saving profile context...");
  const saved = await mcpCall("brain_profile_context_remember", {
    statement,
    scope,
    source: "brain_app_ui",
  });
  if (oldId && saved.id !== oldId) {
    await mcpCall("brain_profile_context_forget", { context_id: oldId });
  }
  await Promise.all([
    refreshProfile().catch(() => {}),
    refreshPrompt().catch(() => {}),
  ]);
  setStatus("Profile context saved.");
}

async function forgetProfileItem(container) {
  const id = container.dataset.contextId;
  if (!id) return;
  if (!window.confirm("Remove this profile context item from Brain?")) return;
  setStatus("Removing profile context...");
  await mcpCall("brain_profile_context_forget", {
    context_id: id,
    confirmed_by_user: true,
  });
  await Promise.all([
    refreshProfile().catch(() => {}),
    refreshPrompt().catch(() => {}),
  ]);
  setStatus("Profile context removed.");
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
  $("authorizeBrain").addEventListener("click", () => {
    startOAuth().catch((error) => setStatus(error.message, true));
  });
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
  $("refreshPrompt").addEventListener("click", () => refreshPrompt().catch((error) => setStatus(error.message, true)));
  $("recentCards").addEventListener("click", (event) => {
    const card = event.target.closest(".memory-card");
    if (!card) return;
    showMemoryDetails(card.dataset.memoryId).catch((error) => setStatus(error.message, true));
  });
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
    await Promise.all([
      refreshProfile().catch((error) => setStatus(error.message, true)),
      refreshPrompt().catch(() => {}),
    ]);
  });
  $("profileItems").addEventListener("click", (event) => {
    const action = event.target?.dataset?.action;
    const container = event.target.closest(".edit-item");
    if (!action || !container) return;
    const operation = action === "save-profile" ? saveProfileItem : forgetProfileItem;
    operation(container).catch((error) => setStatus(error.message, true));
  });
  $("prepromptForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    setStatus("Adding custom preprompt instruction...");
    await mcpCall("brain_profile_context_remember", {
      statement: $("prepromptStatement").value,
      scope: "brain_preprompt",
      source: "brain_app_ui",
    }).catch((error) => {
      setStatus(error.message, true);
      return null;
    });
    $("prepromptStatement").value = "";
    await refreshPrompt().catch((error) => setStatus(error.message, true));
  });
  $("prepromptItems").addEventListener("click", (event) => {
    const action = event.target?.dataset?.action;
    const container = event.target.closest(".edit-item");
    if (!action || !container) return;
    const operation = action === "save-profile" ? saveProfileItem : forgetProfileItem;
    operation(container).catch((error) => setStatus(error.message, true));
  });
}

wireEvents();
finishOAuthIfPresent()
  .then((handled) => {
    if (handled) return;
    if (state.token) {
      Promise.all([
        refreshReview(),
        refreshProfile(),
        refreshPrompt(),
      ]).catch((error) => setStatus(error.message, true));
    } else {
      setStatus("Authorize Brain or paste a bearer token to load memory.");
    }
  })
  .catch((error) => setStatus(error.message, true));
