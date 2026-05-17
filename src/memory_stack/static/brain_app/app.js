const state = {
  previewArgs: null,
  latestSession: null,
  latestHealth: null,
  csrfToken: "",
  currentUser: null,
};

const endpointGroups = [
  {
    title: "User UI",
    endpoints: [
      { method: "GET", path: "/", label: "Memory dashboard" },
      { method: "GET", path: "/user", label: "Memory dashboard alias" },
      { method: "GET", path: "/cognee", label: "User Cognee UI" },
      { method: "GET", path: "/cognee-login", label: "Cognee UI sign-in" },
      { method: "GET", path: "/privacy", label: "Privacy" },
      { method: "GET", path: "/terms", label: "Terms" },
      { method: "GET", path: "/support", label: "Support" },
    ],
  },
  {
    title: "Brain MCP",
    endpoints: [
      { method: "GET/POST", path: "/mcp", label: "Curated ChatGPT App MCP" },
      { method: "GET/POST", path: "/admin/mcp", label: "Admin MCP surface" },
      { method: "GET/POST", path: "/app/mcp", label: "Legacy curated MCP alias" },
    ],
  },
  {
    title: "Auth And Account",
    endpoints: [
      { method: "POST", path: "/login", label: "Cookie session login" },
      { method: "POST", path: "/logout", label: "Cookie session logout" },
      { method: "GET", path: "/auth/session", label: "Current UI session" },
      { method: "PUT", path: "/account/password", label: "Change own password" },
      { method: "POST", path: "/register", label: "OAuth client registration" },
      { method: "POST", path: "/token", label: "OAuth token exchange" },
      { method: "POST", path: "/revoke", label: "OAuth token revoke" },
    ],
  },
  {
    title: "Admin",
    endpoints: [
      { method: "GET", path: "/admin", label: "Admin dashboard" },
      { method: "GET/POST", path: "/admin/users", label: "List or create users" },
      { method: "PUT/DELETE", path: "/admin/users/{user_id}", label: "Update or delete user" },
      { method: "GET", path: "/admin/cognee", label: "Admin Cognee UI" },
      { method: "ANY", path: "/admin/cognee-api/{path}", label: "Admin Cognee API proxy" },
    ],
  },
  {
    title: "Memory HTTP",
    endpoints: [
      { method: "POST", path: "/memory/remember", label: "Store memory" },
      { method: "POST", path: "/memory/ingest_source", label: "Ingest source" },
      { method: "POST", path: "/memory/recall", label: "Recall memories" },
      { method: "POST", path: "/memory/profile_entity", label: "Profile entity" },
      { method: "GET", path: "/memory/open_loops", label: "List open loops" },
      { method: "GET", path: "/memory/{memory_id}", label: "Read memory" },
      { method: "POST", path: "/memory/review_recent", label: "Review recent writes" },
      { method: "POST", path: "/memory/undo_last", label: "Undo latest write" },
    ],
  },
  {
    title: "Discovery And Health",
    endpoints: [
      { method: "GET", path: "/healthz", label: "Brain service health" },
      { method: "GET", path: "/.well-known/oauth-protected-resource/mcp", label: "MCP resource metadata" },
      { method: "GET", path: "/.well-known/oauth-protected-resource/admin/mcp", label: "Admin MCP resource metadata" },
      { method: "GET", path: "/.well-known/oauth-authorization-server", label: "OAuth authorization metadata" },
      { method: "GET", path: "/icon.png", label: "App icon" },
    ],
  },
  {
    title: "Slack Agent",
    endpoints: [
      { method: "GET", path: "/slack/healthz", label: "Slack service health" },
      { method: "POST", path: "/slack/events", label: "Slack events" },
      { method: "POST", path: "/slack/commands", label: "Slash commands" },
      { method: "POST", path: "/slack/interactions", label: "Block interactions" },
    ],
  },
];

const $ = (id) => document.getElementById(id);

function setStatus(message, isError = false) {
  const status = $("status");
  status.textContent = message || "";
  status.classList.toggle("error", isError);
}

