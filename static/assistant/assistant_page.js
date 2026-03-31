(function () {
  "use strict";

  function qsa(selector, rootElement) {
    return Array.prototype.slice.call((rootElement || document).querySelectorAll(selector));
  }

  var root = document.getElementById("assistant-page-root");
  var initialDataEl = document.getElementById("assistant-page-initial-data");
  if (!root || !initialDataEl) {
    return;
  }

  var initialData = {};
  try {
    initialData = JSON.parse(initialDataEl.textContent || "{}");
  } catch (error) {
    initialData = {};
  }

  var state = {
    assistantName: initialData.assistantName || "Eustacio",
    conversationLimit: Number(initialData.conversationLimit || 100),
    conversationCount: Number(initialData.conversationCount || 0),
    processingUi: initialData.processingUi || {},
    conversations: Array.isArray(initialData.conversations) ? initialData.conversations.slice() : [],
    selectedConversation: initialData.selectedConversation || null,
    sending: false,
    creating: false,
    deleting: false
  };

  var pageUrl = root.dataset.pageUrl || "/assistant/";
  var chatUrl = root.dataset.chatUrl || "/assistant/chat";
  var conversationsUrl = root.dataset.conversationsUrl || "/assistant/conversations";
  var conversationUrlTemplate = root.dataset.conversationUrlTemplate || "/assistant/conversations/0";
  var deleteUrlTemplate = root.dataset.deleteUrlTemplate || "/assistant/conversations/0/delete";

  var newButton = document.getElementById("assistant-page-new");
  var countEl = document.getElementById("assistant-page-count");
  var limitEl = document.getElementById("assistant-page-limit");
  var limitNoticeEl = document.getElementById("assistant-page-limit-notice");
  var sidebarFlashEl = document.getElementById("assistant-page-sidebar-flash");
  var mainFlashEl = document.getElementById("assistant-page-main-flash");
  var listEl = document.getElementById("assistant-page-list");
  var titleEl = document.getElementById("assistant-page-title");
  var subtitleEl = document.getElementById("assistant-page-subtitle");
  var deleteButton = document.getElementById("assistant-page-delete");
  var messagesEl = document.getElementById("assistant-page-messages");
  var typingEl = document.getElementById("assistant-page-typing");
  var formEl = document.getElementById("assistant-page-form");
  var inputEl = document.getElementById("assistant-page-input");
  var sendButton = document.getElementById("assistant-page-send");
  var suggestedQuestionButtons = qsa("[data-suggested-question]");

  if (!newButton || !countEl || !limitEl || !limitNoticeEl || !sidebarFlashEl || !mainFlashEl ||
      !listEl || !titleEl || !subtitleEl || !deleteButton || !messagesEl || !typingEl ||
      !formEl || !inputEl || !sendButton) {
    return;
  }

  var processingController = window.AssistantProcessingUI
    ? window.AssistantProcessingUI.createController(typingEl, state.processingUi)
    : null;
  var processingState = window.AssistantProcessingUI
    ? window.AssistantProcessingUI.createRequestState(processingController)
    : null;
  var hasServerRenderedMessages = messagesEl.children.length > 0;

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

  function buildDeleteUrl(id) {
    return deleteUrlTemplate.replace(/0\/delete$/, String(id) + "/delete");
  }

  function formatDateTime(value) {
    if (!value) {
      return "agora";
    }
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function messageLabel(count) {
    return count === 1 ? "mensagem" : "mensagens";
  }

  function selectedConversationId() {
    return state.selectedConversation && state.selectedConversation.id
      ? Number(state.selectedConversation.id)
      : null;
  }

  function sortConversations() {
    state.conversations.sort(function (left, right) {
      var leftDate = new Date(left.updated_at || left.created_at || 0).getTime();
      var rightDate = new Date(right.updated_at || right.created_at || 0).getTime();
      if (leftDate === rightDate) {
        return Number(right.id || 0) - Number(left.id || 0);
      }
      return rightDate - leftDate;
    });
  }

  function upsertConversationSummary(summary) {
    if (!summary || !summary.id) {
      return;
    }

    var updated = false;
    for (var i = 0; i < state.conversations.length; i += 1) {
      if (Number(state.conversations[i].id) === Number(summary.id)) {
        state.conversations[i] = Object.assign({}, state.conversations[i], summary);
        updated = true;
        break;
      }
    }
    if (!updated) {
      state.conversations.push(summary);
    }
    sortConversations();
  }

  function removeConversationSummary(conversationId) {
    state.conversations = state.conversations.filter(function (conversation) {
      return Number(conversation.id) !== Number(conversationId);
    });
  }

  function setFlash(element, message, type) {
    element.classList.remove("hidden", "is-error", "is-success");
    if (!message) {
      element.textContent = "";
      element.classList.add("hidden");
      return;
    }
    element.textContent = message;
    if (type === "error") {
      element.classList.add("is-error");
    } else if (type === "success") {
      element.classList.add("is-success");
    }
  }

  function clearFlashes() {
    setFlash(sidebarFlashEl, "", "");
    setFlash(mainFlashEl, "", "");
  }

  function startProcessing(text) {
    if (processingState) {
      var token = processingState.begin(text);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return token;
    }
    if (processingController) {
      processingController.start(text);
    } else {
      typingEl.hidden = false;
    }
    messagesEl.scrollTop = messagesEl.scrollHeight;
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

  function resizeInput() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + "px";
  }

  function updateControls() {
    var busy = state.sending || state.creating || state.deleting;
    var limitReached = state.conversationCount >= state.conversationLimit;
    newButton.disabled = busy || limitReached;
    sendButton.disabled = busy;
    deleteButton.disabled = busy || !selectedConversationId();
    countEl.textContent = String(state.conversationCount);
    limitEl.textContent = String(state.conversationLimit);
    limitNoticeEl.classList.toggle("hidden", !limitReached);
  }

  function syncUrl() {
    if (!window.history || typeof window.history.replaceState !== "function") {
      return;
    }
    var conversationId = selectedConversationId();
    var nextUrl = pageUrl;
    if (conversationId) {
      nextUrl += "?conversation_id=" + encodeURIComponent(String(conversationId));
    }
    window.history.replaceState({}, "", nextUrl);
  }

  function renderConversationList() {
    listEl.innerHTML = "";
    if (!state.conversations.length) {
      var empty = document.createElement("div");
      empty.id = "assistant-page-list-empty";
      empty.className = "assistant-page__list-empty";
      empty.innerHTML = 
        '<div style="font-size: 32px; margin: 0 auto 8px; text-align: center;">📥</div>' +
        '<p>Nenhuma conversa ainda.</p>' +
        '<p class="text-xs">Clique em "Nova conversa" para começar.</p>';
      listEl.appendChild(empty);
      return;
    }

    var activeId = selectedConversationId();
    for (var i = 0; i < state.conversations.length; i += 1) {
      var conversation = state.conversations[i];
      var row = document.createElement("div");
      row.className = "assistant-page__thread-row";
      row.setAttribute("role", "listitem");

      var link = document.createElement("a");
      link.href = buildPageConversationUrl(conversation.id);
      link.className = "assistant-page__thread";
      if (activeId && Number(conversation.id) === activeId) {
        link.classList.add("is-active");
      }
      link.setAttribute("data-conversation-link", "");
      link.setAttribute("data-conversation-id", String(conversation.id));

      var title = document.createElement("span");
      title.className = "assistant-page__thread-title";
      title.textContent = conversation.title || "Nova conversa";

      var meta = document.createElement("span");
      meta.className = "assistant-page__thread-meta";
      meta.textContent = String(conversation.message_count || 0) + " " +
        messageLabel(Number(conversation.message_count || 0)) + " - " +
        formatDateTime(conversation.updated_at || conversation.created_at);

      link.appendChild(title);
      link.appendChild(meta);

      var deleteThreadButton = document.createElement("button");
      deleteThreadButton.type = "button";
      deleteThreadButton.className = "assistant-page__thread-delete";
      deleteThreadButton.setAttribute("data-delete-conversation-id", String(conversation.id));
      deleteThreadButton.setAttribute("aria-label", "Excluir conversa " + (conversation.title || "Nova conversa"));
      deleteThreadButton.setAttribute("title", "Excluir conversa");
      deleteThreadButton.innerHTML = '<i data-lucide="trash-2" class="w-4 h-4"></i>';

      row.appendChild(link);
      row.appendChild(deleteThreadButton);
      listEl.appendChild(row);
    }
  }

  function renderConversationHeader() {
    var conversation = state.selectedConversation;
    if (!conversation) {
      titleEl.textContent = state.assistantName;
      subtitleEl.textContent = "Selecione uma conversa salva ou crie uma nova para iniciar um chat persistido.";
      deleteButton.classList.add("hidden");
      return;
    }

    titleEl.textContent = conversation.title || "Nova conversa";
    subtitleEl.textContent =
      "Atualizada em " + formatDateTime(conversation.updated_at || conversation.created_at) +
      " - " + String(conversation.message_count || 0) + " " + messageLabel(Number(conversation.message_count || 0));
    deleteButton.classList.remove("hidden");
  }

  function renderMessages(options) {
    if (options && options.preserveExisting && hasServerRenderedMessages) {
      return;
    }

    messagesEl.innerHTML = "";
    var conversation = state.selectedConversation;

    if (!conversation) {
      var emptyState = document.createElement("div");
      emptyState.className = "assistant-page__empty-state";
      emptyState.innerHTML =
        '<div style="font-size: 48px; margin: 0 auto 12px; text-align: center;">✨</div>' +
        '<div class="assistant-page__empty-title">O Eustácio pode ajudar você</div>' +
        '<p class="assistant-page__empty-copy">Use as sugestões ao lado ou pergunte livremente sobre produtividade, risco, alertas e pipeline de dados.</p>';
      messagesEl.appendChild(emptyState);
      hasServerRenderedMessages = false;
      return;
    }

    var messages = Array.isArray(conversation.messages) ? conversation.messages : [];
    
    if (!messages.length) {
      var blankState = document.createElement("div");
      blankState.className = "assistant-page__empty-state";
      blankState.innerHTML =
        '<div style="font-size: 48px; margin: 0 auto 12px; text-align: center;">💬</div>' +
        '<div class="assistant-page__empty-title">Conversa iniciada</div>' +
        '<p class="assistant-page__empty-copy">Envie a primeira pergunta para começar a conversar com o Eustácio.</p>';
      messagesEl.appendChild(blankState);
      hasServerRenderedMessages = false;
      return;
    }

    for (var i = 0; i < messages.length; i += 1) {
      var message = messages[i];
      
      var wrapper = document.createElement("div");
      wrapper.className = "assistant-page__message assistant-page__message--" + message.role;
      
      // Criar container flex para avatar + mensagem
      var flexContainer = document.createElement("div");
      flexContainer.className = "flex items-start gap-3";
      
      // Criar avatar com emoji como fallback
      var avatar = document.createElement("div");
      avatar.className = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0";
      avatar.style.fontSize = "16px";
      
      if (message.role === "user") {
        avatar.className += " bg-sky-500/20";
        avatar.textContent = "👤";
      } else {
        avatar.className += " bg-violet-500/20";
        avatar.textContent = "🤖";
      }
      
      // Criar bubble
      var bubble = document.createElement("div");
      bubble.className = "assistant-page__bubble";
      try {
        if (window.AssistantMessageRendering) {
          window.AssistantMessageRendering.renderMessageContent(document, bubble, message);
        } else {
          bubble.textContent = message.content || "";
        }
      } catch (renderError) {
        if (window.console && typeof window.console.error === "function") {
          window.console.error("[Eustacio][page] Falha ao renderizar mensagem.", renderError);
        }
        bubble.textContent = message && message.content ? message.content : "Mensagem indisponivel.";
      }
      
      flexContainer.appendChild(avatar);
      flexContainer.appendChild(bubble);
      wrapper.appendChild(flexContainer);
      messagesEl.appendChild(wrapper);
    }
    hasServerRenderedMessages = false;
    messagesEl.scrollTop = messagesEl.scrollHeight;
    
    // Tentar inicializar Lucide se disponível (opcional)
    setTimeout(function() {
      if (window.lucide) {
        try {
          window.lucide.createIcons();
        } catch (e) {
          window.console.debug("[Eustacio][page] Lucide indisponivel, seguindo com fallback visual.");
        }
      }
    }, 100);
  }

  function renderAll(options) {
    renderConversationList();
    renderConversationHeader();
    renderMessages(options);
    updateControls();
    syncUrl();
  }

  function buildPageConversationUrl(conversationId) {
    return pageUrl + "?conversation_id=" + encodeURIComponent(String(conversationId));
  }

  async function loadConversation(conversationId, pushFocus, fallbackUrl) {
    clearFlashes();
    resetProcessing();
    try {
      var url = buildConversationUrl(conversationId);
      var response = await fetch(url, {
        method: "GET",
        headers: {
          "Accept": "application/json"
        },
        credentials: "same-origin"
      });

      if (response.status === 404) {
        throw new Error("Conversa nao encontrada.");
      }
      var data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Nao foi possivel carregar a conversa.");
      }
      state.selectedConversation = data.conversation || null;

      if (state.selectedConversation) {
        upsertConversationSummary(state.selectedConversation);
      }
      renderAll();
      if (pushFocus) {
        inputEl.focus();
      }
    } catch (error) {
      if (fallbackUrl && window.location && typeof window.location.assign === "function") {
        window.location.assign(fallbackUrl);
        return;
      }
      setFlash(mainFlashEl, error.message || "Nao foi possivel carregar a conversa.", "error");
    }
  }

  async function createConversation(options) {
    if (state.creating) {
      return state.selectedConversation;
    }

    clearFlashes();
    state.creating = true;
    updateControls();

    try {
      var response = await fetch(conversationsUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({})
      });
      var data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Nao foi possivel criar uma nova conversa.");
      }

      var conversation = data.conversation || null;
      if (!conversation) {
        throw new Error("Resposta invalida ao criar a conversa.");
      }
      conversation.messages = [];
      state.selectedConversation = conversation;
      state.conversationCount = Number(data.conversation_count || state.conversationCount + 1);
      upsertConversationSummary(conversation);
      renderAll();
      if (!options || !options.silentSuccess) {
        setFlash(sidebarFlashEl, "Nova conversa criada.", "success");
      }
      if (!options || options.redirectOnSuccess !== false) {
        window.location.assign(buildPageConversationUrl(conversation.id));
        return conversation;
      }
      inputEl.focus();
      return conversation;
    } catch (error) {
      setFlash(sidebarFlashEl, error.message || "Nao foi possivel criar uma nova conversa.", "error");
      return null;
    } finally {
      state.creating = false;
      updateControls();
    }
  }

  async function deleteConversationById(conversationId, options) {
    if (!conversationId || state.deleting) {
      return;
    }

    if (!window.confirm("Excluir esta conversa do historico?")) {
      return;
    }

    clearFlashes();
    resetProcessing();
    state.deleting = true;
    updateControls();

    try {
      var response = await fetch(buildDeleteUrl(conversationId), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({})
      });
      var data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Nao foi possivel excluir a conversa.");
      }

      removeConversationSummary(conversationId);
      state.conversationCount = Number(data.conversation_count || Math.max(state.conversationCount - 1, 0));
      if (Number(selectedConversationId()) === Number(conversationId)) {
        state.selectedConversation = null;
      }
      renderAll();
      setFlash(sidebarFlashEl, "Conversa excluida.", "success");

      if (options && options.redirectAfterDelete) {
        if (state.conversations.length) {
          window.location.assign(buildPageConversationUrl(state.conversations[0].id));
        } else {
          window.location.assign(pageUrl);
        }
        return;
      }
      inputEl.focus();
    } catch (error) {
      setFlash(mainFlashEl, error.message || "Nao foi possivel excluir a conversa.", "error");
    } finally {
      state.deleting = false;
      updateControls();
    }
  }

  async function deleteCurrentConversation() {
    var conversationId = selectedConversationId();
    await deleteConversationById(conversationId, { redirectAfterDelete: true });
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (state.sending || state.creating || state.deleting) {
      return;
    }

    var text = (inputEl.value || "").trim();
    if (!text) {
      return;
    }

    clearFlashes();
    if (!selectedConversationId()) {
      var conversation = await createConversation({ silentSuccess: true, redirectOnSuccess: false });
      if (!conversation || !conversation.id) {
        return;
      }
    }

    var conversationId = selectedConversationId();
    state.sending = true;
    var requestToken = startProcessing(text);
    updateControls();

    try {
      var response = await fetch(chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({
          text: text,
          conversation_id: conversationId,
          origin: "page"
        })
      });
      var data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Nao foi possivel enviar a mensagem.");
      }

      if (!data.conversation_id) {
        throw new Error(data.answer || "Nao foi possivel continuar esta conversa.");
      }
      if (data && data.debug_trace && window.console && typeof window.console.debug === "function") {
        window.console.debug("[Eustacio][page][trace]", data.debug_trace);
      }

      if (Number(conversationId) !== Number(selectedConversationId())) {
        if (data.conversation) {
          upsertConversationSummary(data.conversation);
          renderConversationList();
          updateControls();
        }
        stopProcessing(requestToken);
        return;
      }

      if (!state.selectedConversation || Number(state.selectedConversation.id) !== Number(data.conversation_id)) {
        state.selectedConversation = {
          id: data.conversation_id,
          messages: []
        };
      }

      if (data.conversation) {
        upsertConversationSummary(data.conversation);
        state.selectedConversation = Object.assign({}, data.conversation);
      } else {
        var currentMessages = Array.isArray(state.selectedConversation.messages)
          ? state.selectedConversation.messages.slice()
          : [];
        currentMessages.push({
          role: "user",
          content: text,
          payload: {},
          created_at: new Date().toISOString()
        });
        currentMessages.push({
          role: "assistant",
          content: data.answer || "",
          payload: data && typeof data.answer_payload === "object" ? data.answer_payload : {},
          created_at: new Date().toISOString()
        });
        state.selectedConversation.messages = currentMessages;
        state.selectedConversation.message_count = currentMessages.length;
      }

      inputEl.value = "";
      resizeInput();
      renderAll();
      stopProcessing(requestToken);
    } catch (error) {
      failProcessing(requestToken);
      setFlash(mainFlashEl, error.message || "Nao foi possivel enviar a mensagem.", "error");
    } finally {
      state.sending = false;
      updateControls();
      inputEl.focus();
    }
  }

  newButton.addEventListener("click", function () {
    createConversation({ redirectOnSuccess: true });
  });

  deleteButton.addEventListener("click", function () {
    deleteCurrentConversation();
  });

  listEl.addEventListener("click", function (event) {
    var deleteConversationButton = event.target.closest("[data-delete-conversation-id]");
    if (deleteConversationButton) {
      event.preventDefault();
      event.stopPropagation();
      var deleteConversationId = deleteConversationButton.getAttribute("data-delete-conversation-id");
      if (!deleteConversationId) {
        return;
      }
      deleteConversationById(deleteConversationId, {
        redirectAfterDelete: Number(deleteConversationId) === Number(selectedConversationId())
      });
      return;
    }

    var link = event.target.closest("[data-conversation-link]");
    if (!link) {
      return;
    }
    if (link.href && window.location && typeof window.location.assign === "function") {
      event.preventDefault();
      window.location.assign(link.href);
    }
  });

  formEl.addEventListener("submit", sendMessage);

  inputEl.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(event);
    }
  });

  inputEl.addEventListener("input", resizeInput);

  suggestedQuestionButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      var question = button.getAttribute("data-suggested-question") || "";
      inputEl.value = question;
      resizeInput();
      inputEl.focus();
    });
  });

  sortConversations();
  resizeInput();
  resetProcessing();
  renderAll({ preserveExisting: true });
})();
