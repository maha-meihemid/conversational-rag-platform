const API_BASE = "/api/v1";
const SESSION_KEY = "rag_conversation_id";

const elements = {
  chatForm: document.querySelector("#chat-form"),
  messageInput: document.querySelector("#message"),
  messages: document.querySelector("#messages"),
  welcomeCard: document.querySelector("#welcome-card"),
  composerStatus: document.querySelector("#composer-status"),
  sendButton: document.querySelector("#send-button"),
  newChat: document.querySelector("#new-chat"),
  pageTitle: document.querySelector("#page-title"),
  profileForm: document.querySelector("#profile-form"),
  profileStatus: document.querySelector("#profile-status"),
  saveProfile: document.querySelector("#save-profile"),
  apiStatus: document.querySelector("#api-status"),
  statusDot: document.querySelector(".status-dot"),
};

function setApiStatus(online) {
  elements.apiStatus.textContent = online ? "API online" : "API unavailable";
  elements.statusDot.classList.toggle("is-online", online);
  elements.statusDot.classList.toggle("is-offline", !online);
}

function addMessage(role, text, pending = false) {
  elements.welcomeCard.hidden = true;
  const article = document.createElement("article");
  article.className = `message ${role}${pending ? " pending" : ""}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  article.appendChild(bubble);
  elements.messages.appendChild(article);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return article;
}

function setSending(sending) {
  elements.sendButton.disabled = sending;
  elements.messageInput.disabled = sending;
  elements.composerStatus.textContent = sending
    ? "Searching the knowledge base…"
    : "Session memory is active";
}

async function sendMessage(message) {
  addMessage("user", message);
  const pending = addMessage("assistant", "Thinking with your knowledge base…", true);
  setSending(true);

  const payload = { message };
  const conversationId = localStorage.getItem(SESSION_KEY);
  if (conversationId) payload.conversation_id = conversationId;

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("The assistant is temporarily unavailable.");
    const result = await response.json();
    localStorage.setItem(SESSION_KEY, result.conversation_id);
    pending.remove();
    addMessage("assistant", result.answer);
    setApiStatus(true);
  } catch (error) {
    pending.remove();
    addMessage("assistant", error.message);
    setApiStatus(false);
  } finally {
    setSending(false);
    elements.messageInput.focus();
  }
}

elements.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  if (!message) return;
  elements.messageInput.value = "";
  elements.messageInput.style.height = "auto";
  sendMessage(message);
});

elements.messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.chatForm.requestSubmit();
  }
});

elements.messageInput.addEventListener("input", () => {
  elements.messageInput.style.height = "auto";
  elements.messageInput.style.height = `${elements.messageInput.scrollHeight}px`;
});

document.querySelectorAll(".prompt-chip").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.textContent.trim()));
});

elements.newChat.addEventListener("click", async () => {
  const conversationId = localStorage.getItem(SESSION_KEY);
  if (conversationId) {
    try {
      await fetch(`${API_BASE}/conversations/${conversationId}`, { method: "DELETE" });
    } catch {
      // Local session reset remains available if the API cannot be reached.
    }
  }
  localStorage.removeItem(SESSION_KEY);
  elements.messages.querySelectorAll(".message").forEach((message) => message.remove());
  elements.welcomeCard.hidden = false;
  elements.composerStatus.textContent = "New session ready";
  elements.messageInput.focus();
});

async function loadProfile() {
  try {
    const response = await fetch(`${API_BASE}/assistant-profile`);
    if (!response.ok) throw new Error();
    const profile = await response.json();
    Object.entries(profile).forEach(([name, value]) => {
      const field = elements.profileForm.elements.namedItem(name);
      if (field) field.value = value;
    });
    document.querySelector("#welcome-copy").textContent =
      `Talk with ${profile.name}, grounded only in ${profile.domain}.`;
    elements.profileStatus.textContent = "Profile loaded from the API.";
    setApiStatus(true);
  } catch {
    elements.profileStatus.textContent = "The assistant profile could not be loaded.";
    setApiStatus(false);
  }
}

elements.profileForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  elements.saveProfile.disabled = true;
  elements.profileStatus.textContent = "Saving profile…";
  const profile = Object.fromEntries(new FormData(elements.profileForm).entries());

  try {
    const response = await fetch(`${API_BASE}/assistant-profile`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    if (response.status === 403) {
      throw new Error("Editing is disabled. Enable it in the server environment first.");
    }
    if (!response.ok) throw new Error("The profile could not be saved.");
    elements.profileStatus.textContent = "Profile saved. New answers use this configuration.";
    await loadProfile();
  } catch (error) {
    elements.profileStatus.textContent = error.message;
  } finally {
    elements.saveProfile.disabled = false;
  }
});

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    const selected = button.dataset.view;
    document.querySelectorAll("[data-view]").forEach((item) => {
      item.classList.toggle("is-active", item === button);
    });
    document.querySelectorAll("[data-panel]").forEach((panel) => {
      const active = panel.dataset.panel === selected;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    elements.pageTitle.textContent = selected === "chat" ? "Conversation" : "Assistant profile";
    elements.newChat.hidden = selected !== "chat";
  });
});

loadProfile();
