(function () {
  "use strict";

  var root = document.getElementById("assistant-widget-root");
  if (!root) {
    return;
  }

  var userId = root.dataset.userId;
  if (!userId) {
    return;
  }

  var widgetChatUrl = root.dataset.widgetChatUrl || "/assistant/widget/chat";
  var widgetSaveUrl = root.dataset.widgetSaveUrl || "/assistant/widget/session/save";
  var assistantName = root.dataset.assistantName || "Eustacio";
  var emptyStateMessage = root.dataset.emptyState || (
    "Pergunte ao " + assistantName + " sobre monitoramento, produtividade, pausas, relatorios e regras operacionais."
  );
  var saveLabel = root.dataset.saveLabel || "Salvar conversa";
  var savedLabel = root.dataset.savedLabel || "Conversa salva";

  var fab = document.getElementById("assistant-fab");
  var drawer = document.getElementById("assistant-drawer");
  var closeBtn = document.getElementById("assistant-close");
  var saveButton = document.getElementById("assistant-save");
  var messagesEl = document.getElementById("assistant-messages");
  var inputEl = document.getElementById("assistant-input");
  var sendButton = document.getElementById("assistant-send");
  var typingEl = document.getElementById("assistant-typing");
  var processingConfigEl = document.getElementById("assistant-widget-processing-config");

  if (!fab || !drawer || !closeBtn || !saveButton || !messagesEl || !inputEl || !sendButton || !typingEl) {
    return;
  }

  var processingConfig = {};
  try {
    processingConfig = processingConfigEl ? JSON.parse(processingConfigEl.textContent || "{}") : {};
  } catch (error) {
    processingConfig = {};
  }
  var processingController = window.AssistantProcessingUI
    ? window.AssistantProcessingUI.createController(typingEl, processingConfig)
    : null;
  var processingState = window.AssistantProcessingUI
    ? window.AssistantProcessingUI.createRequestState(processingController)
    : null;

  var sending = false;
  var saving = false;
  var widgetSessionId = null;
  var savedConversationId = null;
  var sessionMessages = [];

  function isAssistantOpen() {
    return drawer.classList.contains("open");
  }

  function createWidgetSessionId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") {
      return "widget_" + window.crypto.randomUUID().replace(/-/g, "");
    }
    return "widget_" + Date.now() + "_" + Math.floor(Math.random() * 1000000);
  }

  function ensureWidgetSessionId() {
    if (!widgetSessionId) {
      widgetSessionId = createWidgetSessionId();
    }
    return widgetSessionId;
  }

  function getCsrfToken() {
    var name = "csrftoken=";
    var decodedCookie = decodeURIComponent(document.cookie || "");
    var chunks = decodedCookie.split(";");
    for (var i = 0; i < chunks.length; i += 1) {
      var chunk = chunks[i].trim();
      if (chunk.indexOf(name) === 0) {
        return chunk.substring(name.length);
      }
    }
    return "";
  }

  function scrollMessagesToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function renderEmptyState() {
    messagesEl.innerHTML = "";
    var empty = document.createElement("p");
    empty.className = "assistant-empty";
    empty.textContent = emptyStateMessage;
    messagesEl.appendChild(empty);
  }

  function removeEmptyStateIfPresent() {
    var emptyState = messagesEl.querySelector(".assistant-empty");
    if (emptyState) {
      emptyState.remove();
    }
  }

  function appendMessage(role, content, payload) {
    removeEmptyStateIfPresent();
    var wrapper = document.createElement("div");
    wrapper.className = "assistant-message assistant-message--" + role;
    var bubble = document.createElement("div");
    bubble.className = "assistant-message__bubble";
    if (window.AssistantMessageRendering) {
      window.AssistantMessageRendering.renderMessageContent(document, bubble, {
        role: role,
        content: content,
        payload: payload || {}
      });
    } else {
      bubble.textContent = content;
    }
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollMessagesToBottom();
  }

  function normalizeSessionMessages(messages) {
    if (!Array.isArray(messages)) {
      return [];
    }
    return messages
      .filter(function (item) {
        return item && (item.role === "user" || item.role === "assistant" || item.role === "system") && item.content;
      })
      .map(function (item) {
        return {
          role: item.role,
          content: String(item.content),
          payload: item && typeof item.payload === "object" ? item.payload : {}
        };
      });
  }

  function renderSessionMessages() {
    if (!sessionMessages.length) {
      renderEmptyState();
      return;
    }

    messagesEl.innerHTML = "";
    for (var i = 0; i < sessionMessages.length; i += 1) {
      appendMessage(sessionMessages[i].role, sessionMessages[i].content, sessionMessages[i].payload);
    }
  }

  function startProcessing(text) {
    if (processingState) {
      var token = processingState.begin(text);
      scrollMessagesToBottom();
      return token;
    }
    if (processingController) {
      processingController.start(text);
    } else {
      typingEl.hidden = false;
    }
    scrollMessagesToBottom();
    return 1;
  }

  function failProcessing(token) {
    if (processingState) {
      return processingState.fail(token);
    }
    if (processingController) {
      processingController.fail();
    } else {
      typingEl.hidden = false;
    }
    return true;
  }

  function stopProcessing(token) {
    if (processingState) {
      return processingState.complete(token);
    }
    if (processingController) {
      processingController.stop();
    } else {
      typingEl.hidden = true;
    }
    return true;
  }

  function resetProcessing() {
    if (processingState) {
      processingState.reset();
      return;
    }
    if (processingController) {
      processingController.reset();
      return;
    }
    typingEl.hidden = true;
  }

  function updateControls() {
    sendButton.disabled = sending || saving;
    saveButton.disabled = sending || saving || !sessionMessages.length || Boolean(savedConversationId);
    saveButton.textContent = savedConversationId ? savedLabel : saveLabel;
  }

  function setAssistantOpen(open) {
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    fab.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function openAssistant() {
    if (isAssistantOpen()) {
      return;
    }
    ensureWidgetSessionId();
    resetProcessing();
    setAssistantOpen(true);
    renderSessionMessages();
    updateControls();
    inputEl.focus();
  }

  function resizeInput() {
    inputEl.style.height = "auto";
    var newHeight = Math.min(inputEl.scrollHeight, 160);
    inputEl.style.height = String(newHeight) + "px";
  }

  function closeAssistant() {
    if (!isAssistantOpen()) {
      return;
    }

    setAssistantOpen(false);
    resetProcessing();
  }

  async function sendMessage() {
    if (sending || saving) {
      return;
    }

    var text = (inputEl.value || "").trim();
    if (!text) {
      return;
    }

    var currentSessionId = ensureWidgetSessionId();
    var requestToken = startProcessing(text);
    appendMessage("user", text);
    inputEl.value = "";
    resizeInput();
    sending = true;
    updateControls();

    try {
      var response = await fetch(widgetChatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({
          text: text,
          widget_session_id: currentSessionId
        })
      });

      var data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Falha ao enviar mensagem.");
      }

      if (currentSessionId !== widgetSessionId) {
        return;
      }

      widgetSessionId = data.widget_session_id || currentSessionId;
      if (Array.isArray(data.messages)) {
        sessionMessages = normalizeSessionMessages(data.messages);
      } else {
        sessionMessages.push({ role: "user", content: text, payload: {} });
        sessionMessages.push({
          role: "assistant",
          content: data.answer || "",
          payload: data && typeof data.answer_payload === "object" ? data.answer_payload : {}
        });
      }
      if (data.saved_conversation_id) {
        savedConversationId = Number(data.saved_conversation_id);
      }
      if (data && data.debug_trace && window.console && typeof window.console.debug === "function") {
        window.console.debug("[Eustacio][widget][trace]", data.debug_trace);
      }

      renderSessionMessages();
      stopProcessing(requestToken);
    } catch (error) {
      if (currentSessionId === widgetSessionId) {
        failProcessing(requestToken);
        appendMessage("assistant", error.message || "Erro ao enviar a mensagem. Tente novamente.");
      }
    } finally {
      sending = false;
      updateControls();
      if (isAssistantOpen()) {
        inputEl.focus();
      }
    }
  }

  async function saveConversation() {
    if (saving || sending || !sessionMessages.length || savedConversationId) {
      return;
    }

    var currentSessionId = ensureWidgetSessionId();
    saving = true;
    updateControls();

    try {
      var response = await fetch(widgetSaveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({ widget_session_id: currentSessionId })
      });

      var data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Nao foi possivel salvar a conversa.");
      }

      if (currentSessionId !== widgetSessionId) {
        return;
      }

      savedConversationId = Number(data.conversation_id || 0) || null;
      updateControls();
    } catch (error) {
      if (currentSessionId === widgetSessionId) {
        appendMessage("assistant", error.message || "Nao foi possivel salvar a conversa.");
      }
    } finally {
      saving = false;
      updateControls();
      inputEl.focus();
    }
  }

  fab.addEventListener("click", function () {
    if (isAssistantOpen()) {
      closeAssistant();
    } else {
      openAssistant();
    }
  });

  closeBtn.addEventListener("click", closeAssistant);

  saveButton.addEventListener("click", function () {
    saveConversation();
  });

  sendButton.addEventListener("click", function () {
    sendMessage();
  });

  inputEl.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  inputEl.addEventListener("input", resizeInput);

  drawer.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAssistant();
      fab.focus();
    }
  });

  document.addEventListener("click", function (event) {
    if (!isAssistantOpen()) {
      return;
    }
    if (drawer.contains(event.target) || fab.contains(event.target)) {
      return;
    }
    closeAssistant();
  });

  resizeInput();
  resetProcessing();
  renderEmptyState();
  updateControls();
})();