function csrfHeader() {
  return state.csrfToken ? { "X-Brain-CSRF": state.csrfToken } : {};
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
  const response = await fetch("/mcp", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...csrfHeader(),
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

async function adminRequest(path, { method = "GET", body = null } = {}) {
  const response = await fetch(path, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(method === "GET" ? {} : csrfHeader()),
    },
    body: body ? JSON.stringify(body) : null,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function accountRequest(path, { method = "GET", body = null } = {}) {
  const response = await fetch(path, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(method === "GET" ? {} : csrfHeader()),
    },
    body: body ? JSON.stringify(body) : null,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

function setLoggedIn(payload) {
  state.csrfToken = payload.csrf_token || "";
  state.currentUser = payload.user || null;
  $("loginOverlay").classList.toggle("hidden", Boolean(state.currentUser));
  $("currentUser").textContent = state.currentUser
    ? `${state.currentUser.display_name || state.currentUser.id}${state.currentUser.superuser ? " (root)" : ""}`
    : "Signed out";
  $("accountDetails").textContent = JSON.stringify(state.currentUser || {}, null, 2);
  document.querySelector('[data-tab="users"]').classList.toggle("hidden", !state.currentUser?.superuser);
}

async function refreshSession() {
  const response = await fetch("/auth/session");
  if (response.status === 401) {
    setLoggedIn({});
    setStatus("Sign in to load Brain.");
    return false;
  }
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  setLoggedIn(payload);
  return true;
}

async function refreshHealth() {
  const response = await fetch("/healthz");
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  state.latestHealth = payload;
  return payload;
}

async function loginUser() {
  $("loginStatus").textContent = "Signing in...";
  const response = await fetch("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: $("loginUserId").value,
      password: $("loginPassword").value,
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  $("loginPassword").value = "";
  $("loginStatus").textContent = "";
  setLoggedIn(payload);
  await loadInitialData();
}

async function logoutUser() {
  await fetch("/logout", {
    method: "POST",
    headers: csrfHeader(),
  });
  state.csrfToken = "";
  state.currentUser = null;
  setLoggedIn({});
  setStatus("Signed out.");
}

async function changePassword() {
  setStatus("Changing password...");
  await accountRequest("/account/password", {
    method: "PUT",
    body: {
      current_password: $("currentPassword").value,
      new_password: $("newPassword").value,
    },
  });
  $("currentPassword").value = "";
  $("newPassword").value = "";
  setStatus("Password changed.");
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

async function refreshControls() {
  setStatus("Loading data controls...");
  const payload = await mcpCall("brain_app_data_controls", {
    limit: 25,
    include_recent_memories: true,
  });
  renderList(
    $("appWriteAudit"),
    payload.app_write_audit,
    "No app writes audited yet.",
    (item) => {
      const title = `${item.tool_name || "app write"} - ${item.status || "unknown"}`;
      const meta = [
        item.created_at,
        item.target_id,
        item.confirmed_by_user ? "confirmed" : "unconfirmed",
      ].filter(Boolean).join(" - ");
      return `<div class="item-title">${safe(title)}</div><div class="item-meta">${safe(meta)}</div><div>${safe(item.summary || "")}</div>`;
    },
  );
  renderList(
    $("controlsProfileItems"),
    [...(payload.profile_context || []), ...(payload.preprompt_items || [])],
    "No profile data.",
    (item) => `<div class="item-title">${safe(item.statement)}</div><div class="item-meta">${safe(item.scope)} - ${safe(item.id)}</div>`,
  );
  renderList(
    $("controlsMemoryItems"),
    payload.recent_memory_cards,
    "No recent memories.",
    (item) => `<div class="item-title">${safe(item.summary || item.statement || item.id)}</div><div class="item-meta">${safe(item.kind)} - ${safe(item.id)}</div>`,
  );
  $("dataExport").textContent = JSON.stringify(payload, null, 2);
  setStatus("Data controls loaded.");
}

async function refreshUsers() {
  setStatus("Loading users...");
  const payload = await adminRequest("/admin/users");
  $("usersRegistry").textContent = JSON.stringify({
    users_file: payload.users_file,
    users_file_configured: payload.users_file_configured,
    current_user_id: payload.current_user_id,
    superuser_ids: payload.superuser_ids,
  }, null, 2);
  renderEditableUsers(payload.users || []);
  setStatus("Users loaded.");
}

function renderEditableUsers(users) {
  const target = $("usersList");
  target.innerHTML = "";
  if (!users.length) {
    target.innerHTML = '<div class="item"><div class="item-meta">No users configured.</div></div>';
    return;
  }
  users.forEach((user) => {
    const wrapper = document.createElement("article");
    wrapper.className = "item edit-item user-item";
    wrapper.dataset.userId = user.id;
    wrapper.innerHTML = `
      <div class="item-title">${safe(user.id)}</div>
      <label>Display name</label>
      <input data-field="display_name" value="${safe(user.display_name || "")}" />
      <label>Email</label>
      <input data-field="email" value="${safe(user.email || "")}" />
      <label>New password</label>
      <input data-field="password" type="password" autocomplete="new-password" placeholder="leave unchanged" />
      <label class="check-row">
        <input data-field="superuser" type="checkbox" ${user.superuser ? "checked" : ""} />
        <span>Superuser</span>
      </label>
      <div class="form-row">
        <button type="button" data-action="save-user">Save</button>
        <button class="danger" type="button" data-action="delete-user">Delete</button>
      </div>
    `;
    target.appendChild(wrapper);
  });
}

async function createUser() {
  setStatus("Creating user...");
  await adminRequest("/admin/users", {
    method: "POST",
    body: {
      id: $("newUserId").value,
      display_name: $("newUserDisplayName").value,
      email: $("newUserEmail").value,
      password: $("newUserPassword").value,
      superuser: $("newUserSuperuser").checked,
    },
  });
  $("newUserId").value = "";
  $("newUserDisplayName").value = "";
  $("newUserEmail").value = "";
  $("newUserPassword").value = "";
  $("newUserSuperuser").checked = false;
  await refreshUsers();
}

async function saveUser(container) {
  const userId = container.dataset.userId;
  const password = container.querySelector('[data-field="password"]').value;
  const body = {
    display_name: container.querySelector('[data-field="display_name"]').value,
    email: container.querySelector('[data-field="email"]').value,
    superuser: container.querySelector('[data-field="superuser"]').checked,
  };
  if (password) body.password = password;
  setStatus("Saving user...");
  await adminRequest(`/admin/users/${encodeURIComponent(userId)}`, {
    method: "PUT",
    body,
  });
  await refreshUsers();
}

async function deleteUser(container) {
  const userId = container.dataset.userId;
  if (!window.confirm(`Delete user ${userId}? Existing user-scoped Brain data is not deleted.`)) return;
  setStatus("Deleting user...");
  await adminRequest(`/admin/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
  await refreshUsers();
}

function promptText(promptPayload) {
  return promptPayload?.messages?.[0]?.content?.text || JSON.stringify(promptPayload, null, 2);
}

async function refreshEndpointHelp() {
  setStatus("Loading endpoint help...");
  const health = await refreshHealth();
  const baseUrl = (health.public_mcp_url || "").replace(/\/mcp$/, "") || window.location.origin;
  $("endpointHelp").innerHTML = endpointGroups.map((group) => `
    <article class="endpoint-group">
      <h3>${safe(group.title)}</h3>
      <div class="endpoint-list">
        ${group.endpoints.map((endpoint) => `
          <div class="endpoint-row">
            <span class="endpoint-method">${safe(endpoint.method)}</span>
            <code>${safe(endpoint.path)}</code>
            <span>${safe(endpoint.label)}</span>
          </div>
        `).join("")}
      </div>
    </article>
  `).join("");
  $("endpointHelp").insertAdjacentHTML(
    "afterbegin",
    `<div class="endpoint-base">Public base: <code>${safe(baseUrl)}</code></div>`,
  );
  setStatus("Endpoint help loaded.");
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
    confirmed_by_user: true,
  });
  if (oldId && saved.id !== oldId) {
    await mcpCall("brain_profile_context_forget", {
      context_id: oldId,
      confirmed_by_user: true,
    });
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
  if (tabName === "users" && state.currentUser?.superuser) {
    refreshUsers().catch((error) => setStatus(error.message, true));
  }
  if (tabName === "help") {
    refreshEndpointHelp().catch((error) => setStatus(error.message, true));
  }
}

async function loadInitialData() {
  await Promise.all([
    refreshReview(),
    refreshProfile(),
    refreshPrompt(),
    refreshControls(),
  ]);
}

function wireEvents() {
  $("loginForm").addEventListener("submit", (event) => {
    event.preventDefault();
    loginUser().catch((error) => {
      $("loginStatus").textContent = error.message;
      $("loginStatus").classList.add("error");
    });
  });
  $("logoutButton").addEventListener("click", () => {
    logoutUser().catch((error) => setStatus(error.message, true));
  });
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => showTab(tab.dataset.tab));
  });
  $("refreshReview").addEventListener("click", () => refreshReview().catch((error) => setStatus(error.message, true)));
  $("refreshProfile").addEventListener("click", () => refreshProfile().catch((error) => setStatus(error.message, true)));
  $("refreshPrompt").addEventListener("click", () => refreshPrompt().catch((error) => setStatus(error.message, true)));
  $("refreshControls").addEventListener("click", () => refreshControls().catch((error) => setStatus(error.message, true)));
  $("refreshUsers").addEventListener("click", () => refreshUsers().catch((error) => setStatus(error.message, true)));
  $("refreshEndpointHelp").addEventListener("click", () => refreshEndpointHelp().catch((error) => setStatus(error.message, true)));
  $("passwordForm").addEventListener("submit", (event) => {
    event.preventDefault();
    changePassword().catch((error) => setStatus(error.message, true));
  });
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
      confirmed_by_user: true,
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
      confirmed_by_user: true,
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
  $("userForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    createUser().catch((error) => setStatus(error.message, true));
  });
  $("usersList").addEventListener("click", (event) => {
    const action = event.target?.dataset?.action;
    const container = event.target.closest(".user-item");
    if (!action || !container) return;
    const operation = action === "save-user" ? saveUser : deleteUser;
    operation(container).catch((error) => setStatus(error.message, true));
  });
}

wireEvents();
refreshSession()
  .then((authenticated) => {
    if (authenticated) {
      if (window.location.pathname.startsWith("/admin") && state.currentUser?.superuser) {
        showTab("users");
      }
      return loadInitialData();
    }
    return null;
  })
  .catch((error) => setStatus(error.message, true));
