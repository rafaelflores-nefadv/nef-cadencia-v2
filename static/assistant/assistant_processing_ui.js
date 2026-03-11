(function (root, factory) {
  "use strict";

  var api = factory(root);
  root.AssistantProcessingUI = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function (root) {
  "use strict";

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function buildDefaultConfig() {
    return {
      labels: {
        understanding_query: "Entendendo sua pergunta",
        checking_context: "Verificando o contexto da conversa",
        resolving_intent: "Interpretando sua solicitacao",
        querying_database: "Consultando dados no sistema",
        running_tool: "Buscando informacoes",
        filtering_results: "Filtrando os dados para melhor resultado",
        building_response: "Montando a resposta",
        validating_response: "Validando a resposta final",
        completed: "Resposta concluida",
        failed: "Nao foi possivel concluir o processamento"
      },
      fallbackSequences: {
        "default": [
          "understanding_query",
          "checking_context",
          "resolving_intent",
          "building_response",
          "validating_response"
        ],
        analytics: [
          "understanding_query",
          "checking_context",
          "resolving_intent",
          "querying_database",
          "filtering_results",
          "building_response",
          "validating_response"
        ],
        tool: [
          "understanding_query",
          "checking_context",
          "resolving_intent",
          "running_tool",
          "building_response",
          "validating_response"
        ],
        blocked: [
          "understanding_query",
          "resolving_intent",
          "validating_response"
        ]
      }
    };
  }

  function inferFallbackKey(text) {
    var normalized = normalizeText(text);
    if (/\b(envi|mande|notifique|avise|dispare)\b/.test(normalized)) {
      return "tool";
    }
    if (/\b(produtiv|improdutiv|desempenh|ranking|top|pior|melhor|ocupac|pausa|periodo|mes|ano|semana)\b/.test(normalized)) {
      return "analytics";
    }
    return "default";
  }

  function createController(element, config) {
    var baseConfig = buildDefaultConfig();
    var effectiveConfig = Object.assign({}, baseConfig, config || {});
    effectiveConfig.labels = Object.assign({}, baseConfig.labels, (config && config.labels) || {});
    effectiveConfig.fallbackSequences = Object.assign({}, baseConfig.fallbackSequences, (config && config.fallbackSequences) || {});

    var textNode = element.querySelector(".assistant-processing__text");
    var dotNode = element.querySelector(".assistant-processing__dot");
    var sequenceTimerId = null;
    var hideTimerId = null;
    var swapTimerId = null;
    var sequenceRunId = 0;

    function addClass(className) {
      if (element.classList && typeof element.classList.add === "function") {
        element.classList.add(className);
      }
    }

    function removeClass(className) {
      if (element.classList && typeof element.classList.remove === "function") {
        element.classList.remove(className);
      }
    }

    function clearSequenceTimer() {
      if (sequenceTimerId) {
        root.clearInterval(sequenceTimerId);
        sequenceTimerId = null;
      }
    }

    function clearHideTimer() {
      if (hideTimerId) {
        root.clearTimeout(hideTimerId);
        hideTimerId = null;
      }
    }

    function clearSwapTimer() {
      if (swapTimerId) {
        root.clearTimeout(swapTimerId);
        swapTimerId = null;
      }
    }

    function clearAllTimers() {
      clearSequenceTimer();
      clearHideTimer();
      clearSwapTimer();
    }

    function writeText(nextText) {
      if (!textNode) {
        element.textContent = nextText;
        return;
      }
      if (textNode.textContent === nextText) {
        return;
      }
      addClass("is-swapping");
      textNode.textContent = nextText;
      clearSwapTimer();
      swapTimerId = root.setTimeout(function () {
        removeClass("is-swapping");
        swapTimerId = null;
      }, 220);
    }

    function showStatus(status) {
      clearHideTimer();
      element.hidden = false;
      element.dataset.processingState = status || "";
      writeText(effectiveConfig.labels[status] || "Pensando...");
      if (dotNode && typeof dotNode.setAttribute === "function") {
        dotNode.setAttribute("data-status", status || "");
      }
      removeClass("is-hidden");
      removeClass("is-leaving");
      addClass("is-visible");
    }

    function hideStatus(immediate) {
      clearHideTimer();
      removeClass("is-swapping");
      if (immediate) {
        clearSwapTimer();
        removeClass("is-visible");
        removeClass("is-leaving");
        addClass("is-hidden");
        element.hidden = true;
        element.dataset.processingState = "";
        return;
      }
      removeClass("is-visible");
      addClass("is-leaving");
      hideTimerId = root.setTimeout(function () {
        removeClass("is-leaving");
        addClass("is-hidden");
        element.hidden = true;
        element.dataset.processingState = "";
        hideTimerId = null;
      }, 220);
    }

    function runFallbackSequence(text) {
      clearSequenceTimer();
      sequenceRunId += 1;
      var localRunId = sequenceRunId;
      var key = inferFallbackKey(text);
      var sequence = effectiveConfig.fallbackSequences[key] || effectiveConfig.fallbackSequences["default"] || [];
      if (!sequence.length) {
        showStatus("understanding_query");
        return;
      }
      var index = 0;
      showStatus(sequence[index]);
      sequenceTimerId = root.setInterval(function () {
        if (localRunId !== sequenceRunId) {
          clearSequenceTimer();
          return;
        }
        if (index >= sequence.length - 1) {
          clearSequenceTimer();
          return;
        }
        index += 1;
        showStatus(sequence[index]);
      }, 950);
    }

    function scheduleFailureHide() {
      clearHideTimer();
      hideTimerId = root.setTimeout(function () {
        hideStatus(false);
      }, 900);
    }

    function resetImmediate() {
      sequenceRunId += 1;
      clearAllTimers();
      hideStatus(true);
    }

    resetImmediate();

    return {
      start: function (text) {
        clearHideTimer();
        runFallbackSequence(text);
      },
      fail: function () {
        clearSequenceTimer();
        showStatus("failed");
        scheduleFailureHide();
      },
      stop: function () {
        clearSequenceTimer();
        hideStatus(false);
      },
      reset: function () {
        resetImmediate();
      },
      isVisible: function () {
        return !element.hidden;
      }
    };
  }

  function createRequestState(controller) {
    var nextToken = 0;
    var activeToken = 0;

    return {
      begin: function (text) {
        nextToken += 1;
        activeToken = nextToken;
        if (controller && typeof controller.start === "function") {
          controller.start(text);
        }
        return activeToken;
      },
      isActive: function (token) {
        return Boolean(token) && token === activeToken;
      },
      complete: function (token) {
        if (!this.isActive(token)) {
          return false;
        }
        activeToken = 0;
        if (controller && typeof controller.stop === "function") {
          controller.stop();
        }
        return true;
      },
      fail: function (token) {
        if (!this.isActive(token)) {
          return false;
        }
        activeToken = 0;
        if (controller && typeof controller.fail === "function") {
          controller.fail();
        }
        return true;
      },
      reset: function () {
        activeToken = 0;
        nextToken += 1;
        if (controller && typeof controller.reset === "function") {
          controller.reset();
        } else if (controller && typeof controller.stop === "function") {
          controller.stop();
        }
      },
      activeToken: function () {
        return activeToken;
      }
    };
  }

  return {
    buildDefaultConfig: buildDefaultConfig,
    createController: createController,
    createRequestState: createRequestState,
    inferFallbackKey: inferFallbackKey
  };
});
