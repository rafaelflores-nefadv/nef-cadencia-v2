const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { setTimeout: delay } = require("node:timers/promises");

const processingUi = require("../static/assistant/assistant_processing_ui.js");

const widgetScript = fs.readFileSync(
  path.join(__dirname, "..", "static", "assistant", "assistant_widget.js"),
  "utf8"
);

function createClassList() {
  const values = new Set();
  return {
    add(name) {
      values.add(name);
    },
    remove(name) {
      values.delete(name);
    },
    contains(name) {
      return values.has(name);
    },
    toggle(name, force) {
      if (force === undefined) {
        if (values.has(name)) {
          values.delete(name);
          return false;
        }
        values.add(name);
        return true;
      }
      if (force) {
        values.add(name);
        return true;
      }
      values.delete(name);
      return false;
    },
  };
}

function createElement(tagName, ownerDocument, id) {
  const listeners = new Map();
  const element = {
    tagName: String(tagName || "div").toUpperCase(),
    id: id || "",
    ownerDocument,
    dataset: {},
    style: {},
    children: [],
    parentNode: null,
    className: "",
    classList: createClassList(),
    textContent: "",
    hidden: false,
    disabled: false,
    value: "",
    scrollTop: 0,
    scrollHeight: 0,
    attributes: {},
    addEventListener(type, handler) {
      if (!listeners.has(type)) {
        listeners.set(type, []);
      }
      listeners.get(type).push(handler);
    },
    dispatchEvent(event) {
      const handlers = listeners.get(event.type) || [];
      handlers.forEach((handler) => handler(event));
    },
    click() {
      this.dispatchEvent({ type: "click", target: this, preventDefault() {} });
    },
    focus() {},
    setAttribute(name, value) {
      this.attributes[name] = String(value);
    },
    getAttribute(name) {
      return this.attributes[name] || null;
    },
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      this.scrollHeight = this.children.length * 120;
      return child;
    },
    removeChild(child) {
      const index = this.children.indexOf(child);
      if (index >= 0) {
        this.children.splice(index, 1);
        child.parentNode = null;
      }
      this.scrollHeight = this.children.length * 120;
      return child;
    },
    remove() {
      if (this.parentNode) {
        this.parentNode.removeChild(this);
      }
    },
    contains(target) {
      if (target === this) {
        return true;
      }
      return this.children.some((child) => typeof child.contains === "function" && child.contains(target));
    },
    querySelector(selector) {
      if (selector === ".assistant-empty") {
        return this.children.find((child) => child.className === "assistant-empty") || null;
      }
      if (selector === ".assistant-processing__text") {
        return this._processingText || null;
      }
      if (selector === ".assistant-processing__dot") {
        return this._processingDot || null;
      }
      return null;
    },
  };

  Object.defineProperty(element, "innerHTML", {
    get() {
      return "";
    },
    set() {
      element.children.slice().forEach((child) => child.remove());
      element.textContent = "";
    },
  });

  return element;
}

function buildEnvironment() {
  const documentListeners = new Map();
  const elements = new Map();

  const document = {
    cookie: "csrftoken=test-token",
    createElement(tagName) {
      return createElement(tagName, document);
    },
    getElementById(id) {
      return elements.get(id) || null;
    },
    addEventListener(type, handler) {
      if (!documentListeners.has(type)) {
        documentListeners.set(type, []);
      }
      documentListeners.get(type).push(handler);
    },
    dispatchEvent(event) {
      const handlers = documentListeners.get(event.type) || [];
      handlers.forEach((handler) => handler(event));
    },
  };

  function register(id, tagName) {
    const element = createElement(tagName, document, id);
    elements.set(id, element);
    return element;
  }

  const root = register("assistant-widget-root", "div");
  root.dataset.userId = "7";
  root.dataset.widgetChatUrl = "/assistant/widget/chat";
  root.dataset.widgetEndUrl = "/assistant/widget/session/end";
  root.dataset.widgetSaveUrl = "/assistant/widget/session/save";
  root.dataset.assistantName = "Eustacio";
  root.dataset.emptyState = "Pergunte ao Eustacio sobre a operacao.";
  root.dataset.saveLabel = "Salvar conversa";
  root.dataset.savedLabel = "Conversa salva";

  const fab = register("assistant-fab", "button");
  const drawer = register("assistant-drawer", "aside");
  const closeBtn = register("assistant-close", "button");
  const saveButton = register("assistant-save", "button");
  const messagesEl = register("assistant-messages", "div");
  const inputEl = register("assistant-input", "textarea");
  inputEl.scrollHeight = 40;
  const sendButton = register("assistant-send", "button");
  const typingEl = register("assistant-typing", "div");
  typingEl.hidden = true;
  typingEl._processingText = { textContent: "" };
  typingEl._processingDot = {
    attributes: {},
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
  };
  const processingConfigEl = register("assistant-widget-processing-config", "script");
  processingConfigEl.textContent = JSON.stringify(processingUi.buildDefaultConfig());

  const fetchCalls = [];
  const fetchQueue = [];
  const fetch = (url, options) => {
    fetchCalls.push({ url, options });
    if (!fetchQueue.length) {
      throw new Error("Unexpected fetch call: " + url);
    }
    return fetchQueue.shift()(url, options);
  };

  const windowObject = {
    document,
    AssistantProcessingUI: processingUi,
    crypto: {
      randomUUID() {
        return "123e4567-e89b-12d3-a456-426614174000";
      },
    },
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
  };

  const context = {
    window: windowObject,
    document,
    fetch,
    console,
    Math,
    Date,
    JSON,
    decodeURIComponent,
    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
  };

  vm.runInNewContext(widgetScript, context, { filename: "assistant_widget.js" });

  return {
    elements: { root, fab, drawer, closeBtn, saveButton, messagesEl, inputEl, sendButton, typingEl },
    document,
    fetchCalls,
    pushFetch(handler) {
      fetchQueue.push(handler);
    },
  };
}

