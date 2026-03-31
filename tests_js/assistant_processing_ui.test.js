const assert = require("node:assert/strict");
const { setTimeout: delay } = require("node:timers/promises");

const {
  createController,
  createRequestState,
} = require("../static/assistant/assistant_processing_ui.js");

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
  };
}

function createElement() {
  const textNode = { textContent: "" };
  const dotNode = {
    attributes: {},
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
  };

  return {
    hidden: false,
    dataset: {},
    classList: createClassList(),
    textContent: "",
    querySelector(selector) {
      if (selector === ".assistant-processing__text") {
        return textNode;
      }
      if (selector === ".assistant-processing__dot") {
        return dotNode;
      }
      return null;
    },
    _textNode: textNode,
    _dotNode: dotNode,
  };
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
  await runTest("controller starts hidden and does not render stale thinking state", async () => {
    const element = createElement();
    const controller = createController(element, {});

    assert.equal(controller.isVisible(), false);
    assert.equal(element.hidden, true);
    assert.equal(element.dataset.processingState, "");
    assert.equal(element._textNode.textContent, "");
  });

  await runTest("successful request completes and clears the processing state", async () => {
    const element = createElement();
    const state = createRequestState(createController(element, {}));
    const token = state.begin("qual o pior agente do ano?");

    assert.equal(state.isActive(token), true);
    assert.equal(element.hidden, false);

    state.complete(token);
    await delay(260);

    assert.equal(state.activeToken(), 0);
    assert.equal(element.hidden, true);
    assert.equal(element.dataset.processingState, "");
  });

  await runTest("failed request shows temporary error and then clears", async () => {
    const element = createElement();
    const state = createRequestState(createController(element, {}));
    const token = state.begin("consultar produtividade");

    state.fail(token);
    assert.equal(element.hidden, false);
    assert.equal(element.dataset.processingState, "failed");

    await delay(1150);

    assert.equal(element.hidden, true);
    assert.equal(element.dataset.processingState, "");
  });

  await runTest("reset invalidates an older request and keeps the component clean", async () => {
    const element = createElement();
    const state = createRequestState(createController(element, {}));
    const token = state.begin("ranking de produtividade");

    state.reset();
    assert.equal(state.isActive(token), false);
    assert.equal(element.hidden, true);
    assert.equal(element.dataset.processingState, "");

    await delay(1100);

    assert.equal(element.hidden, true);
    assert.equal(element.dataset.processingState, "");
  });

  await runTest("stale token cannot hide a newer active request", async () => {
    const element = createElement();
    const state = createRequestState(createController(element, {}));
    const firstToken = state.begin("primeira consulta");
    const secondToken = state.begin("segunda consulta");

    assert.equal(state.complete(firstToken), false);
    assert.equal(element.hidden, false);
    assert.equal(state.isActive(secondToken), true);

    state.complete(secondToken);
    await delay(260);

    assert.equal(element.hidden, true);
    assert.equal(state.activeToken(), 0);
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
