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

  var chatUrl = root.dataset.chatUrl || "/assistant/chat";
  var conversationUrlTemplate = root.dataset.conversationUrlTemplate || "/assistant/conversation/0";

  var fab = document.getElementById("assistant-fab");
  var drawer = document.getElementById("assistant-drawer");
  var closeBtn = document.getElementById("assistant-close");
  var messagesEl = document.getElementById("assistant-messages");
  var inputEl = document.getElementById("assistant-input");
  var sendButton = document.getElementById("assistant-send");
  var typingEl = document.getElementById("assistant-typing");

  if (!fab || !drawer || !closeBtn || !messagesEl || !inputEl || !sendButton || !typingEl) {
    return;
  }

  var storageKey = "assistant:conversation:" + userId;
  var conversationId = readConversationId();
  var loadedConversationId = null;
  var sending = false;

  function isAssistantOpen() {
    return drawer.classList.contains("open");
  }

  function readConversationId() {
    var saved = null;
    try {
      saved = window.localStorage.getItem(storageKey);
    } catch (error) {
      return null;
    }
    if (!saved || !/^\d+$/.test(saved)) {
      return null;
    }
    return Number(saved);
  }

  function saveConversationId(id) {
    if (!id) {
      return;
    }
    conversationId = Number(id);
    try {
      window.localStorage.setItem(storageKey, String(conversationId));
    } catch (error) {
      // Ignora erros de storage (ex: modo privado com bloqueio).
    }
  }

  function clearConversationId() {
    conversationId = null;
    loadedConversationId = null;
    try {
      window.localStorage.removeItem(storageKey);
    } catch (error) {
      // Ignora erros de storage para manter o fluxo do widget.
    }
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

  function buildConversationUrl(id) {
    return conversationUrlTemplate.replace(/0$/, String(id));
  }

  function scrollMessagesToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function renderEmptyState() {
    messagesEl.innerHTML = "";
    var empty = document.createElement("p");
    empty.className = "assistant-empty";
    empty.textContent = "Fa\u00e7a uma pergunta...";
    messagesEl.appendChild(empty);
  }

  function removeEmptyStateIfPresent() {
    var emptyState = messagesEl.querySelector(".assistant-empty");
    if (emptyState) {
      emptyState.remove();
    }
  }

  function appendMessage(role, content) {
    removeEmptyStateIfPresent();
    var wrapper = document.createElement("div");
    wrapper.className = "assistant-message assistant-message--" + role;
    var bubble = document.createElement("div");
    bubble.className = "assistant-message__bubble";
    bubble.textContent = content;
    wrapper.appendChild(bubble);
    messagesEl.appendChild(wrapper);
    scrollMessagesToBottom();
  }

  function setTyping(visible) {
    typingEl.hidden = !visible;
    if (visible) {
      scrollMessagesToBottom();
    }
  }

  function setSendingState(isSending) {
    sending = isSending;
    sendButton.disabled = isSending;
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
    setAssistantOpen(true);

    if (conversationId) {
      loadConversationHistory(conversationId);
    } else if (!messagesEl.children.length) {
      renderEmptyState();
    }

    inputEl.focus();
  }

  function closeAssistant() {
    if (!isAssistantOpen()) {
      return;
    }
    setAssistantOpen(false);
  }

  function resizeInput() {
    inputEl.style.height = "auto";
    var newHeight = Math.min(inputEl.scrollHeight, 160);
    inputEl.style.height = String(newHeight) + "px";
  }

  async function loadConversationHistory(targetConversationId) {
    if (loadedConversationId === targetConversationId) {
      return;
    }

    try {
      var response = await fetch(buildConversationUrl(targetConversationId), {
        method: "GET",
        headers: {
          "Accept": "application/json"
        },
        credentials: "same-origin"
      });

      if (response.status === 404) {
        clearConversationId();
        renderEmptyState();
        return;
      }

      if (!response.ok) {
        throw new Error("Falha ao carregar o historico.");
      }

      var payload = await response.json();
      var messages = Array.isArray(payload.messages) ? payload.messages : [];

      messagesEl.innerHTML = "";
      if (!messages.length) {
        renderEmptyState();
      } else {
        for (var i = 0; i < messages.length; i += 1) {
          appendMessage(messages[i].role, messages[i].content);
        }
      }

      loadedConversationId = targetConversationId;
    } catch (error) {
      appendMessage("assistant", "Nao foi possivel carregar o historico agora.");
    }
  }

  async function sendMessage() {
    if (sending) {
      return;
    }

    var text = (inputEl.value || "").trim();
    if (!text) {
      return;
    }

    appendMessage("user", text);
    inputEl.value = "";
    resizeInput();
    setTyping(true);
    setSendingState(true);

    var payload = { text: text };
    if (conversationId) {
      payload.conversation_id = conversationId;
    }

    try {
      var response = await fetch(chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error("Falha ao enviar mensagem.");
      }

      var data = await response.json();
      if (data.conversation_id) {
        saveConversationId(data.conversation_id);
        loadedConversationId = conversationId;
      }

      appendMessage("assistant", data.answer || "");
    } catch (error) {
      appendMessage("assistant", "Erro ao enviar a mensagem. Tente novamente.");
    } finally {
      setTyping(false);
      setSendingState(false);
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

  // Fecha ao clicar fora do widget.
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
  renderEmptyState();
})();