function extractTexts(element) {
  const values = [];

  function visit(node) {
    if (node.textContent) {
      values.push(node.textContent);
    }
    if (Array.isArray(node.children)) {
      node.children.forEach(visit);
    }
  }

  visit(element);
  return values;
}

async function runTest(name, fn) {
  try {
    await fn();
    console.log("ok - " + name);
  } catch (error) {
    console.error("fail - " + name);
    throw error;
  }
}

async function main() {
  await runTest("widget starts hidden without ghost thinking state", async () => {
    const env = buildEnvironment();
    assert.equal(env.elements.typingEl.hidden, true);
    assert.equal(env.elements.typingEl.dataset.processingState, "");
    assert.equal(env.elements.typingEl._processingText.textContent, "");
    assert.equal(env.elements.drawer.classList.contains("open"), false);
  });

  await runTest("opening widget with empty conversation keeps processing hidden", async () => {
    const env = buildEnvironment();

    env.elements.fab.click();

    assert.equal(env.elements.drawer.classList.contains("open"), true);
    assert.equal(env.elements.typingEl.hidden, true);
    assert.equal(env.elements.typingEl.dataset.processingState, "");
  });

  await runTest("closing preserves temporary conversation and does not call end session", async () => {
    const env = buildEnvironment();
    env.elements.fab.click();
    assert.equal(env.elements.typingEl.hidden, true);

    let resolveFetch;
    env.pushFetch(() => new Promise((resolve) => {
      resolveFetch = resolve;
    }));

    env.elements.inputEl.value = "Quais agentes estao em pausa agora?";
    env.elements.sendButton.click();

    assert.equal(env.elements.typingEl.hidden, false);
    assert.equal(env.fetchCalls.length, 1);
    assert.equal(env.fetchCalls[0].url, "/assistant/widget/chat");

    resolveFetch({
      ok: true,
      json: async () => ({
        answer: "Encontrei 3 agentes em pausa.",
        saved_conversation_id: null,
      }),
    });

    await delay(0);
    await delay(260);

    assert.equal(env.elements.typingEl.hidden, true);

    env.elements.closeBtn.click();
    assert.equal(env.elements.drawer.classList.contains("open"), false);
    assert.equal(env.elements.typingEl.hidden, true);
    assert.equal(env.fetchCalls.some((call) => call.url === "/assistant/widget/session/end"), false);

    const textsAfterClose = extractTexts(env.elements.messagesEl).join(" | ");
    assert.match(textsAfterClose, /Quais agentes estao em pausa agora\?/);
    assert.match(textsAfterClose, /Encontrei 3 agentes em pausa\./);

    env.elements.fab.click();
    assert.equal(env.elements.drawer.classList.contains("open"), true);
    assert.equal(env.elements.typingEl.hidden, true);

    const textsAfterReopen = extractTexts(env.elements.messagesEl).join(" | ");
    assert.match(textsAfterReopen, /Quais agentes estao em pausa agora\?/);
    assert.match(textsAfterReopen, /Encontrei 3 agentes em pausa\./);
    assert.equal(env.elements.typingEl.hidden, true);
    assert.equal(env.elements.typingEl.dataset.processingState, "");
  });

  await runTest("refresh recreates widget state from zero", async () => {
    const firstEnv = buildEnvironment();
    firstEnv.elements.fab.click();
    firstEnv.pushFetch(() => Promise.resolve({
      ok: true,
      json: async () => ({
        answer: "Resumo pronto.",
        saved_conversation_id: null,
      }),
    }));
    firstEnv.elements.inputEl.value = "Resumo operacional";
    firstEnv.elements.sendButton.click();

    await delay(0);
    await delay(260);

    const firstTexts = extractTexts(firstEnv.elements.messagesEl).join(" | ");
    assert.match(firstTexts, /Resumo operacional/);

    const refreshedEnv = buildEnvironment();
    refreshedEnv.elements.fab.click();

    assert.equal(refreshedEnv.elements.typingEl.hidden, true);
    const refreshedTexts = extractTexts(refreshedEnv.elements.messagesEl).join(" | ");
    assert.match(refreshedTexts, /Pergunte ao Eustacio sobre a operacao\./);
    assert.doesNotMatch(refreshedTexts, /Resumo operacional/);
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
